# llm/llm_client.py
import asyncio
import json
import random
import httpx
from functools import wraps
from typing import Dict, Any, Optional, Type, List, Union, TypeVar, Callable, Awaitable
from guardianhub.config.settings import settings
from guardianhub import get_logger
from opentelemetry.propagate import inject
from pydantic import BaseModel, ValidationError

logger = get_logger(__name__)

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Awaitable[Any]])


def retry_with_backoff(
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        exceptions: tuple = (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError, ValidationError)
) -> Callable[[F], F]:
    """
    A decorator that retries an async function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for the delay between retries
        jitter: Whether to add random jitter to the delay
        exceptions: Tuple of exceptions to catch and retry on
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay

            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1

                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise

                    # Calculate next delay with exponential backoff and jitter
                    delay = min(delay * backoff_factor, max_delay)
                    if jitter:
                        delay = random.uniform(0, delay)

                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} after error: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    await asyncio.sleep(delay)

        return wrapper

    return decorator


T = TypeVar('T', bound=BaseModel)


class LLMWorker:
    """Unified client for LLM interactions with structured output support."""
    
    DEFAULT_MODEL = "default"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 2048

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            timeout=240.0
        )
        
    def _resolve_response_model(
        self,
        response_model: Optional[Type[T]],
        response_model_name: Optional[str]
    ) -> Optional[Type[T]]:
        """Resolve the response model from name or return the provided model.
        
        Args:
            response_model: Direct model class if available
            response_model_name: Name of the model to resolve if response_model is None
            
        Returns:
            Resolved model class or None if resolution fails
        """
        if response_model is not None:
            return response_model
            
        if response_model_name is not None:
            try:
                from guardianhub.models.registry.registry import get_model
                resolved_model = get_model(response_model_name)
                if resolved_model is None:
                    logger.warning(f"Could not find model: {response_model_name}")
                return resolved_model
            except ImportError as e:
                logger.warning(f"Failed to import model {response_model_name}: {e}")
        return None

    @retry_with_backoff(max_retries=2, initial_delay=1.0, max_delay=30.0)
    async def _make_llm_request(
            self,
            payload: Dict[str, Any],
            use_fallback_model: bool = False
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the LLM API with the given payload.

        Args:
            payload: The request payload to send to the LLM API
            use_fallback_model: If True, use the fallback model key

        Returns:
            The parsed JSON response from the API

        Raises:
            httpx.HTTPStatusError: If the API returns an error status code
            json.JSONDecodeError: If the response is not valid JSON
        """
        # Create a copy of the payload to avoid modifying the original
        request_payload = payload.copy()

        headers = {}
        # Inject traceparent + tracestate
        inject(headers)

        # If using fallback model, update the model_key
        if use_fallback_model:
            request_payload['model_key'] = 'default'
            logger.info("Using fallback 'default' model for LLM request.. there has been a failure in LLM")
            logger.info("🌐 Using fallback 'default' model for LLM request.. there has been a failure in LLM")

        try:
            response = await self.client.post(
                "/chat/completions",
                json=request_payload,
                headers=headers,
                timeout=360.0
            )
            response.raise_for_status()
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}\nResponse text: {response.text}")
                raise RuntimeError(f"Invalid JSON response from LLM service: {response.text}") from e

        except httpx.HTTPStatusError as e:
            # If not already using fallback and it's a server error, try with fallback model
            if not use_fallback_model and e.response.status_code >= 500:
                logger.warning(
                    f"LLM request failed with status {e.response.status_code}. "
                    "Retrying with fallback model..."
                )
                # Retry with fallback model
                return await self._make_llm_request(payload, use_fallback_model=True)
            raise  # Re-raise if already using fallback or not a server error

    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            model: str = DEFAULT_MODEL,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            response_model_name: Optional[str] = None,
            response_model: Optional[Type[T]] = None,
            **kwargs
    ) -> Union[Dict[str, Any], T, str]:
        """
        Send a chat completion request to the LLM service with automatic fallback to a more powerful model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum number of tokens to generate
            response_format: Optional format specification for the response
            response_model: Optional Pydantic model for structured output
            **kwargs: Additional arguments to pass to the API

        Returns:
            Dict containing the API response or an instance of response_model if provided

        Raises:
            RuntimeError: If the API request fails after retries and fallback
            ValidationError: If response_model is provided and the response doesn't match the schema
        """
        # Resolve the response model if needed
        resolved_model = self._resolve_response_model(response_model, response_model_name)
        
        # Prepare the base payload
        payload = {
            "model": settings.llm.get_config(self.DEFAULT_MODEL).model_name,
            "model_key": model,
            "messages": messages,
            **{k: v for k, v in kwargs.items() if v is not None}
        }
        
        # Add optional parameters if provided
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        # Handle structured output if we have a response model name
        if response_model_name:
            payload["response_model_name"] = response_model_name

        try:
            # First try with the default model key
            try:
                response_data = await self._make_llm_request(payload, use_fallback_model=False)
            except Exception as e:
                # If the error is not a server error, re-raise it
                if not (isinstance(e, httpx.HTTPStatusError) and e.response.status_code >= 500):
                    raise
                # For server errors, let _make_llm_request handle the fallback
                response_data = await self._make_llm_request(payload, use_fallback_model=True)
            logger.debug(f"Received response data: {response_data}")

            if "choices" in response_data:
                content = response_data["choices"][0]["message"].get("content")

                # If content is a JSON string, parse it
                if content and isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON response: {e}")
                        return content

                # If we have a response model, validate against it
                if resolved_model and content:
                    try:
                        return resolved_model.model_validate(content)
                    except ValidationError as e:
                        logger.error(f"Response validation failed: {e}")
                        logger.debug(f"Response content: {content}")
                        return resolved_model()

                return content or response_data

            return response_data

        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}", exc_info=True)
            # If we have a response model, return a default instance
            if response_model is not None:
                logger.warning(f"Returning default {response_model.__name__} due to LLM error")
                if hasattr(response_model, 'model_fields') and 'plan' in response_model.model_fields:
                    return response_model(plan=[])
                return response_model()
            raise RuntimeError(f"LLM request failed: {str(e)}") from e


    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
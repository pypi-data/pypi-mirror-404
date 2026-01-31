# In sutram_services/llm/llm_client.py
import json
from typing import Dict, Any, Optional, Type, TypeVar

from guardianhub import get_logger
from guardianhub.utils.json_utils import parse_structured_response, extract_json_from_text
from guardianhub.clients.llm_worker import LLMWorker
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel
from guardianhub.config.settings import settings

logger = get_logger(__name__)
T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """Service for managing LLM interactions."""

    def __init__(self):
        self.worker = LLMWorker(settings.endpoints.LLM_URL, "NO_API_KEY")
        self.llm = self.worker  # For backward compatibility
        self.eval_llm = self.worker
        self.logger = logger

    async def invoke_unstructured_model(
            self,
            model: str,
            user_input: str,
            system_prompt: str,
            model_key: str = "default",
            temperature: float = 0.7,
            **kwargs
    ) -> str:
        """
        Invokes the LLM to generate a natural language, unstructured text response.

        Args:
            model: The model identifier to use
            user_input: User's input text
            system_prompt: System prompt for the LLM
            model_key: Key to identify the model configuration
            temperature: Sampling temperature (0-2)
            **kwargs: Additional arguments to pass to the LLM worker

        Returns:
            str: The raw text content of the LLM's response.
        """
        try:
            self.logger.info(f"🌐 Calling LLM for unstructured text generation (Model: {model})")

            # 1. Build message list with potential additional context from kwargs
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]

            # 2. Prepare base parameters
            llm_params = {
                "messages": messages,
                "model_key": model_key,
                "temperature": temperature,
                "max_tokens": 4048,
                **{k: v for k, v in kwargs.items() if v is not None}
            }

            # 3. Call the LLM
            response = await self.worker.chat_completion(**llm_params)

            # 4. Extract and return the raw text content
            response_text = response
            self.logger.debug(f"Raw unstructured LLM response: {response_text[:100]}...")
            return response_text

        except Exception as e:
            self.logger.error(f"Error in invoke_unstructured_model: {str(e)}", exc_info=True)
            raise RuntimeError(f"Unstructured LLM invocation failed: {str(e)}") from e

    async def invoke_structured_model(
            self,
            user_input: str,
            system_prompt_template: str,
            context: Optional[Dict[str, Any]] = None, # 🎯 NEW: Accept context
            response_model: Optional[Type[T]] = None,
            response_model_name: Optional[str] = None,
            model_key: str = "default",
            langfuse_trace_id: Optional[str] = None,
            parent_span_id: Optional[str] = None,
    ) -> T:
        try:
            # 1. HYDRATION: Inject the Plan and Facts into the Template
            # We use .format(**context) if context exists, otherwise use raw template
            final_system_prompt = system_prompt_template
            if context:
                try:
                    final_system_prompt = system_prompt_template.format(**context)
                    self.logger.debug(f"Successfully hydrated system prompt with {list(context.keys())}")
                except KeyError as e:
                    self.logger.warning(f"Template hydration missed a key: {str(e)}. Sending raw.")
                except Exception as e:
                    self.logger.error(f"Hydration failed: {str(e)}")

            # 2. Build the messages with the rendered prompt
            messages = [
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": user_input}
            ]

            # Call the LLM with the response model for schema validation
            self.logger.debug(f"Sending request to LLM with model: {model_key}")
            response = await self.worker.chat_completion(
                messages=messages,
                model=model_key,
                temperature=0.1,  # Lower temperature for more deterministic output
                response_model=response_model,
                response_model_name=response_model_name,
                langfuse_trace_id=langfuse_trace_id,
                otel_trace_id=parent_span_id,
                max_tokens=4048
            )

            # If we get here, the response is already validated by the client
            self.logger.info("Successfully got response from LLM")
            return response

        except Exception as e:
            self.logger.error(f"LLM request failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"LLM request failed: {str(e)}") from e

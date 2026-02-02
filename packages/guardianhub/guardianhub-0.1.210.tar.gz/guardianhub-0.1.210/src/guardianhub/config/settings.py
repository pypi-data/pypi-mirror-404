"""Core settings for the GuardianHub Foundation SDK."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field, ConfigDict
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_config_defaults(env: str = None) -> dict:
    """Load configuration defaults from JSON files based on environment."""
    env = (env or os.environ.get("ENVIRONMENT", "development")).lower()
    env = "development" if env == "dev" else env

    config_dir = Path(__file__).parent
    possible_files = [f"config_{env}.json", "config_dev.json", "config_development.json"]
    for filename in possible_files:
        config_path = config_dir / filename
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception:
                continue
    return {}

class ServiceInfo(BaseModel):
    """Metadata about the microservice using the SDK."""
    name: str = "guardianhub-service"
    version: str = "0.0.1"
    id: str = "guardian-01"
    host: str = "0.0.0.0"
    port: int = 8001

class LoggingSettings(BaseModel):
    """Standardized logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class ModelConfig(BaseModel):
    """Standardized schema for any LLM model configuration."""
    model_name: str
    provider: str = "OPENAI"  # GEMINI, OLLAMA, OPENAI, etc.
    base_url: str
    api_key: str = "your-api-key-here"
    temperature: float = 0.1
    max_tokens: int = 2048
    streaming: bool = False
    headers: Dict[str, str] = {}
    model_kwargs: Dict[str, Any] = {}

class LLMSettings(BaseModel):
    """Registry of models defined in the config JSON."""
    # This matches your "model_configs": { "judge": {...}, "tuned": {...} }
    model_configs: Dict[str, ModelConfig] = Field(default_factory=dict)

    def get_config(self, key: str = "default") -> ModelConfig:
        """Helper to safely retrieve a model config by its key."""
        return self.model_configs.get(key, self.model_configs.get("default"))

class CredentialConfig(BaseModel):
    """Manages credentials from config.
    These values can be overridden via environment variables:
       - Set GH_CREDENTIALS__LANGFUSE_PUBLIC_KEY="your_public_key" in your .env file or environment
    """
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        # Convert all keys to uppercase
        processed_data = {k.upper(): v for k, v in data.items()}
        super().__init__(**processed_data)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a credential value (case-insensitive)."""
        return getattr(self, key.upper(), default)


class SpecialistSettings(BaseModel):
    """Configuration specific to Specialist Agent identity."""
    agent_name: str = "specialist-default"
    agent_domain: str = "infrastructure"  # CMDB, K8S, SECURITY
    capabilities: List[str] = Field(default_factory=list)
    hop_limit: int = 3  # Prevents infinite A2A loops
    callback_timeout: int = 300  # 5 minutes for "Coming Home"
    task_queue: str = "specialist-queue"
    default_dna: str = "Standard Sovereign Protocol"

class TemporalSettings(BaseModel):
    """Muscle settings for durable execution."""
    namespace: str = "default"
    task_queue: str = "specialist-queue"
    # Mapping of activity categories to timeouts
    short_timeout: int = 60
    medium_timeout: int = 900
    long_timeout: int = 3600


class WorkflowSettings(BaseModel):
    """Configuration for Temporal Activity routing and policies."""

    activity_mapping: Dict[str, str] = Field(default_factory=lambda: {
        # Sensory & Recon
        "conduct_reconnaissance": "conduct_reconnaissance",
        "retrieve_intelligence_history": "retrieve_intelligence_history",

        # Cognitive & Planning
        "analyze_tactical_context": "analyze_tactical_context",
        "formulate_mission_proposal": "formulate_mission_proposal",

        # Execution & Mesh
        "execute_direct_intervention": "execute_direct_intervention",
        "recruit_specialist_support": "recruit_specialist_support",

        # Validation & Learning
        "verify_objective_attainment": "verify_objective_attainment",
        "commit_mission_after_action_report": "commit_mission_after_action_report",
        "summarize_intelligence_debrief": "summarize_intelligence_debrief",
        "transmit_mission_completion": "transmit_mission_completion"
    })

    short_activities: List[str] = Field(default_factory=lambda: [
        "conduct_reconnaissance", "retrieve_intelligence_history", "transmit_mission_completion"
    ])

    medium_activities: List[str] = Field(default_factory=lambda: [
        "analyze_tactical_context", "formulate_mission_proposal",
        "summarize_intelligence_debrief", "verify_objective_attainment"
    ])

    long_activities: List[str] = Field(default_factory=lambda: [
        "execute_direct_intervention", "recruit_specialist_support", "commit_mission_after_action_report"
    ])

class ServiceEndpoints(BaseModel):
    """
    Endpoints for essential shared services.
    Supports dictionary-style access for backward compatibility.
    """
    model_config = ConfigDict(extra="allow")

    CONSUL_HTTP_ADDR: str = "http://localhost:8500"
    GRAPH_DB_URL: str = "http://localhost:8009"
    LLM_URL: str = "http://localhost:8001"
    LANGFUSE_HOST: str = "http://localhost:3000"
    POSTGRES_URL: str = "postgresql://user:password@localhost:5432/guardianhub"
    TEXT_EMBEDDING_SERVICE_URL: str = "http://localhost:8010"
    TOOL_REGISTRY_URL: str = "http://localhost:8000"
    TOOL_EXECUTOR_URL: str = "http://localhost:8003"
    VECTOR_SERVICE_URL: str = "http://localhost:8005"
    TEMPORAL_HOST_URL: str = "localhost:7233"
    SUTRAM_CALLBACK_URL: str = "http://localhost:8000/v1/agent/callback"
    CLASSIFICATION_SERVICE_URL: str = "http://localhost:8000/v1/agent/callback"
    METADATA_EXTRACTION_SERVICE_URL: str = "http://localhost:8000/v1/agent/callback"
    PAPERLESS_SERVICE_URL: str = "http://localhost:8000/v1/agent/callback"

    ENVIRONMENT: str = "development"

    def __init__(self, **data):
        # Handle case-insensitive environment variables
        processed_data = {}
        for k, v in data.items():
            # Convert to uppercase for case-insensitive matching
            if k.upper() in self.__class__.model_fields:
                processed_data[k.upper()] = v
            else:
                processed_data[k] = v

        # Initialize the model with known fields
        super().__init__(**{k: v for k, v in processed_data.items()
                          if k in self.__class__.model_fields})

        # Store extra fields in __pydantic_extra__
        extra_data = {k: v for k, v in processed_data.items()
                     if k not in self.__class__.model_fields}
        if extra_data:
            if not hasattr(self, '__pydantic_extra__'):
                object.__setattr__(self, '__pydantic_extra__', {})
            self.__pydantic_extra__.update(extra_data)

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style get method for backward compatibility."""
        # First try to get from model fields (case-insensitive)
        key_upper = key.upper()
        if key_upper in self.__class__.model_fields:
            return getattr(self, key_upper, default)

        # Then try to get from extra fields (case-sensitive)
        if hasattr(self, '__pydantic_extra__'):
            # Try exact match first
            if key in self.__pydantic_extra__:
                return self.__pydantic_extra__[key]
            # Try case-insensitive match
            for k, v in self.__pydantic_extra__.items():
                if k.upper() == key_upper:
                    return v

        # Finally, try direct attribute access
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Enable dictionary-style access."""
        value = self.get(key)
        if value is None and not hasattr(self, key) and not (hasattr(self, '__pydantic_extra__') and key in self.__pydantic_extra__):
            raise KeyError(f"'{key}' not found in ServiceEndpoints")
        return value


class VectorConfig(BaseModel):
    """Vector database configuration."""
    default_collection: str = Field("document_templates", description="The primary RAG collection")

    # NEW: Allow services to define their own required collections in their config_*.json
    additional_collections: List[str] = Field(
        default_factory=lambda: ["ace_context_bullets", "episodes", "lessons"],
        description="Collections to be initialized on service startup"
    )


class VectorSettings(BaseModel):
    """Production-ready configuration for VectorClient operations."""
    http_timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    max_batch_size: int = 100
    max_query_length: int = 1000
    max_document_length: int = 100000
    health_check_interval: float = 30.0
    default_collection: str = "document_templates"
    additional_collections: List[str] = Field(default_factory=lambda: ["episodes", "ace_context_bullets"])


class CoreSettings(BaseSettings):
    """
    The Core Settings class. Automatically merges bundled JSON
    profiles with environment variables.
    """
    model_config = SettingsConfigDict(
        env_prefix="GH_",
        env_nested_delimiter="__",
        extra="allow"
    )

    specialist_settings: SpecialistSettings = Field(default_factory=SpecialistSettings)
    temporal_settings: TemporalSettings = Field(default_factory=TemporalSettings)
    workflow_settings: WorkflowSettings = Field(default_factory=WorkflowSettings)
    service: ServiceInfo = Field(default_factory=ServiceInfo)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    endpoints: ServiceEndpoints = Field(default_factory=ServiceEndpoints)
    credentials: CredentialConfig = Field(default_factory=CredentialConfig)
    vector: VectorSettings = Field(default_factory=VectorSettings)
    excluded_urls: Optional[str] = None
    max_retries: int = 3
    retry_delay: int = 2
    http_timeout: int = 30

    def __init__(self, **data):
        # Handle environment variable overrides for ENVIRONMENT
        env = os.environ.get("ENVIRONMENT")
        if env:
            if "endpoints" not in data:
                data["endpoints"] = {}
            data["endpoints"]["ENVIRONMENT"] = env

        # Let Pydantic handle the main initialization
        super().__init__(**data)

    @model_validator(mode="before")
    @classmethod
    def _bootstrap_config(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Load the appropriate config file based on environment
            env = data.get("ENVIRONMENT") or os.environ.get("ENVIRONMENT", "development")
            config_data = _load_config_defaults(env)

            if isinstance(config_data, dict):
                # Create a copy of the input data to avoid modifying it
                result = config_data.copy()

                # Update with environment variables, but preserve the endpoints
                if "endpoints" in data and isinstance(data["endpoints"], dict):
                    # Create a new endpoints dict with the config defaults
                    endpoints = result.get("endpoints", {}).copy()
                    # Update with any environment overrides
                    endpoints.update(data["endpoints"])
                    result["endpoints"] = endpoints

                # Update with any other non-endpoint data
                for key, value in data.items():
                    if key != "endpoints":
                        result[key] = value

                return result
        return data

@lru_cache()
def get_cached_settings() -> CoreSettings:
    return CoreSettings()

# Exported singleton
settings: CoreSettings = get_cached_settings()
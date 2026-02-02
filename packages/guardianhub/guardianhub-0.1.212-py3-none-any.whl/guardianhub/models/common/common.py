from typing import List, Dict, Any, Optional, TypeVar, Generic
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
from ..registry.registry import register_model

T = TypeVar('T')

class Status(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"

@register_model
class KeyValuePair(BaseModel):
    """Generic key-value pair model."""
    key: str = Field(..., description="The key of the pair")
    value: Any = Field(..., description="The value associated with the key")
    type: Optional[str] = Field(None, description="Type hint for the value")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "environment",
                "value": "production",
                "type": "string"
            }
        }
    )

@register_model
class StringList(BaseModel):
    """Generic list of strings with metadata."""
    items: List[str] = Field(..., description="List of string items")
    source: Optional[str] = Field(None, description="Source of the list")
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the list items"
    )

@register_model
class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    items: List[T] = Field(..., description="List of items in the current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of items per page")
    has_more: bool = Field(..., description="Whether there are more items to fetch")

@register_model
class ErrorResponse(BaseModel):
    """Standard error response model."""
    status: Status = Field(Status.ERROR, description="Status of the response")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )

@register_model
class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response model with typed data."""
    status: Status = Field(Status.SUCCESS, description="Status of the response")
    data: T = Field(..., description="Response data payload")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the response"
    )

@register_model
class KeywordList(BaseModel):
    """Model for keyword extraction response."""
    keywords: List[str] = Field(..., description="List of extracted keywords")
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction"
    )
    source: Optional[str] = Field(
        None,
        description="Source of the keywords (e.g., 'llm', 'basic')"
    )

    @field_validator('keywords', mode='before')
    @classmethod
    def validate_keywords(cls, v):
        if not isinstance(v, list):
            raise ValueError("keywords must be a list")
        return [str(kw).strip() for kw in v if kw and str(kw).strip()]

from pydantic import BaseModel, Field
from typing import List, Optional

@register_model
class KnowledgeTriplet(BaseModel):
    subject: str = Field(description="PascalCase entity name")
    predicate: str = Field(description="SCREAMING_SNAKE_CASE relationship")
    object: str = Field(description="PascalCase target entity or value")
    # --- Intelligence Enrichment ---
    reasoning: str = Field(description="The 'Why' behind this link")
    evidence: str = Field(description="The source quote for this link")
    context_type: str = Field(description="Social Media, Wiki, News, or Marketplace")

@register_model
class EntityExtraction(BaseModel):
    entities: List[str] = Field(description="List of key entities found (Products, Brands, Locations)")
    triplets: List[KnowledgeTriplet] = Field(description="Relationships for the Knowledge Graph")

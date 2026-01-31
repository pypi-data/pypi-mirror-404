import datetime
import uuid

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class VectorQueryRequest(BaseModel):
    """Unified Semantic Request - The 'Ask'."""
    query: str = Field(..., description="The semantic intent (e.g., 'Check for DB throttling').")
    n_results: int = Field(5, description="Limit for the top-k nearest neighbors.")
    collection: str = Field("episodes", description="The domain (tools, episodes, lessons).")
    # 🎯 FIX: Added filters to allow strict multi-tenancy (Agent-specific memory)
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters (e.g., agent_id=cmdb).")


class VectorQueryResult(BaseModel):
    """The Sovereign Discovery - A single fact/tool from memory."""
    id: str = Field(..., description="The vector store UID.")
    content: str = Field(..., alias="document_text", description="The factual text/dossier.")
    similarity: float = Field(..., alias="similarity_score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="The 'Why' and 'Where'.")

    # 🎯 REFINEMENT: Direct accessors for common fields to stop 'get()' guessing
    @property
    def source_agent(self) -> str:
        return self.metadata.get("agent_id", "system")


class VectorQueryResponse(BaseModel):
    """The High-Fidelity Result Set."""
    results: List[VectorQueryResult]
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
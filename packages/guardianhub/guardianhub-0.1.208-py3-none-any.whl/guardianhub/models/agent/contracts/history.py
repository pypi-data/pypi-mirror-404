# guardianhub_sdk/models/contracts/history.py
from .base import SovereignBaseContract,SovereignBaseResponse
from pydantic import Field
from typing import List, Dict, Any

class HistoryRequest(SovereignBaseContract):
    """Signature for Episodic Memory Retrieval (HISTORY)."""
    search_query: str = Field(..., description="The semantic query to find parallel missions")
    limit: int = Field(5, description="Number of historical parallels to retrieve")
    min_success_score: float = Field(0.0, description="Filter for only high-quality lessons")


class HistoryResponse(SovereignBaseResponse):
    """The historical parallels and lessons learned."""
    episodes: List[Dict[str, Any]] = Field(default_factory=list)
    lessons_discovered: List[str] = Field(default_factory=list)
    avg_similarity_score: float = Field(0.0)
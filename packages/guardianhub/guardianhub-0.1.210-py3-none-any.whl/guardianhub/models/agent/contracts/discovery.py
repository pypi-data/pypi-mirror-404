# guardianhub_sdk/models/contracts/discovery.py
from typing import List,Dict,Any

from .base import SovereignBaseContract,SovereignBaseResponse
from pydantic import Field


class DiscoveryRequest(SovereignBaseContract):
    """Signature for Scoping and Fact-finding (RECON)."""
    sub_objective: str = Field(..., description="The specific intelligence goal")
    environment: str = Field("prod", description="Target environment (e.g., US-West, Prod)")
    depth_limit: int = Field(5, description="Max depth for graph/web traversal")


# guardianhub_sdk/models/contracts/discovery.py

class DiscoveryResponse(SovereignBaseResponse):  # 🎯 Inherits the status/telemetry
    """The full 'Satya' (Truth) captured during Recon."""
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    beliefs: List[Dict[str, Any]] = Field(default_factory=list)
    episodes: List[Dict[str, Any]] = Field(default_factory=list)

    # We can add helper properties here
    @property
    def total_intelligence_count(self) -> int:
        return len(self.facts) + len(self.beliefs) + len(self.episodes)

    @property
    def total_count(self) -> int:  # 🎯 Add this to match the logger call
        return len(self.facts) + len(self.beliefs) + len(self.episodes)
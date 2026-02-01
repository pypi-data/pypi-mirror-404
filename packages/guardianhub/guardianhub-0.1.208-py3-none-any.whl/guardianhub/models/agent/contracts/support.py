# guardianhub_sdk/models/contracts/support.py
from .base import SovereignBaseContract, SovereignBaseResponse
from pydantic import Field
from typing import Dict, Any, Optional

class SupportRequest(SovereignBaseContract):
    """The 'Legion' Request: Peer Recruitment (Kalki Avatar)."""
    target_specialty: str = Field(..., description="The required skill (e.g., 'logistics')")
    objective: str = Field(..., description="The task for the peer agent")
    priority: str = Field("NORMAL", description="LOW, NORMAL, CRITICAL")
    shared_context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PeerSupportOutcome(SovereignBaseResponse):
    """The 'Legion' Response: The result of peer recruitment."""
    peer_name: str = Field(..., description="The name of the recruited agent")
    mission_id: str = Field(..., description="The session ID of the peer's sub-mission")
    recruitment_status: str = Field(..., description="ACCEPTED, QUEUED, or REJECTED")
    peer_metadata: Dict[str, Any] = Field(default_factory=dict)
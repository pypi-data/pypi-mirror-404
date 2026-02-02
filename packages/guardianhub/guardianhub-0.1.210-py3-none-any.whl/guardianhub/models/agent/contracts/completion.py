# guardianhub_sdk/models/contracts/completion.py
from .base import SovereignBaseContract, SovereignBaseResponse
from pydantic import Field
from typing import Dict, Any, Optional

class MissionManifest(SovereignBaseContract):
    """The 'Final Signal' Request: Proof of Mission Completion."""
    mission_id: str = Field(..., description="The unique session/mission identifier")
    final_report: Dict[str, Any] = Field(..., description="The synthesized IntelligenceReport")
    mission_status: str = Field("COMPLETED", description="Final state: COMPLETED, FAILED, or PARTIAL")
    callback_url: str = Field(..., description="Sutram's local DNS callback endpoint")

class CallbackAck(SovereignBaseResponse):
    """The 'Final Signal' Response: Orchestrator's acknowledgement."""
    orchestrator_received: bool = Field(True)
    next_mission_token: Optional[str] = Field(None, description="For chained agentic workflows")
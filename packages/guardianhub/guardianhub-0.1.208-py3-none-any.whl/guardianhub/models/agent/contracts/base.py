
# guardianhub_sdk/models/contracts/base.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class SovereignBaseContract(BaseModel):
    """The universal envelope for all Sovereign Activity Handshakes."""
    session_id: str = Field(..., description="The unique conversation/session identifier")
    template_id: str = Field(..., description="The Mission DNA pattern being followed")
    agent_name: str = Field(..., description="The identity of the Specialist executing the work")
    trace_id: Optional[str] = Field(None, description="Langfuse/OTEL trace anchor")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SovereignBaseResponse(BaseModel):
    """The universal status report for all Sovereign Activities."""
    success: bool = Field(True, description="Whether the activity completed its core logic")
    correlation_id: str = Field(..., description="Matches the session_id/trace_id of the request")
    produced_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = Field(None, description="Details if success is False")
    telemetry: Dict[str, Any] = Field(default_factory=dict, description="Timing, token counts, etc.")
    metadata: Dict[str, Any] = Field(default_factory=dict)

# guardianhub_sdk/models/contracts/attainment.py
from .base import SovereignBaseContract, SovereignBaseResponse
from .action import ActionOutcome
from pydantic import Field
from typing import Optional

class AttainmentCheck(SovereignBaseContract):
    """The 'Inspector' Request: Verify the action's truth."""
    step_id: str = Field(..., description="The ID from the MacroPlan")
    action_name: str = Field(..., description="The ID from the MacroPlan")
    action_outcome: ActionOutcome = Field(..., description="The result from the INTERVENTION phase")
    verification_mode: str = Field("IDEMPOTENT", description="Mode: IDEMPOTENT, STATE_CHECK, or PESSIMISTIC")

class AttainmentReport(SovereignBaseResponse):
    """The 'Inspector' Response: Was the goal actually met?"""
    attained: bool = Field(..., description="Binary confirmation of goal state")
    discrepancy_found: Optional[str] = Field(None)
    certainty_score: float = Field(0.0, ge=0.0, le=1.0)
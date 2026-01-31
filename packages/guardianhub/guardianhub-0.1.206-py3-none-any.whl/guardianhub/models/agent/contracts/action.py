# guardianhub_sdk/models/contracts/action.py
import uuid

from .base import SovereignBaseContract, SovereignBaseResponse
from pydantic import Field
from typing import Dict, Any, Optional

class ActionStep(SovereignBaseContract):
    """The 'Hand' Request: A single execution unit."""
    action_name: str = Field(..., description="The tool or method to invoke")
    action_input: Dict[str, Any] = Field(default_factory=dict)
    step_id: str = Field(..., description="UUID for the step in the MacroPlan")
    is_dry_run: bool = Field(False)

class ActionOutcome(SovereignBaseResponse):
    """The 'Hand' Response: The result of the action with impact metrics."""
    status: str = Field(..., description="SUCCESS, FAILED, or SKIPPED")
    observation: str = Field(..., description="Narrative of what the tool saw/did")
    raw_result: Dict[str, Any] = Field(default_factory=dict)

    # 🎯 NEW: Placeholders for post-processor intelligence
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Quantitative impact (e.g., latency_ms, cost_usd, rows_affected)"
    )
    analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Qualitative results from anomaly/risk post-processors"
    )

    action_id: str = Field(default_factory=lambda: f"ACT-{uuid.uuid4().hex[:6]}")
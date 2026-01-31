# guardianhub_sdk/models/contracts/debrief.py
from .base import SovereignBaseContract, SovereignBaseResponse
from .action import ActionOutcome
from pydantic import Field
from typing import List, Dict, Any

class SummaryBrief(SovereignBaseContract):
    """The 'Scribe' Request: Synthesize the timeline."""
    original_objective: str = Field(..., description="The sub-goal we started with")
    step_results: List[Dict[str, Any]]
    is_partial_success: bool = Field(False, description="Flag if some steps failed")
    # 🎯 NEW: Quantitative context for the Scribe
    total_steps: int = Field(..., description="Total steps in the plan")
    success_count: int = Field(..., description="Number of attained steps")

class IntelligenceReport(SovereignBaseResponse):
    """The 'Scribe' Response: The final narrative of the mission."""
    narrative_summary: str = Field(..., description="The LLM-generated story of the mission")
    key_takeaways: List[str] = Field(default_factory=list)
    final_status: str = Field("SUCCESS", description="SUCCESS, PARTIAL, or FAILED")
    impact_metrics: Dict[str, float] = Field(default_factory=dict, description="Aggregated metrics")
# guardianhub_sdk/models/contracts/learning.py
from .base import SovereignBaseContract,SovereignBaseResponse
from pydantic import Field
from datetime import datetime
from typing import List, Dict, Any, Optional

class AfterActionReport(SovereignBaseContract):
    """Signature for Long-term Memory Commitment (AAR)."""
    mission_id: str = Field(..., description="Unique ID for this specific execution")
    summary_brief: str = Field(..., description="The synthesized narrative from the DEBRIEF")
    execution_data: List[Dict[str, Any]] = Field(..., description="The raw step-by-step outcomes")
    aha_moment: Optional[str] = Field(None, description="The specific lesson or pattern discovered")
    success_score: float = Field(..., ge=0.0, le=1.0, description="Quantitative mission success")

# guardianhub_sdk/models/contracts/learning.py

class LearningAnchor(SovereignBaseResponse):
    """The 'Wisdom' Response: Confirmation of memory commitment."""
    # 🎯 THE FIX: Make memory_id Optional or provide a default for failures
    memory_id: Optional[str] = Field(None, description="The vector ID in the Satya Segment")
    indexed_at: datetime = Field(default_factory=datetime.now)
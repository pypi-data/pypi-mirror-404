"""Agent planning and execution models for the GuardianHub system.

This module contains Pydantic models for agent planning, mission execution,
and inter-agent communication within the GuardianHub ecosystem.
"""
import time
from typing import List, Dict, Any, Optional, Literal
from uuid import uuid4
from pydantic import BaseModel, Field, conlist
from ..registry.registry import register_model

# =============================================================================
# Core Planning Models
# =============================================================================

class PlanStep(BaseModel):
    """A single step in the agent's overall macro-plan."""
    # The exact name of the tool to be called (must match a registered tool)
    tool_name: str = Field(..., description="The exact name of the tool to execute.")

    # A unique name for this step, used as the key to store the result in macro_context.
    step_name: str = Field(
        ...,
        description=(
            "A unique identifier for this plan step. "
            "Its result will be stored under this name in the macro_context."
        )
    )

    # The arguments for the tool call, passed as a dictionary.
    tool_args: Dict[str, Any] = Field(
        ...,
        description="The dictionary of arguments required for the tool call."
    )

    # The list of results (by step_name) this step requires before it can be executed.
    dependencies: List[str] = Field(
        default_factory=list,
        description=(
            "List of step_name strings whose results must be available "
            "in macro_context before this step can run."
        )
    )

    # Internal status, handled by the graph executor.
    status: Literal["pending", "running", "complete", "error"] = Field(
        default="pending",
        description=(
            "The current status of the step (pending, running, complete, error). "
            "Must be 'pending' initially."
        )
    )


@register_model
class MacroPlan(BaseModel):
    """The clean, definitive structured plan for Sovereign Specialists."""

    # Standardizing on 'steps' to match LLM intuition and your Dossier logic
    steps: List[PlanStep] = Field(
        default_factory=list,
        description="The sequence of PlanStep objects required to fulfill the mission."
    )

    reflection: Optional[str] = Field(
        default="",
        description="Architectural reasoning for this plan."
    )

    # 🚀 The missing piece that was defaulting to 0.0 in your logs
    confidence_score: float = Field(
        default=0.0,
        description="Architect certainty score (0.0 to 1.0)."
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual metadata for the mission."
    )


class MacroPlanResponse(BaseModel):
    """Response model for the LLM's planning output."""
    plan: List[PlanStep] = Field(
        default_factory=list,
        description="List of plan steps"
    )
    reflection: Optional[str] = Field(
        default="",
        description="Reasoning behind the plan"
    )



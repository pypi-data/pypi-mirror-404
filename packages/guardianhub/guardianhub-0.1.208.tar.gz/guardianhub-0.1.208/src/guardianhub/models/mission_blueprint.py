# models/agent_models.py
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_serializer,ConfigDict
from .registry.registry import register_model


@register_model
class MissionBlueprintDNA(BaseModel):
    """
    The 'Pattern DNA' evolved from Agent Specs and Sutram Reflection.
    Defines the Mission Brief, Persona-based limits, and Success metrics.
    """
    template_id: str = Field(..., description="TPL-<INTENT>-<ROLE>")
    mission_category: str = Field(..., description="e.g., 'Remediation', 'Audit', 'Recon'")

    # --- MISSION BRIEF (The Blueprint) ---
    brief_summary: str = Field(..., description="The 'Intent' for the Specialist Colonel")
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Verifiable outcomes (e.g., 'CI state == reconciled')"
    )

    # NEW: The 'Why'. Critical for Intelligence Briefings
    mission_rationale: Optional[str] = Field(None, description="Strategic justification for this pattern")

    # --- PERSONA & SAFETY (The Governance) ---
    target_persona: str = Field(..., description="Target user role (e.g. SRE, Admin)")
    auth_level_required: int = Field(default=1, description="Minimum auth level to execute")
    safety_constraints: List[str] = Field(
        default_factory=lambda: ["Read-Only by default"],
        description="Guardrails (e.g., 'No service restarts without human approval')"
    )

    # NEW: Escalation path if the mission fails or safety is breached
    escalation_policy: Optional[str] = Field(default="SRE_LEAD_NOTIFY", description="Who to alert on failure")

    # --- DYNAMIC TOPOLOGY (The Graph Link) ---
    required_context_domains: List[str] = Field(
        default_factory=list,
        description="Which graph domains to query (e.g. ['k8s', 'networking', 'cmdb'])"
    )

    # NEW: Impact Radius metadata for the UI
    estimated_blast_radius: Literal["Entity", "Namespace", "Cluster", "Global"] = Field("Entity")

    # --- DURABILITY & SLA (The Temporal Layer) ---
    # These will be used to configure the Temporal Workflow timeouts automatically
    execution_timeout_seconds: int = Field(default=3600, description="Max time for the Colonel to complete the mission")
    max_retries: int = Field(default=3, description="Standard retry policy for this specific pattern")

    # --- UI & NARRATIVE (The Intelligence Briefing) ---
    # Metadata for the Mission Control frontend
    ui_config: Dict[str, Any] = Field(
        default_factory=lambda: {"icon": "shield-check", "theme": "default"},
        description="Visualization hints for the dashboard"
    )

    # NEW: Narrative blueprint for the final After-Action Report
    briefing_template: str = Field(
        default="Mission {mission_id} handled {intent} for {target_persona}.",
        description="Standardized reporting structure for briefings"
    )

    # --- SYSTEM METADATA ---
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    last_evolved_at: Optional[datetime] = None
    reflection_count: int = Field(default=0)

    # 🟢 THE PURE V2 WAY:
    # Force ISO format during ANY JSON serialization attempt
    @field_serializer('created_at', 'last_evolved_at')
    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat() if dt else None

    # This ensures that if someone calls dict(model), it still tries to stay safe
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "template_id": "TPL-RECON-SRE",
                "created_at": "2026-01-24T07:28:54Z"
            }
        }
    )
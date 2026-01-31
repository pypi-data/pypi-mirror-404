import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict
from .registry.registry import register_model
from guardianhub.config.settings import settings


# =============================================================================
# ZONE 1: ADMINISTRATIVE ENUMS & BASE
# =============================================================================

class AgentStatus(str, Enum):
    # Use the values your DB is actually storing (lowercase 'draft')
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"

class AgentBase(BaseModel):
    """The fundamental identity shared by all agent models."""
    name: str = Field(..., description="Unique identifier for the agent.", json_schema_extra={"example": "cmdb-health-agent"})
    description: str = Field(default="", description="Brief purpose of the agent.")
    system_prompt: str = Field(..., description="The core persona and behavioral instructions.")

# =============================================================================
# ZONE 2: REGISTRY & DB MODELS (Internal & Admin API)
# =============================================================================

class AgentMission(BaseModel):
    """The 'Subscription' data for linking an Agent to a Semantic Tool."""
    agent_name: str = Field(..., description="The name of the agent subscribing.") # 👈 Add this
    name: str = Field(..., description="The name of the semantic tool.")
    mission: str = Field(..., description="The specific intent for this tool in this agent's context.")
    constraints: Optional[str] = Field(None, description="Operational guardrails.")


@register_model
class AgentCreate(AgentBase):
    """The strict schema for Registry DB operations and LLM Generation."""
    domain: str = Field(..., description="The operational domain.", json_schema_extra={"example": "infrastructure"})
    status: AgentStatus = Field(AgentStatus.DRAFT)
    tags: List[str] = Field(default_factory=list)
    tools: List[AgentMission] = Field(
        default_factory=list,
        description="List of mission-authorized tools for this agent."
    )
    reflection_config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Agent(AgentCreate):
    """The complete Agent record including DB-generated fields."""
    id: str = Field(..., description="UUID from the database.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)

@register_model
class AgentResponse(BaseModel):
    """Response model for agent operations."""
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Name of the agent")
    status: AgentStatus = Field(..., description="Current status of the agent")
    domain: str = Field(..., description="Domain of the agent")
    description: str = Field(default="", description="Description of the agent")
    system_prompt: str = Field(..., description="System prompt for the agent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message: Optional[str] = Field(None, description="Additional details about the operation")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

# =============================================================================
# ZONE 3: LLM STRUCTURED OUTPUT MODELS (Registered for LLM awareness)
# =============================================================================

@register_model
class SearchPhrasesResponse(BaseModel):
    search_phrases: List[str] = Field(..., description="1 to 3 relevant search phrases.")

@register_model
class LLMReflectionConfig(BaseModel):
    enabled: Optional[bool] = Field(None)
    optimization_types: List[str] = Field(default_factory=list)
    synthesis_directives: Optional[Dict[str, Any]] = Field(None)

@register_model
class LLMKnowledgeSuggestion(BaseModel):
    type: str = Field(..., description="e.g., 'document', 'query'")
    value: str = Field(..., description="ID or URL")

@register_model
class AgentLLMConfigSuggestion(BaseModel):
    """Structured output for LLM-generated agent proposals."""
    system_prompt: str = Field(...)
    reflection_config: LLMReflectionConfig = Field(...)
    initial_warmup_query: str = Field(...)
    knowledge_suggestions: List[LLMKnowledgeSuggestion] = Field(default_factory=list)

# =============================================================================
# ZONE 4: STRATEGIC DISPATCH & A2A (Wire Formats - Not Registered)
# =============================================================================
@register_model
class AgentSubMission(BaseModel):
    """Tactical 'Marching Orders' dispatched from Sutram to a Specialist."""
    mission_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str = Field(..., description="The unique session ID for the OODA loop.")

    # 🚀 Strategic Context: Handed to Config Defaults
    default_dna: str = "Standard Sovereign Protocol"
    template_id: str = Field(
        description="The OODA template ID being executed."
    )

    # Core Objective
    sub_objective: str = Field(..., description="The specialist's specific goal.")
    assigned_mission_intent: str = Field(..., description="The mission intent from the registry.")

    # 🚀 Shared Situational Awareness
    context_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Facts discovered by previous agents in this session."
    )

    # Constraints & Auth
    constraints: List[str] = Field(default_factory=list)
    auth_context: List[str] = Field(default_factory=list)

    # 🎯 RESILIENCE FIX: Ensure these are simple dicts to avoid
    # Pydantic recursive validation errors in Temporal
    relevant_beliefs: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata & Callback
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # 🎯 THE GLOBAL CALLBACK: Handed to Config Defaults
    callback_url: str = Field(
        default=settings.endpoints.SUTRAM_CALLBACK_URL,
        description="Standardized callback endpoint."
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)
# =============================================================================
# ZONE 3: LLM STRUCTURED OUTPUT MODELS (Registered for LLM awareness)
# =============================================================================

@register_model
class A2AExchangeSchema(BaseModel):
    """
    The 'Handshake' used for Peer-to-Peer capability negotiation.
    The LLM generates this when it needs to consult another agent.
    """
    negotiation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this peer-to-peer negotiation."
    )

    capability_requested: str = Field(
        ...,
        description="The specific capability being requested (e.g., 'get_k8s_logs')."
    )

    required_format: Literal["json", "graph_nodes", "markdown_report"] = Field(
        ...,
        description="The expected format of the response from the peer."
    )

    priority: Literal["low", "medium", "high", "critical"] = Field(
        "medium",
        description="Priority level of the request."
    )

    # The 'Belief' Exchange
    shared_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="A slice of local context/facts to help the receiver process the request."
    )

    token_budget: int = Field(2000, description="Max tokens for the response.")
    hop_limit: int = Field(2, description="Prevents infinite recursive delegation.")


@register_model
class ExplorationPlan(BaseModel):
    """
    The LLM generates this when it identifies a 'Fog of War'
    and needs to propose an inquiry path to the Orchestrator.
    """
    status: Literal["EXPLORING"] = "EXPLORING"
    reason: str = Field(..., description="The gap in knowledge or toolset.")
    target_agents: List[str] = Field(..., description="Peer agents to consult.")
    inquiry: str = Field(..., description="The specific question for the peers.")


class A2AMessage(BaseModel):
    """Carrier for Peer-to-Peer communication."""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    sender: str
    receiver: str
    trace_parent: str
    session_id: str
    message_type: Literal["DELEGATE_EXPLORATION", "NEGOTIATE_CAPABILITY", "DATA_PROVISION"]
    payload: Dict[str, Any]
    hop_count: int = 0
    timestamp: float = Field(default_factory=time.time)


@register_model
class TacticalAuditReport(BaseModel):
    """The formal response from the Safety Officer."""
    success: bool = Field(True)
    decision: Literal["PROCEED", "HALT", "ADVISE"] = Field(...)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    # 🎯 ALIGNMENT: Match the workflow's expectation
    justification: str = Field(..., description="The reasoning behind the safety decision")
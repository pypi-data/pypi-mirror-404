from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from ..registry.registry import register_model


@register_model
class StructuredExtractionResult(BaseModel):
    """
    Unified result model for document classification and metadata extraction.
    The LLM must populate the 'document_type' and 'metadata' fields.
    """
    document_type: str = Field(
        ...,
        description=(
            "The primary classification of the document. Must be one of the provided types "
            "(e.g., 'Invoice', 'Receipt', 'Contract', 'Technical Knowledge Documents', 'Unknown')."
        )
    )
    # FIX: Use default_factory=dict. This ensures that if the field is missing or comes in as null,
    # Pydantic accepts it and defaults it to an empty dictionary {}.
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="A dictionary containing the extracted key-value metadata pairs specific to the classified document_type."
    )
    confidence: float = Field(
        1.0,
        description="A confidence score (0.0 to 1.0) of the classification/extraction accuracy. Default to 1.0."
    )


from pydantic import BaseModel, Field
from typing import List, Optional

@register_model
class DispatchManifest(BaseModel):
    """
    The Strategic Dispatch result. Defines which specialist agent is activated
    and the specific mission parameters they must inherit.
    """
    dispatch_logic: str = Field(
        ...,
        description="Detailed reasoning for selecting the specific agent and mission."
    )
    selected_agent: str = Field(
        ...,
        description="The unique name of the specialist agent, or 'NONE' if no match is found."
    )
    assigned_mission_intent: str = Field(
        ...,
        description="The exact mission intent string from the agent spec being activated."
    )
    # 🚨 NEW: Archetype classification for DNA matching
    mission_category: str = Field(
        default="Recon",
        description="The category of the mission (e.g., 'Remediation', 'Audit', 'Recon', 'Migration')."
    )

    # 🚨 NEW: The 'What' - Crucial for impact radius and topological grounding
    target_entities: List[str] = Field(
        default_factory=list,
        description="List of specific CIs, clusters, or resource names identified from the user query."
    )

    sub_objective: str = Field(
        ...,
        description="The precise instruction for the specialist to plan against."
    )
    required_auth: List[str] = Field(
        default_factory=list,
        description="List of vault keys required for this specific mission."
    )
    ingestion_needs: List[str] = Field(
        default_factory=list,
        description="List of Neo4j queries or ingestion types needed to prime the agent."
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Boundaries and rules the specialist must follow during execution."
    )
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator, ConfigDict
from ..registry.registry import register_model

# --- Unified ToolType Enum ---
# Merges the previous ToolType and AgentToolType into a single, comprehensive enum.
class ToolType(str, Enum):
    """The unified type of a tool, describing its nature and function."""
    # From the old agent_models.py
    AGENTIC = "AgenticTool"
    SEMANTIC = "SemanticTool"
    CONCRETE = "ConcreteTool"
    MCP = "MCPTool"
    CUSTOM = "Custom"
    # From the old tools/models.py or so


class ToolCallStep(BaseModel):
    name: str = Field(..., description="Unique step name")
    title: Optional[str] = Field(None, description="Human-readable title for the step")
    description: Optional[str] = Field(None, description="Detailed description of what the step does")
    operation: str = Field(..., description="Operation ID of the concrete tool to call")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to the operation")
    store_as: Optional[str] = Field(None, description="Variable name to store result for next steps")

class Workflow(BaseModel):
    steps: List[ToolCallStep] = Field(..., description="Ordered sequence of tool calls")
    post_process: Union[str, Dict[str, Any]] = Field(..., description="Python code or configuration to process results after all steps")

class SemanticToolRead(BaseModel):
    name: str
    description: Optional[str] = None
    tool_type: str = Field(ToolType.SEMANTIC.name, description=f"Must be '{ToolType.SEMANTIC.name}'")
    workflow: dict | None = Field(default_factory=dict)  # provide default
    version: str = "1.0.0"

@register_model
class SemanticToolDSL(BaseModel):
    """
    Unified model representing a semantic tool DSL.
    """
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    tool_type: str = Field(ToolType.SEMANTIC.name, description=f"Must be '{ToolType.SEMANTIC.name}'")
    version: str = "1.0.0"
    workflow: Workflow
    tool_ids: List[UUID] = Field(default_factory=list, description="Concrete tools used in this workflow")
    openapi_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Full DSL or optional OpenAPI schema")

    @validator("tool_type")
    def enforce_semantic_type(cls, v):
        if v != ToolType.SEMANTIC.name:
            raise ValueError(f"tool_type must be '{ToolType.SEMANTIC.name}'")
        return v

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        json_schema_extra={
            "example": {
                "name": "check_missing_relationships",
                "description": "Checks CIs for missing relationships",
                "tool_type": "SEMANTIC",
                "version": "1.0.0",
                "tool_ids": ["uuid-of-concrete-tool1", "uuid-of-concrete-tool2"],
                "workflow": {
                    "steps": [
                        {
                            "name": "get_servers",
                            "operation": "getApiNowTableTablename",
                            "parameters": {
                                "tableName": "cmdb_ci_server",
                                "sysparm_query": "install_status=1",
                                "sysparm_limit": 100
                            },
                            "store_as": "servers_data"
                        },
                        {
                            "name": "get_relationships",
                            "operation": "getApiNowTableTablename",
                            "parameters": {"tableName": "cmdb_rel_ci", "sysparm_limit": 100},
                            "store_as": "all_relationships_data"
                        }
                    ],
                    "post_process": "if not all_cis_data or not all_relationships_data: return {'status':'error'}"
                }
            }
        }
    )

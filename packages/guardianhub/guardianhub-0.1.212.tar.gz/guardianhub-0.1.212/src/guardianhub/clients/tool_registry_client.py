# tool_registry_client.py
import json
from typing import Any, Dict, List, Optional

import backoff
import httpx
from guardianhub import get_logger

from guardianhub.config.settings import settings

logger = get_logger(__name__)


class ToolRegistryClient:
    """HTTP client for the tool registry service with retry logic."""

    def __init__(self):
        self._base_url = settings.endpoints.TOOL_REGISTRY_URL
        self._timeout = settings.endpoints.get("TOOL_REGISTRY_TIMEOUT", 10)
        self._service_port = 8002  # Default port for tool registry

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """Base request method with retry logic."""
        url = f"{self._base_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    async def load_agentic_capabilities(self) -> Dict[str, Any]:
        """Get all agent specifications from registry."""
        # First get all agent names
        agent_names = await self._request("GET", "/agent_registry/agents/names")

        # Then fetch specs for each agent
        agent_specs = {}
        for agent_name in agent_names:
            spec = await self._request("GET", f"/agent_registry/agents/{agent_name}/spec")
            agent_specs[agent_name] = spec

        return agent_specs

    async def get_agent_spec(self, agent_name: str) -> Dict[str, Any]:
        """Get agent specification by name."""
        return await self._request("GET", f"/agent_registry/agents/{agent_name}/spec")

    async def search_tools(
            self,
            query: str,
            agent_id: str,  # 🚀 MANDATORY for security wall
            intent: str,  # 🚀 MANDATORY for context filtering
            n_results: int = 5,
            collection: str = "sutram_agentic_tools"
    ) -> List[Dict[str, Any]]:
        """
        Performs Secure Semantic Discovery.
        """
        payload = {
            "query": query,
            "agent_id": agent_id,
            "intent": intent,
            "n_results": n_results,
            "collection": collection
        }

        # Returns the normalized List[Dict] we perfected in the VectorServiceClient
        response = await self._request("POST", "/data_registry/search/vector", json=payload)
        return response.get("results", [])

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        return await self._request("GET", "/tool_registry/api/tools")

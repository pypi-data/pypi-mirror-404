# tool_registry_client.py
import json
from typing import Any, Dict, List, Optional, Literal

import backoff
import httpx
from pydantic import BaseModel, Field
from guardianhub import get_logger

from guardianhub.config.settings import settings

logger = get_logger(__name__)


class ServiceCheck(BaseModel):
    """Model for Consul service check configuration."""
    CheckID: str
    Name: str
    HTTP: str
    Interval: str
    Timeout: str
    Status: str = "passing"


class ServiceRegistration(BaseModel):
    """Model for Consul service registration."""
    ID: str
    Name: str
    Address: str
    Port: int
    Tags: List[str] = Field(default_factory=list)
    Checks: List[ServiceCheck] = Field(default_factory=list)


class NodeDeregistration(BaseModel):
    """Model for Consul node deregistration."""
    Node: str
    ServiceID: Optional[str] = None
    CheckID: Optional[str] = None


class ConsulClient:
    """HTTP client for Consul service discovery and health monitoring."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        self._base_url = base_url or settings.endpoints.CONSUL_HTTP_ADDR
        self._timeout = timeout

    async def _request(
            self,
            method: str,
            path: str,
            json_data: Optional[Dict] = None,
            params: Optional[Dict] = None
    ) -> Any:
        """Base request method with retry logic."""
        url = f"{self._base_url.rstrip('/')}{path}"
        headers = {"Content-Type": "application/json"}

        @backoff.on_exception(
            backoff.expo,
            (httpx.RequestError, httpx.HTTPStatusError),
            max_tries=3
        )
        async def _make_request():
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(
                    method,
                    url,
                    json=json_data,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                if response.status_code == 204:  # No Content
                    return None
                return response.json() if response.content else None

        return await _make_request()

    async def get_service_url(self, service_name: str) -> str:
        """
        High-level discovery: Returns a usable base URL for a healthy service instance.
        If multiple instances exist, it returns the first healthy one.
        """
        health_data = await self.get_service_health(service_name, passing_only=True)

        if not health_data:
            raise RuntimeError(f"No healthy instances of service '{service_name}' found in Consul.")

        # Consul health/service response structure:
        # health_data[0]['Service']['Address'] and health_data[0]['Service']['Port']
        instance = health_data[0].get("Service", {})
        address = instance.get("Address") or health_data[0].get("Node", {}).get("Address")
        port = instance.get("Port")

        if not address or not port:
            raise ValueError(f"Could not resolve Address/Port for service: {service_name}")

        return f"http://{address}:{port}"

    async def register_service(self, service: ServiceRegistration) -> bool:
        """Register a new service with Consul."""
        path = f"/v1/agent/service/register"
        data = service.dict(exclude_none=True)
        try:
            await self._request("PUT", path, json_data=data)
            logger.info(f"Successfully registered service: {service.ID}")
            return True
        except Exception as e:
            logger.error(f"Failed to register service {service.ID}: {str(e)}")
            return False

    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service from Consul."""
        path = f"/v1/agent/service/deregister/{service_id}"
        try:
            await self._request("PUT", path)
            logger.info(f"Successfully deregistered service: {service_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service {service_id}: {str(e)}")
            return False

    async def deregister_node(self, node: NodeDeregistration) -> bool:
        """Deregister a node and/or its services from Consul catalog."""
        path = "/v1/catalog/deregister"
        try:
            await self._request("PUT", path, json_data=node.dict(exclude_none=True))
            logger.info(f"Successfully deregistered node: {node.Node}")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister node {node.Node}: {str(e)}")
            return False

    async def get_service_health(
            self,
            service_name: str,
            passing_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get health status of a service."""
        path = f"/v1/health/service/{service_name}"
        params = {"passing": "1"} if passing_only else {}
        try:
            return await self._request("GET", path, params=params)
        except Exception as e:
            logger.error(f"Failed to get health for service {service_name}: {str(e)}")
            return []

    async def get_services_by_health_state(
            self,
            state: Literal["passing", "warning", "critical"]
    ) -> List[Dict[str, Any]]:
        """Get services by their health state."""
        path = f"/v1/health/state/{state}"
        try:
            return await self._request("GET", path)
        except Exception as e:
            logger.error(f"Failed to get services with state {state}: {str(e)}")
            return []

    async def fire_event(self, name: str, payload: Optional[Dict] = None) -> bool:
        """Fire a new Consul event."""
        path = f"/v1/event/fire/{name}"
        try:
            result = await self._request("PUT", path, json_data=payload or {})
            logger.info(f"Fired event {name} with ID: {result.get('ID')}")
            return True
        except Exception as e:
            logger.error(f"Failed to fire event {name}: {str(e)}")
            return False

    async def list_services(self) -> Dict[str, Any]:
        """List all registered services in Consul."""
        try:
            return await self._request("GET", "/v1/agent/services")
        except Exception as e:
            logger.error(f"Failed to list services: {str(e)}")
            return {}
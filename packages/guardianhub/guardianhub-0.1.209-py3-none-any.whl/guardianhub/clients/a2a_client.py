# services/common/a2a_client.py

import httpx
import time
from typing import Dict, Any, List, Optional
from guardianhub import get_logger
from guardianhub.models.agent_models import  A2AMessage, A2AExchangeSchema

logger = get_logger(__name__)


class A2AClient:
    """
    The secure communication interface for Inter-Agent collaboration.
    Enables recursive delegation, exploration, and capability negotiation.
    """

    def __init__(self, sender_name: str, consul_service: Any):
        self.sender_name = sender_name
        self.consul = consul_service
        self.timeout = 30.0

    async def negotiate_and_delegate(
            self,
            target_agent: str,
            objective: str,
            session_id: str,
            shared_beliefs: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Full-Throttle A2A Loop:
        1. Negotiate (Can you do this?)
        2. Delegate (Do it.)
        """
        # 1. Resolve Target via Consul
        endpoint = await self.consul.resolve_agent_endpoint(target_agent)
        if not endpoint:
            logger.error(f"❌ Could not resolve endpoint for {target_agent}")
            return {"status": "failed", "reason": "Target agent unreachable"}

        # 2. Step 1: Negotiate (Lightweight Handshake)
        handshake = A2AMessage(
            sender=self.sender_name,
            receiver=target_agent,
            session_id=session_id,
            message_type="NEGOTIATE_CAPABILITY",
            payload={"capability_requested": objective},
            trace_parent="OTel_Context_Placeholder"  # Should pull from current span
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"🤝 Negotiating with {target_agent}...")
            neg_response = await client.post(f"{endpoint}/v1/a2a/inbox", json=handshake.model_dump())

            if neg_response.status_code != 200 or neg_response.json().get("status") != "ready":
                logger.warning(f"🚫 {target_agent} declined the mission negotiation.")
                return {"status": "declined", "reason": "Agent not ready or lacks capability"}

            # 3. Step 2: Delegate Exploration (The Heavy Lifting)
            logger.info(f"📡 Dispatching Ranger: {target_agent}")
            exploration_request = handshake.copy(update={
                "message_type": "DELEGATE_EXPLORATION",
                "payload": {"sub_objective": objective},
                "context_beliefs": shared_beliefs or []
            })

            # Increment hop count to prevent infinite loops
            exploration_request.hop_count += 1

            result_response = await client.post(f"{endpoint}/v1/a2a/inbox", json=exploration_request.model_dump())
            result_response.raise_for_status()

            return result_response.json()

    async def broadcast_capability_request(self, intent: str) -> List[str]:
        """
        Queries the mesh to find all agents capable of a specific intent.
        """
        # Logic to hit Consul for specific tags (e.g. 'capability:prometheus')
        return await self.consul.find_agents_by_intent(intent)
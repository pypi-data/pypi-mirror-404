from datetime import datetime
import json
from typing import Dict, Any, List, Optional
from guardianhub import get_logger
from guardianhub.clients import VectorClient, GraphDBClient, ToolRegistryClient
# 🎯 Standardized Contracts
from guardianhub.models import VectorQueryRequest, VectorQueryResponse

logger = get_logger(__name__)


class EpisodicManager:
    """
    The Sovereign Librarian: Standardizes how the AI Guardian remembers.
    Routes sensory data to Satya (Facts), Leela (Narratives), and Dharma (Wisdom).
    """

    def __init__(
            self,
            vector_client: Optional[VectorClient] = None,
            graph_client: Optional[GraphDBClient] = None,
            tool_registry: Optional[ToolRegistryClient] = None
    ):
        self.vector_client = vector_client or VectorClient()
        self.graph_client = graph_client or GraphDBClient()
        self.tool_registry = tool_registry or ToolRegistryClient()

    # ============================================================================
    # 1. SATYA (Truth): Sensory Infrastructure Discovery
    # ============================================================================

    async def record_resource_discovery(self, session_id: str, tool_results: Dict[str, Any]):
        """Promotes tool findings to Graph Facts (Satya)."""
        findings = tool_results.get("report", {}).get("detailed_metrics", [])
        if not findings: return

        query = """
        MERGE (e:Episode {session_id: $session_id})
        WITH e
        UNWIND $findings AS finding
        MERGE (r:Resource {name: finding.tool_name})
        SET r.last_observed = datetime(),
            r.current_status = finding.status,
            r.observed_in_session = $session_id

        MERGE (f:Fact {fact_id: "assertion_" + finding.tool_name + "_" + toString(timestamp())})
        SET f.content = finding.factual_summary_text,
            f.type = 'infrastructure',
            f.last_updated = datetime()

        MERGE (e)-[:DISCOVERED]->(f)
        MERGE (f)-[:ASSERTED_FOR]->(r)
        """
        params = {
            "session_id": session_id,
            "findings": findings
        }
        await self.graph_client._execute_write_query(query, params)

        # guardianhub_sdk/agents/services/episodic_manager.py (Refined Snippet)

    async def get_infrastructure_ground_truth(self, search_term: str, env: str) -> List[Dict[str, Any]]:
        """
        Avatar: Kurma (The Shell/Foundation).
        Retrieves CI topology from Neo4j Satya Segment.
        """
        logger.info(f"🐢 [SATYA] Querying topology for: {search_term} ({env})")

        # Clean the search term to prevent Cypher injection or empty matches
        clean_term = search_term.replace("'", "").replace("\"", "")

        query = """
        MATCH (ci:ConfigurationItem)
        WHERE (ci.name CONTAINS $search OR any(tag IN ci.tags WHERE tag CONTAINS $search))
        AND ci.env = $env
        OPTIONAL MATCH (ci)-[:DEPENDS_ON*1..2]->(dep)
        RETURN ci.name as name, ci.status as status, ci.kind as kind, 
               collect(DISTINCT dep.name) as impacted_services
        LIMIT 25
        """
        try:
            results = await self.graph_client._execute_read_query(
                query,
                {"search": clean_term, "env": env}
            )
            return results if results else []
        except Exception as e:
            logger.error(f"❌ [SATYA] Graph fetch failed: {e}")
            return []  # Fail-open with empty list to satisfy workflow types

    # ============================================================================
    # 2. LEELA (Narrative): Episodic History
    # ============================================================================

    async def record_session_narrative(self, session_id: str, results: Dict[str, Any]):
        """Records the mission story in the Graph and caches it in Vector Memory."""
        try:
            agent_specs = await self.tool_registry.load_agentic_capabilities()
            capabilities_snapshot = list(agent_specs.keys())
        except Exception as e:
            logger.warning(f"⚠️ Capability snapshot failure: {e}")
            capabilities_snapshot = []

        # 1. Update Graph Narrative
        query = """
        MERGE (e:Episode {session_id: $session_id})
        SET e.timestamp = datetime($timestamp),
            e.outcome = $outcome,
            e.capabilities = $capabilities,
            e.summary = $summary,
            e.mission_dna = $mission_dna
        WITH e
        MATCH (m:MissionBlueprint {template_id: $template_id})
        MERGE (e)-[:EXECUTED_AS]->(m)
        """
        params = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "outcome": results.get("status", "unknown"),
            "summary": results.get("reflection", "No synthesis provided."),
            "capabilities": capabilities_snapshot,
            "mission_dna": results.get("mission_dna", "Standard Protocol"),
            "template_id": results.get("active_template_id", "TPL-GENERIC")
        }
        await self.graph_client._execute_write_query(query, params)

        # 🎯 2. Standardized Vector Upsert
        # We push a stringified narrative to the episodes collection
        await self.vector_client.upsert_atomic(
            collection="episodes",
            doc_id=f"narrative-{session_id}",
            text=results.get("reflection", "Mission completion without summary."),
            metadata={
                "session_id": session_id,
                "template_id": params["template_id"],
                "type": "mission_narrative",
                "outcome": params["outcome"]
            }
        )

    # ============================================================================
    # 3. DHARMA (Wisdom): Learning & Hindsight
    # ============================================================================

    async def get_recent_episodes(self, query_text: str, template_id: str) -> List[Dict[str, Any]]:
        """
        [HINDSIGHT HANDSHAKE]
        Uses the Standardized Vector Contract to retrieve historical parallels.
        """
        try:
            # 🚀 THE 10-FOLD MOVE: No more dict interpreting.
            request = VectorQueryRequest(
                query=query_text,
                collection="episodes",
                n_results=5,
                filters={"template_id": template_id}
            )

            response: VectorQueryResponse = await self.vector_client.query(request)

            # Return validated content only
            return [res.model_dump() for res in response.results]
        except Exception as e:
            logger.error(f"❌ [HINDSIGHT] Search failed: {e}")
            return []

    async def get_hindsight(self, current_task: str, template_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Cross-references Graph Lessons with Episode outcomes."""
        query = """
        MATCH (m:MissionBlueprint)-[:GENERATED_LESSON]->(l:ACE_Lesson)
        WHERE (m.template_id = $template_id) OR (toLower(l.topic) CONTAINS toLower($task))
        OPTIONAL MATCH (e:Episode {session_id: l.derived_from})
        RETURN e.outcome AS past_outcome, l.content AS advice, l.topic AS lesson_topic
        ORDER BY l.created_at DESC LIMIT 3
        """
        return await self.graph_client._execute_read_query(query, {"task": current_task, "template_id": template_id})


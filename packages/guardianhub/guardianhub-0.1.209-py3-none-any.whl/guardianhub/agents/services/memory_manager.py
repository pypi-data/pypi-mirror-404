from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from guardianhub import get_logger
from guardianhub.clients import VectorClient, GraphDBClient, ToolRegistryClient
from guardianhub.clients.llm_client import LLMClient
# 🎯 IMPORT OUR NEW CONTRACTS
from guardianhub.models import VectorQueryRequest, VectorQueryResponse
from guardianhub.models.common.common import KeywordList

logger = get_logger(__name__)


class MemoryManager:
    def __init__(
            self,
            vector_client: Optional[VectorClient] = None,
            graph_client: Optional[GraphDBClient] = None,
            tool_registry: Optional[ToolRegistryClient] = None
    ):
        self.vector_client = vector_client or VectorClient()
        self.graph_client = graph_client or GraphDBClient()
        self.tool_registry = tool_registry or ToolRegistryClient()
        self.llm_client = LLMClient()

    async def get_reasoning_context(self, query: str, template_id: str,depth:int, tools: List[Dict]) -> Dict[str, Any]:
        """
        [SOVEREIGN CONTEXT ASSEMBLY]
        Unified retrieval of facts (Graph), beliefs (Graph Lessons), and episodes (Vector).
        """
        logger.info(f"🧠 [MEMORY] Assembling reasoning context for: {query[:50]}...")

        # 1. KEYWORD EXTRACTION (Sensory Priming)
        keywords_list = await self._resolve_keywords(query, tools)
        current_caps = {t['name'] for t in tools}

        # 2. PARALLEL MEMORY FETCH (Tiered Retrieval)
        # We wrap these in try-except to ensure one failure doesn't blind the whole agent
        facts = await self._fetch_facts(template_id, keywords_list)
        beliefs = await self._fetch_beliefs(query, keywords_list, current_caps)
        episodes = await self._fetch_episodes(query, template_id)

        logger.info(
            f"✅ [MEMORY] Retrieval complete: {len(facts)} facts, "
            f"{len(beliefs)} beliefs, {len(episodes)} episodes."
        )

        return {
            "facts": facts,
            "beliefs": beliefs,
            "episodes": episodes,
            "metadata": {
                "assembled_at": datetime.utcnow().isoformat(),
                "keywords_used": keywords_list
            }
        }

    # --- 🛰️ INTERNAL TIERED FETCHERS ---

    async def _fetch_episodes(self, query: str, template_id: str) -> List[Dict]:
        """
        [HINDSIGHT] Pulls historical mission outcomes via the Vector Contract.
        """
        try:
            # 🎯 THE 10-FOLD MOVE: Use the Standardized Request
            request = VectorQueryRequest(
                query=query,
                collection="episodes",
                n_results=5,
                filters={"template_id": template_id}  # Filter by mission type
            )

            response: VectorQueryResponse = await self.vector_client.query(request)

            # Map the validated objects to the dict format the LLM expects
            return [res.model_dump() for res in response.results]
        except Exception as e:
            logger.error(f"❌ [MEMORY] Episode retrieval failed: {e}")
            return []

    async def _fetch_facts(self, template_id: str, keywords: List[str]) -> List[Dict]:
        """[SATYA] Infrastructure ground truth from Neo4j."""
        try:
            return await self.graph_client.get_infrastructure_facts(
                template_id=template_id,
                keywords=keywords
            )
        except Exception as e:
            logger.error(f"❌ [MEMORY] Fact retrieval failed: {e}")
            return []

    async def _fetch_beliefs(self, query: str, keywords: List[str], caps: set) -> List[Dict]:
        """[DHARMA] Past lessons and strategies filtered by current capabilities."""
        try:
            all_beliefs = await self.graph_client.get_ace_lessons(query=query, keywords=keywords)
            actionable = []
            for b in all_beliefs:
                # Direct tool-based filtering or global strategies
                is_actionable = b.get("related_tool") in caps or b.get("type") == "STRATEGY"
                b["actionable"] = is_actionable
                actionable.append(b)
            return actionable
        except Exception as e:
            logger.error(f"❌ [MEMORY] Belief retrieval failed: {e}")
            return []

    # --- 🛠️ RESOLUTION HELPERS ---

    async def _resolve_keywords(self, query: str, tools: List[Dict]) -> List[str]:
        """Resolves keywords from tool metadata or LLM extraction."""
        # 1. Try Tool Metadata first (High Signal)
        if tools and isinstance(tools[0], dict):
            excerpt = tools[0].get('metadata', {}).get('llama_index_metadata', {}).get('excerpt_keywords')
            if excerpt:
                kw = [k.strip() for k in excerpt.split(',')] if isinstance(excerpt, str) else excerpt
                return kw

        # 2. Fallback to LLM extraction (Cognitive Skimming)
        llm_result = await self._extract_search_keywords(query)
        return llm_result.keywords if llm_result.keywords else []

    async def _extract_search_keywords(self, query: str) -> KeywordList:
        """LLM-powered technical entity extraction."""
        system_prompt = """
        You are a technical entity extractor. Extract infrastructure terms, tool names, or CI types.
        Return ONLY a JSON list of strings.
        Example: "investigate DB lag" -> ["database", "latency", "performance"]
        """
        try:
            return await self.llm_client.invoke_structured_model(
                user_input=query,
                system_prompt_template=system_prompt,
                response_model_name="KeywordList",
            )
        except Exception:
            return KeywordList(keywords=self._basic_keyword_extraction(query), source="fallback")

    def _basic_keyword_extraction(self, query: str) -> List[str]:
        """Regex-free clean split fallback."""
        noise = {"need", "check", "show", "status", "what", "find"}
        words = query.lower().replace("?", "").split()
        return [w for w in words if w not in noise and len(w) > 2][:5]

    async def get_hindsight_segment(self, query: str, template_id: str) -> List[Dict[str, Any]]:
        """
        Standardized entry point for historical memory retrieval.
        Handles the Vector Contract and Filtering.
        """
        try:
            request = VectorQueryRequest(
                query=query,
                collection="episodes",
                n_results=5,
                filters={"template_id": template_id}
            )

            response: VectorQueryResponse = await self.vector_client.query(request)

            # 🎯 THE 10-FOLD RETURN:
            # Convert validated result objects into a clean dict format for LLM context
            return [res.model_dump() for res in response.results]
        except Exception as e:
            logger.error(f"❌ [MEMORY_MANAGER] Hindsight retrieval failure: {e}")
            return []

    # Inside MemoryManager class

    async def assimilate_proposal(self, current_metadata: Dict, proposal_payload: Dict) -> Dict:
        """
        [DHARMA INGESTION]
        Standardizes how the Architect's plan enters the nervous system.
        Ensures the 'Why' (Reflection) is paired with the 'What' (MacroPlan).
        """
        session_id = proposal_payload.get('session_id', 'unknown')
        logger.info(f"🧠 [MEMORY] Assimilating Tactical Proposal for session {session_id}")

        # 1. Identity & DNA Mapping
        # We preserve the original DNA to ensure the 'Law' remains consistent
        dna_anchor = current_metadata.get("mission_dna") or "Audit Only"
        template_id = current_metadata.get("template_id", "TPL-GENERIC")

        # 2. Extract Narrative Logic
        # This is the Specialist's ephemeral reasoning that will eventually become a 'Lesson'
        reflection = proposal_payload.get("reflection") or proposal_payload.get("rationale",
                                                                                "No tactical rationale provided.")

        return {
            "macro_plan": proposal_payload.get("macro_plan", []),
            "metadata": {
                **current_metadata,
                "handshake_status": "PLAN_READY",
                "dispatch_in_progress": False,
                "law_segment": dna_anchor,  # Permanent Governance
                "wisdom_segment": reflection,  # Decision Logic for future Hindsight
                "template_id": template_id,
                "ingested_at": datetime.utcnow().isoformat()
            }
        }

    async def assimilate_intervention(
            self,
            current_plan: List,
            current_context: Dict,
            current_metadata: Dict,
            result_payload: Dict
    ) -> Dict:
        """
        [SATYA CONSOLIDATION]
        Standardizes how real-world tool results are merged into the Mission State.
        Prepares the data for the 'After Action Report' (AAR).
        """
        mission_id = result_payload.get('mission_id', 'unknown')
        logger.info(f"⚡ [MEMORY] Assimilating intervention results for mission {mission_id}")

        # 1. Plan State Update
        # We find the 'running' step and mark it complete with real data
        updated_plan = []
        for step in current_plan:
            new_step = step.copy()
            if new_step.get("status") == "running" or new_step.get("step_id") == result_payload.get("step_id"):
                new_step["status"] = "completed"
                # We store the raw output here for technical tracing
                new_step["result_data"] = result_payload.get("result")
                new_step["completed_at"] = datetime.utcnow().isoformat()
            updated_plan.append(new_step)

        # 2. Context Enrichment
        # We add the result to the macro_context so the next step's LLM prompt has it
        new_context = {**current_context}
        new_context[mission_id] = result_payload

        # 3. Final State Delta
        return {
            "macro_plan": updated_plan,
            "macro_context": new_context,
            "metadata": {
                **current_metadata,
                "dispatch_in_progress": False,  # Release the workflow lock
                "last_mission_id": mission_id,
                "last_result_status": result_payload.get("status", "unknown")
            }
        }
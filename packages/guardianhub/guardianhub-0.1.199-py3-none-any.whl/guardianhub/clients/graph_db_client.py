"""
Graph Database Client for Neo4j operations.

This module provides functionality for:
- Mission DNA persistence and retrieval
- Context bullet management and scoring
- Infrastructure fact storage and retrieval
- Shared blackboard operations for multi-agent coordination
- Template management with migration support
"""

import datetime
import json
import uuid
from typing import Dict, Any, Optional, List, Literal, Union

import httpx
import yaml

from guardianhub import get_logger
from guardianhub.config.settings import settings
from guardianhub.models.common.common import KeywordList
from guardianhub.models.mission_blueprint import MissionBlueprintDNA
from guardianhub.models.template.suggestion import TemplateSchemaSuggestion

# Module logger
logger = get_logger(__name__)


class GraphDBClient:
    """
    Neo4j Graph Database Client for mission-critical operations.
    
    Provides high-level interface for:
    - Mission Blueprint DNA management
    - Context bullet curation and scoring
    - Infrastructure fact tracking
    - Multi-agent shared blackboard coordination
    """

    # ============================================================================
    # INITIALIZATION & CONFIGURATION
    # ============================================================================

    def __init__(self, poll_interval: int = 5, poll_timeout: int = 300) -> None:
        """Initialize the GraphDB client with configuration from settings."""
        self.api_url = settings.endpoints.get("GRAPH_DB_URL")
        self.headers = {"Accept": "application/json"}
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

        self.client = httpx.AsyncClient(
            headers=self.headers, 
            base_url=self.api_url, 
            timeout=self.poll_timeout + 60
        )
        logger.info(f"🔗 GraphDBClient initialized for URL: {self.api_url}")

    # ============================================================================
    # CORE HELPER METHODS
    # ============================================================================

    async def _execute_write_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """Execute a write query against the Graph DB service."""
        try:
            response = await self.client.post(
                "/execute-cypher-write",
                json={"query": query, "parameters": parameters},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json().get("status") == "success"
            if result:
                logger.debug(f"✅ Write query executed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ GraphDB Write Error: {e}")
            return False

    async def _execute_read_query(self, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Standardized Read: Returns the 'results' list from the Graph."""
        try:
            response = await self.client.post(
                "/query-cypher",
                json={"query": query, "parameters": parameters},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return data.get("results", [])
            return []
        except Exception as e:
            logger.error(f"❌ GraphDB Read Error: {e}")
            return []

    # ============================================================================
    # MISSION DNA MANAGEMENT
    # ============================================================================

    async def save_mission_dna(self, dna: MissionBlueprintDNA, active_agent: Optional[str] = None) -> bool:
        """
        Anchors the MissionBlueprintDNA while establishing the Agent-Mission link.
        Supports the 'Mission Story' (What must be done) and
        the 'Agent Story' (Who is authorized/learning).
        """
        query = """
        // 1. MISSION STORY: MERGE the Blueprint (The Law)
        MERGE (m:MissionBlueprint {template_id: $template_id})
        SET m.mission_category = $mission_category,
            m.brief_summary = $brief_summary,
            m.mission_rationale = $mission_rationale,
            m.target_persona = $target_persona,
            m.auth_level_required = $auth_level_required,
            m.success_criteria = $success_criteria,
            m.safety_constraints = $safety_constraints,
            m.escalation_policy = $escalation_policy,
            m.estimated_blast_radius = $estimated_blast_radius,
            m.execution_timeout_seconds = $execution_timeout_seconds,
            m.briefing_template = $briefing_template,
            m.version = $version,
            m.last_evolved_at = datetime(),
            m.reflection_count = coalesce(m.reflection_count, 0) + $reflection_inc

        // 2. TOPOLOGICAL STORY: Link to the overarching Category
        MERGE (c:MissionCategory {name: $mission_category})
        MERGE (m)-[:BELONGS_TO]->(c)

        // 3. AGENT STORY: Link to the Authorized Specialist
        // This allows the Agent to 'own' its performance history for this DNA
        FOREACH (agent_name IN CASE WHEN $active_agent IS NOT NULL THEN [$active_agent] ELSE [] END |
            MERGE (a:AgentSpecialist {name: agent_name})
            MERGE (a)-[r:AUTHORIZED_FOR]->(m)
            SET r.last_used = datetime()
        )

        RETURN m.template_id as id
        """

        params = {
            "template_id": dna.template_id,
            "mission_category": dna.mission_category,
            "brief_summary": dna.brief_summary,
            "mission_rationale": dna.mission_rationale,
            "target_persona": dna.target_persona,
            "auth_level_required": dna.auth_level_required,
            "success_criteria": dna.success_criteria,
            "safety_constraints": dna.safety_constraints,
            "escalation_policy": dna.escalation_policy,
            "estimated_blast_radius": dna.estimated_blast_radius,
            "execution_timeout_seconds": dna.execution_timeout_seconds,
            "briefing_template": dna.briefing_template,
            "version": dna.version,
            "reflection_inc": 1 if dna.reflection_count > 0 else 0,
            "active_agent": active_agent  # 🎯 Connect the 'Who' to the 'What'
        }

        logger.info(f"⚓ Anchoring Dual-Story DNA: {dna.template_id} for Agent: {active_agent}")
        return await self._execute_write_query(query, params)

    # ============================================================================
    # TEMPLATE & DNA RETRIEVAL
    # ============================================================================

    # ============================================================================
    # MISSION DNA / BLUEPRINT RETRIEVAL
    # ============================================================================

    async def get_mission_dna(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        STRICT RETRIEVAL: Fetches only the Sovereign DNA for a Mission.
        Excludes formatting/schema templates to ensure governance integrity.
        """
        query = """
        MATCH (m:MissionBlueprint {template_id: $template_id})

        // Optional: Pull the Category for context
        OPTIONAL MATCH (m)-[:BELONGS_TO]->(c:MissionCategory)

        RETURN properties(m) as dna, 
               c.name as category,
               m.version as version,
               m.last_evolved_at as last_modified
        """
        try:
            results = await self._execute_read_query(query, {"template_id": template_id})
            result = results[0]
            dna = result["dna"]
            # Enrich with topological data
            dna["category"] = result.get("category")
            dna["version"] = result.get("version")
            logger.info(f"🧬 [DNA_FETCH] Mission Blueprint loaded: {template_id} (v{dna.get('version')})")
            logger.warning(f"⚠️ [DNA_FETCH] Unauthorized or missing Mission DNA: {template_id}")
            return dna

        except Exception as e:
            logger.error(f"❌ [DNA_FETCH] Critical failure retrieving DNA {template_id}: {e}")
            return None

    # ============================================================================
    # CONTEXT BULLET MANAGEMENT
    # ============================================================================

    async def merge_context_bullet(self, template_id: str, bullet_data: Dict[str, Any]) -> bool:
        """
        [DHARMA EVOLUTION]
        ACE Curator: Anchors a new Strategic Directive to the Mission DNA.
        Converts a Specialist's 'Reflection' into the system's 'Operating Law'.
        """
        bullet_id = bullet_data.get("bullet_id", f"BUL-{uuid.uuid4().hex[:8]}")

        query = """
            // 1. MISSION DNA ANCHOR: Ensure the Blueprint exists
            MERGE (m:MissionBlueprint {template_id: $template_id})
            ON CREATE SET m.created_at = datetime() 

            // 2. WISDOM ANCHOR: Create/Update the Directive
            MERGE (b:ContextBullet {bullet_id: $bullet_id})
            ON CREATE SET 
                b.content = $content,
                b.type = $type,
                b.domain = $domain,
                b.keywords = $keywords,
                b.source_curator = $source_curator,
                b.helpful_count = 1,  // Starts with 1 because it was just proven
                b.harmful_count = 0,
                b.created_at = datetime()
            ON MATCH SET
                b.keywords = $keywords, // Keep keywords fresh
                b.last_proven_at = datetime()

            // 3. TOPOLOGICAL BINDING: Use the 'Evolved' relationship
            MERGE (m)-[:EVOLVED_STRATEGY]->(b)

            RETURN count(b) AS merge_count
            """

        params = {
            "template_id": template_id,
            "bullet_id": bullet_id,
            "content": bullet_data.get("content", ""),
            "type": bullet_data.get("type", "STRATEGY"),
            "domain": bullet_data.get("domain", "Sovereign"),
            "keywords": bullet_data.get("keywords", []),
            "source_curator": bullet_data.get("source_curator", "Specialist-Reflection")
        }

        logger.info(f"🎯 [CURATOR] Anchoring Wisdom {bullet_id} to Blueprint {template_id}")
        result = await self._execute_write_query(query, params)

        if result:
            logger.info(f"✅ [CURATOR] Strategy evolved: {bullet_id}")
        else:
            logger.error(f"❌ [CURATOR] Failed to anchor wisdom: {bullet_id}")
        return result

    async def update_bullet_scores(
            self,
            bullet_id: str,
            feedback_type: Literal['helpful', 'harmful'],
            weight: float = 1.0  # 🚀 New: Allow weighted feedback
    ) -> bool:
        """
        [KARMA TUNING]
        Updates the utility metrics of a Strategic Directive.
        Used to prune ineffective strategies and boost proven wisdom.
        """
        logger.debug(f"📊 [FEEDBACK] Tuning Wisdom {bullet_id}: {feedback_type} (Weight: {weight})")

        # 🎯 Penalty Bias: In Sovereign systems, 'Harmful' acts have higher weight by default
        effective_weight = weight if feedback_type == 'helpful' else weight * 2.0

        if feedback_type == 'helpful':
            score_clause = "b.helpful_count = coalesce(b.helpful_count, 0) + $weight"
        elif feedback_type == 'harmful':
            score_clause = "b.harmful_count = coalesce(b.harmful_count, 0) + $weight"
        else:
            logger.warning(f"⚠️ Invalid feedback type: {feedback_type}")
            return False

        query = f"""
        MATCH (b:ContextBullet {{bullet_id: $bullet_id}}) 
        SET {score_clause}, 
            b.last_feedback_at = datetime(),
            b.total_interactions = coalesce(b.total_interactions, 0) + 1
        RETURN b.bullet_id as id
        """

        params = {"bullet_id": bullet_id, "weight": effective_weight}

        result = await self._execute_write_query(query, params)

        if result:
            logger.info(f"✅ [FEEDBACK] Wisdom calibrated: {bullet_id} increased {feedback_type}")
        return result



    async def get_top_directives_for_mission(
            self,
            template_id: str,
            user_persona: str,
            limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        [DHARMA RETRIEVAL]
        Retrieves the most effective tactical directives anchored to a Mission DNA.
        Prioritizes proven strategies that align with the Blueprint's history.
        """
        logger.debug(f"🔍 Harvesting Top Directives for DNA: {template_id}")

        query = """
            MATCH (m:MissionBlueprint {template_id: $template_id})-[:EVOLVED_STRATEGY]->(b:ContextBullet)

            // 1. Calculate the 'Wisdom Score'
            WITH b,
                 (coalesce(b.helpful_count, 0) - (coalesce(b.harmful_count, 0) * 2.0)) AS net_utility,
                 CASE WHEN b.target_persona = $user_persona THEN 1.5 ELSE 1.0 END AS persona_weight,
                 // Decay score for stale strategies (Freshness factor)
                 toFloat(duration.between(coalesce(b.created_at, datetime()), datetime()).days) AS days_old

            // 2. Apply Sovereign Weighting: utility * persona / decay
            WITH b, (net_utility * persona_weight) / (1.0 + (days_old / 45.0)) AS wisdom_score

            RETURN properties(b) AS directive, wisdom_score
            ORDER BY wisdom_score DESC
            LIMIT $limit
            """

        payload = {
            "query": query,
            "parameters": {
                "template_id": template_id,
                "user_persona": user_persona,
                "limit": limit
            }
        }

        try:
            response = await self.client.post("/query-cypher", json=payload, timeout=30.0)
            response.raise_for_status()
            results = response.json().get("results", [])

            # 🎯 The "10-fold" Return: Map directives back to the Assembly Engine format
            directives = []
            for rec in results:
                d = rec["directive"]
                directives.append({
                    "id": d["bullet_id"],
                    "content": d["content"],
                    "type": d.get("type", "STRATEGY"),
                    "domain": d.get("domain", "Sovereign"),
                    # We normalize the internal wisdom_score for the LLM's context scoring
                    "score": round(rec["wisdom_score"], 2)
                })

            logger.info(f"🧠 [WISDOM_FETCH] Loaded {len(directives)} directives for DNA {template_id}")
            return directives

        except Exception as e:
            logger.error(f"❌ [WISDOM_FETCH] Failed to harvest directives for {template_id}: {e}")
            return []

    async def get_bullets_by_id(self, bullet_ids: List[str]) -> List[Dict[str, Any]]:
        """
        [DHARMA VALIDATION]
        Retrieves detailed metadata for specific wisdom bullets.
        Used by the ContextAssemblyEngine to perform final 'Truth Scoring'.
        """
        if not bullet_ids:
            return []

        # We fetch the properties + the count of how many Blueprints currently trust this bullet
        query = """
        MATCH (b:ContextBullet)
        WHERE b.bullet_id IN $bullet_ids

        OPTIONAL MATCH (m:MissionBlueprint)-[r:EVOLVED_STRATEGY]->(b)

        RETURN properties(b) as properties, 
               count(m) as trust_factor,
               labels(b) as labels
        """

        try:
            response = await self.client.post(
                "/query-cypher",
                json={"query": query, "parameters": {"bullet_ids": bullet_ids}},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                enriched_bullets = []
                for rec in data.get('results', []):
                    bullet = rec['properties']
                    # Inject structural metadata for the Assembly Engine
                    bullet["trust_factor"] = rec["trust_factor"]
                    bullet["is_ace_bullet"] = "ContextBullet" in rec["labels"]
                    enriched_bullets.append(bullet)

                logger.debug(f"📊 [WISDOM_LOAD] Re-hydrated {len(enriched_bullets)} bullets from ID list.")
                return enriched_bullets

            return []
        except Exception as e:
            logger.error(f"❌ [WISDOM_LOAD] Failed to retrieve wisdom lineage: {e}")
            return []

    async def get_infrastructure_facts(
            self,
            template_id: str,
            keywords: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        [SATYA RETRIEVAL]
        Retrieve topological 'Ground Truth' anchored to the Mission DNA.
        Ensures that the Agent inherits the state of the infrastructure from previous 'Karma'.
        """
        if not keywords:
            logger.warning(f"⚠️ No keywords for fact retrieval in {template_id}. Yielding empty context.")
            return []

        # 1. THE TOPOLOGICAL TRAVERSAL
        # We prioritize facts that are directly linked to the Blueprint DNA.
        cypher_query = """
        MATCH (m:MissionBlueprint {template_id: $template_id})

        // Traverse the links to discovered facts
        MATCH (m)-[:HAS_RECENT_FACT]->(f:InfrastructureFact)

        // Connect to the actual CI/Resource for naming
        OPTIONAL MATCH (r:Resource)-[:PROVIDES_ASSERTION]->(f)

        // CASE-INSENSITIVE Cognitive Filtering
        WITH f, r, [kw IN $keywords | toLower(kw)] AS lower_kws
        WHERE any(kw IN lower_kws WHERE 
            toLower(f.content) CONTAINS kw OR 
            toLower(r.name) CONTAINS kw
        )

        // Return the distinct Fact Bundle
        RETURN DISTINCT {
            resource: coalesce(r.name, "system"),
            summary: f.content,
            metrics_raw: f.metrics,
            observed_at: toString(f.updated_at),
            source_agent: f.source_agent
        } as fact
        ORDER BY fact.observed_at DESC
        LIMIT 5
        """

        params = {"template_id": template_id, "keywords": keywords}

        try:
            response = await self.client.post(
                "/query-cypher",
                json={"query": cypher_query, "parameters": params},
                timeout=30.0
            )
            response.raise_for_status()
            results = response.json().get('results', [])

            # 🧠 HYDRATION LAYER: Reconstructing the sensory data
            enriched_facts = []
            for record in results:
                fact = record.get("fact", {})
                if fact.get("metrics_raw"):
                    try:
                        # Metrics were stored as JSON strings in Neo4j to preserve types
                        fact["metrics"] = json.loads(fact["metrics_raw"])
                    except (json.JSONDecodeError, TypeError):
                        fact["metrics"] = {}
                    del fact["metrics_raw"]
                enriched_facts.append(fact)

            logger.info(f"📊 [SATYA_LOAD] Inherited {len(enriched_facts)} infrastructure facts for {template_id}")
            return enriched_facts

        except Exception as e:
            logger.error(f"❌ [SATYA_LOAD] Retrieval failed for {template_id}: {e}", exc_info=True)
            return []

    async def get_ace_lessons(
            self,
            query: Optional[str] = None,
            keywords: Optional[List[str]] = None,
            limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        [DHARMA RETRIEVAL]
        Retrieve ACE Lessons (Beliefs) from the Agent Space.
        Prioritizes lessons learned by similar Specialists or linked to active Tools.
        """
        if not keywords:
            logger.warning("⚠️ [WISDOM] No keywords provided. Agent is flying blind.")
            return []

        # 1. THE RELATIONAL SEARCH
        # We look for lessons in the ContextBullet pool that match keywords,
        # but we also check if they are linked to a successful Episode.
        cypher_query = """
        MATCH (b:ContextBullet)
        WHERE any(kw IN $keywords WHERE 
            toLower(b.content) CONTAINS toLower(kw) OR 
            toLower(b.domain) CONTAINS toLower(kw)
        )

        // Optional: Tie back to the Specialist or Blueprint for 'Success Proof'
        OPTIONAL MATCH (m:MissionBlueprint)-[r:EVOLVED_STRATEGY]->(b)

        WITH b, count(r) as proven_count, [kw IN $keywords | toLower(kw)] as lower_kws

        // Calculate a cognitive score based on keyword density + historical proof
        WITH b, proven_count,
             size([kw IN lower_kws WHERE toLower(b.content) CONTAINS kw]) as match_density

        RETURN {
            id: b.bullet_id,
            content: b.content,
            type: b.type,
            domain: b.domain,
            related_tool: b.related_tool,
            proven_utility: proven_count,
            score: (match_density * 1.0 / size($keywords)) + (proven_count * 0.1)
        } as lesson
        ORDER BY lesson.score DESC
        LIMIT $limit
        """

        try:
            response = await self.client.post(
                "/query-cypher",
                json={
                    "query": cypher_query,
                    "parameters": {"keywords": keywords, "limit": limit}
                },
                timeout=30.0
            )
            response.raise_for_status()
            results = response.json().get("results", [])

            lessons = [record["lesson"] for record in results if "lesson" in record]
            logger.info(f"🧠 [WISDOM_LOAD] Harvested {len(lessons)} actionable lessons from Agent Space.")
            return lessons

        except Exception as e:
            logger.error(f"❌ [WISDOM_LOAD] Failed to retrieve agentic wisdom: {e}", exc_info=True)
            return []

    # ==========================================================================
    # 2. SHARED BLACKBOARD (Mission-Anchored)
    # ==========================================================================

    async def anchor_mission_findings(
            self,
            session_id: str,
            template_id: str,
            findings: List[Dict[str, Any]],
            source_agent: str = "specialist"
    ) -> bool:
        """
        [SATYA CONSOLIDATION]
        The Single Source of Truth for promoting field discoveries.
        Links the 'Fact' to the 'Mission DNA' and the 'Episode'.
        """
        if not findings:
            return True

        # Prepare findings with serialized metrics
        processed_findings = []
        for f in findings:
            processed_findings.append({
                **f,
                "fact_id": f"F-{template_id}-{f.get('tool_name', 'unknown').replace(' ', '_')}",
                "metrics_json": json.dumps(f.get("metrics", {}))
            })

        query = """
        UNWIND $findings AS finding

        // 1. ANCHOR: Locate the Mission DNA and the Session Episode
        MATCH (m:MissionBlueprint {template_id: $template_id})
        MERGE (e:Episode {session_id: $session_id})

        // 2. RESOURCE: MERGE the global CI/Resource
        MERGE (r:Resource {name: finding.tool_name})
        SET r.last_observed = datetime(),
            r.current_status = finding.status

        // 3. FACT: Create/Update the Immutable Fact
        MERGE (f:InfrastructureFact {fact_id: finding.fact_id})
        SET f.content = finding.factual_summary_text,
            f.metrics = finding.metrics_json,
            f.updated_at = datetime(),
            f.source_agent = $source_agent

        // 4. TOPOLOGY: Establish the Triple-Bind
        MERGE (m)-[:HAS_RECENT_FACT]->(f)  // DNA Link
        MERGE (e)-[:DISCOVERED]->(f)        // Session Link
        MERGE (r)-[:PROVIDES_ASSERTION]->(f) // Resource Link

        RETURN count(f) as fact_count
        """

        params = {
            "session_id": session_id,
            "template_id": template_id,
            "findings": processed_findings,
            "source_agent": source_agent
        }

        logger.info(f"⚓ [CONSOLIDATOR] Anchoring {len(findings)} findings for session {session_id}")
        return await self._execute_write_query(query, params)



    async def upsert_infrastructure_fact(
            self,
            template_id: str,
            resource_name: str,
            fact_content: str,
            metrics: Optional[Dict[str, Any]] = None,
            source_agent: str = "system"
    ) -> bool:
        """
        SENSORY INPUT: Records a new finding into the graph.
        Anchors the Fact to the Mission Pattern and the specific Resource.
        """

        # 1. Prepare the Fact ID to prevent duplication within a mission context
        # format: F-<TEMPLATE>-<RESOURCE_NAME>
        fact_id = f"F-{template_id}-{resource_name.replace(' ', '_')}"

        query = """
        // 1. Ensure the Mission anchor exists
        MATCH (m) 
        WHERE (m:MissionBlueprint OR m:DocumentTemplate) AND m.template_id = $template_id
    
        // 2. MERGE the Resource (The 'What')
        MERGE (r:Resource {name: $resource_name})
        SET r.last_observed = datetime(),
            r.observed_by = $source_agent
    
        // 3. MERGE the Fact (The 'Intelligence')
        MERGE (f:InfrastructureFact {fact_id: $fact_id})
        SET f.content = $content,
            f.metrics = $metrics_json,
            f.updated_at = datetime(),
            f.source_agent = $source_agent
    
        // 4. Establish Topological Links
        MERGE (r)-[:PROVIDES_ASSERTION]->(f)
        MERGE (m)-[:HAS_RECENT_FACT]->(f)
    
        RETURN f.fact_id as id
        """

        params = {
            "template_id": template_id,
            "resource_name": resource_name,
            "fact_id": fact_id,
            "content": fact_content,
            "metrics_json": json.dumps(metrics or {}),
            "source_agent": source_agent
        }

        try:
            success = await self._execute_write_query(query, params)
            if success:
                logger.info(f"🛰️ Fact promoted to Graph: {fact_id} (Source: {source_agent})")
            return success
        except Exception as e:
            logger.error(f"❌ Failed to promote fact {fact_id}: {e}")
            return False


    async def create_lesson_node(
            self,
            template_id: str,
            topic: str,
            type: str,
            content: str,
            related_tool: Optional[str] = None,
            session_id: Optional[str] = None
    ) -> bool:
        """
        [DHARMA ANCHOR]
        Creates an ACE_Lesson node and anchors it to the MissionBlueprint.
        This allows the system to 'learn' from this specific mission type.
        """
        query = """
        // 1. Ensure the Mission DNA exists as the anchor
        MATCH (m:MissionBlueprint {template_id: $template_id})
    
        // 2. MERGE the Lesson based on content to prevent duplicates
        MERGE (l:ACE_Lesson {content: $content})
        SET l.topic = $topic,
            l.type = $type,
            l.related_tool = $related_tool,
            l.derived_from = $session_id,
            l.created_at = datetime()
    
        // 3. Link the Wisdom to the Law (The DNA)
        MERGE (m)-[:GENERATED_LESSON]->(l)
    
        RETURN count(l) as lesson_count
        """
        params = {
            "template_id": template_id,
            "topic": topic,
            "type": type,
            "content": content,
            "related_tool": related_tool,
            "session_id": session_id
        }
        return await self._execute_write_query(query, params)

    async def get_infrastructure_ground_truth(self, search_term: str, env: str) -> List[Dict[str, Any]]:
        """
        [SATYA GATEKEEPER]
        Bridges the Specialist's need for reality with the GraphDB's storage.
        """
        cypher = """
        MATCH (ci:ConfigurationItem)-[:DEPENDS_ON*1..2]->(dep)
        WHERE (ci.name CONTAINS $search OR ci.tags CONTAINS $search)
        AND ci.env = $env
        RETURN ci.name as name, 
               ci.status as status, 
               ci.kind as kind,
               collect(dep.name) as impacted_services
        LIMIT 25
        """
        params = {"search": search_term, "env": env}

        # 🎯 THE FIX: Use 'query' (READ), not '_execute_write_query' (WRITE)
        # This ensures we get the List[Dict] instead of just a Boolean success.
        return await self._execute_read_query(cypher, {"search": search_term, "env": env})
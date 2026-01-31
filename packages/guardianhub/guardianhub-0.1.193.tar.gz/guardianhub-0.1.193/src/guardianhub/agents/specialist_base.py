# guardianhub_sdk/agents/specialist_base.py
import json
import uuid
from typing import Dict, Any, List, Optional, TypeVar, Union
from fastapi import APIRouter, HTTPException

from guardianhub.clients.llm_client import LLMClient

from guardianhub.clients.consul_client import ConsulClient
from guardianhub.clients.tool_registry_client import ToolRegistryClient
from guardianhub.config.settings import settings
from guardianhub.agents.workflows.constants import get_all_activities
from guardianhub.agents.workflows.agent_contract import ActivityRoles
from guardianhub.models.agent.contracts.action import ActionStep,ActionOutcome
from guardianhub.models.agent.contracts import DiscoveryRequest,DiscoveryResponse
from guardianhub.models.agent.contracts import  HistoryRequest,HistoryResponse
from guardianhub.models.agent.contracts.tactical import TacticalBundle,TacticalAuditReport,TACTICAL_RISK_PROMPT
from guardianhub.models.agent.contracts.attainment import AttainmentCheck,AttainmentReport
from guardianhub.models.agent.contracts.debrief import SummaryBrief,IntelligenceReport
from guardianhub.models.agent.contracts.learning import AfterActionReport , LearningAnchor
from guardianhub.models.agent.contracts.completion import  MissionManifest, CallbackAck
from guardianhub.models.agent.contracts.support import  SupportRequest,PeerSupportOutcome
from guardianhub.models.agent_models import AgentSubMission
from guardianhub.models.builtins.vector_models import VectorQueryRequest, VectorQueryResponse
from guardianhub.models.template.agent_plan import MacroPlan
from guardianhub.agents.services.memory_manager import MemoryManager
from guardianhub.agents.services.episodic_manager import EpisodicManager
from guardianhub.clients.a2a_client import A2AClient
from guardianhub.clients.vector_client import VectorClient
from guardianhub.clients.graph_db_client import GraphDBClient
from guardianhub.clients.tool_registry_client import ToolRegistryClient
from guardianhub.clients.classification_client import ClassificationClient
from guardianhub.clients.ocr_client import OCRClient
from guardianhub.clients.paperless_client import PaperlessClient
from guardianhub.clients.text_cleaner_client import TextCleanerClient
from guardianhub.models.agent.contracts.tactical import RiskAnalysisReport
from guardianhub import get_logger
from temporalio import activity
from httpx import AsyncClient

logger = get_logger(__name__)

# Type variable for client types
T = TypeVar('T')


class SovereignSpecialistBase:
    """
    The Foundation for all Specialist Agents.
    Encapsulates Planning, Execution, and Context Management.
    """

    def __init__(self, activities_instance: Any, **kwargs):
        # 1. Identity
        self.spec = settings.specialist_settings
        self.name = self.spec.agent_name

        # 2. Standardize Core Clients (from kwargs or defaults)
        self.llm = kwargs.get('llm_client') or LLMClient()
        self.vector_client = kwargs.get('vector_client') or VectorClient()
        self.graph_client = kwargs.get('graph_client') or GraphDBClient()
        self.tool_registry_client = kwargs.get('tool_registry_client') or ToolRegistryClient()
        self.consul_client = kwargs.get('consul_client') or ConsulClient()
        self.temporal_client = kwargs.get('temporal_client')

        # 🎯 FIX: Initialize custom_clients so get_client() works
        self.custom_clients: Dict[str, Any] = kwargs.get('custom_clients', {})

        # 3. Initialize core services (Senses)
        self.memory = MemoryManager(
            vector_client=self.vector_client,
            graph_client=self.graph_client,
            tool_registry=self.tool_registry_client
        )
        self.episodes = EpisodicManager(
            vector_client=self.vector_client,
            graph_client=self.graph_client,
            tool_registry=self.tool_registry_client
        )
        self.a2a = A2AClient(sender_name=self.name, consul_service=self.consul_client)

        # 4. Domain Activity Instance (The Muscle)
        self.activities_instance = activities_instance

        # 🧬 THE FUSION MOVE
        if hasattr(self.activities_instance, "fuse_with_base"):
            self.activities_instance.fuse_with_base(self)

        # 5. API Gateway Setup
        self.router = APIRouter(prefix="/v1/mission")
        self._setup_routes()

    def get_client(self, client_name: str, client_type: Optional[T] = None) -> Optional[T]:
        """
        Retrieves an extension client from the custom registry.
        """
        client = self.custom_clients.get(client_name)
        if client is not None and client_type is not None and not isinstance(client, client_type):
            raise TypeError(f"Client {client_name} is not of type {client_type.__name__}")
        return client


    def get_activities(self) -> list:
        from temporalio import activity
        registry = {}

        # 1. HARVEST EXPLICIT OVERRIDES (Muscle)
        if hasattr(self.activities_instance, "get_muscle_registry"):
            muscle_map = self.activities_instance.get_muscle_registry()
            for act_name, method in muscle_map.items():
                # Soul Extraction (for metadata pinning)
                target = method.__func__ if hasattr(method, "__func__") else method

                if not hasattr(target, "__temporal_activity_definition"):
                    activity.defn(target, name=act_name)

                # Signature Promotion
                defn = getattr(target, "__temporal_activity_definition")
                target._defn = defn

                # 🟢 RETURN THE BODY: Keep it bound to the specialist instance
                registry[defn.name] = method
                logger.info(f"✅ [FUSED] Muscle capability: {act_name}")

        # 2. HARVEST KERNEL FALLBACKS (SDK Base)
        import inspect
        for _, method in inspect.getmembers(self, predicate=inspect.iscoroutinefunction):
            target = method.__func__ if hasattr(method, "__func__") else method
            defn = getattr(target, "__temporal_activity_definition", None)

            if defn and defn.name not in registry:
                # Signature Promotion
                target._defn = defn
                # 🟢 RETURN THE BODY: Keep it bound to 'self' (the SDK base)
                registry[defn.name] = method
                logger.info(f"🛡️ [KERNEL] Fallback active: {defn.name}")

        return list(registry.values())

    def _setup_routes(self):
        @self.router.post("/propose", summary="Sovereign Planning Handshake")
        async def propose(mission: AgentSubMission):
            activities = self.get_activities()
            try:
                # 🎯 Finding the Architect
                plan_activity = next(a for a in activities if a._defn.name == ActivityRoles.PROPOSAL)

                # Execute domain planning logic
                proposal: MacroPlan = await plan_activity(mission)

                return {
                    "plan": proposal.steps,
                    "rationale": proposal.reflection,
                    "confidence_score": proposal.confidence_score,
                    "session_id": mission.session_id,
                    "metadata": proposal.metadata
                }
            except StopIteration:
                raise HTTPException(status_code=501, detail=f"Agent {self.name} has no PROPOSAL capability.")

        @self.router.post("/execute", summary="Durable Mission Launch")
        async def execute(payload: Dict[str, Any]):
            if not self.temporal_client:
                raise HTTPException(status_code=500, detail="Temporal client not initialized")

            session_id = payload.get("session_id")
            # 🎯 DEFENSIVE CHECK: Ensure we actually have a plan to execute
            plan = payload.get("macro_plan") or payload.get("plan")

            if not session_id or not plan:
                logger.error(f"🛑 Execution denied: Missing session_id or plan in payload")
                raise HTTPException(status_code=400, detail="session_id and plan are required")

            # 🎯 UNIQUE ID: Using session_id ensures we don't duplicate missions
            workflow_id = f"mission-{session_id}-{uuid.uuid4().hex[:6]}"

            try:
                # 🚀 HANDOVER TO DHARMA
                await self.temporal_client.start_workflow(
                    "SpecialistMissionWorkflow",
                    args=[payload],  # 🎯 Matches 'async def run(self, payload: Dict)'
                    id=workflow_id,
                    task_queue=getattr(self.spec, "task_queue", settings.temporal_settings.task_queue)
                )
                return {
                    "status": "running",
                    "workflow_id": workflow_id,
                    "session_id": session_id
                }
            except Exception as e:
                logger.error(f"❌ Failed to start mission workflow: {str(e)}")
                raise HTTPException(status_code=500, detail="Workflow start failure")

    # ============================================================================
    # SOVEREIGN SPECIALIST ACTIVITY METHODS - Organized by ActivityRoles Sequence
    # ============================================================================
    @activity.defn(name=ActivityRoles.RECON)
    async def conduct_reconnaissance(self, request_input: Any) -> DiscoveryResponse:
        """🎯 SIGNATURE FIX: Accepts Any to handle list/dict variations."""
        raw_req = request_input[0] if isinstance(request_input, list) else request_input
        request = DiscoveryRequest.model_validate(raw_req)
        logger.info(f"📡 [RECON] Environment: {request.environment} | Target: {request.sub_objective}")
        start_time = activity.datetime.now()

        try:
            # 1. Access the Multi-Tiered Memory Manager
            context = await self.memory.get_reasoning_context(
                query=request.sub_objective,
                template_id=request.template_id,
                depth=request.depth_limit,
                tools=[]
            )

            # 2. Build the Standardized Response
            response = DiscoveryResponse(
                success=True,
                correlation_id=request.session_id,
                facts=context.get("facts", []),
                beliefs=context.get("beliefs", []),
                episodes=context.get("episodes", []),
                metadata=context.get("metadata", {}),
                telemetry={
                    "duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000,
                    "fact_count": len(context.get("facts", [])),
                    "belief_count": len(context.get("beliefs", [])),
                    "episode_count": len(context.get("episodes", []))
                }
            )

            logger.info(f"✅ [RECON] Discovery complete. Total Intelligence Items: {response.total_count}")
            return response

        except Exception as e:
            logger.error(f"📡 [RECON] Discovery failed: {str(e)}")
            return DiscoveryResponse(
                success=False,
                correlation_id=request.session_id,
                error_message=str(e),
                telemetry={"duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000}
            )

    @activity.defn(name=ActivityRoles.HISTORY)
    async def retrieve_intelligence_history(self, request: HistoryRequest) -> HistoryResponse:
        """
        SDK Default: Episodic Memory Retrieval.
        🎯 SIGNATURE: No more unfilled parameters.
        """
        logger.info(f"📚 [HISTORY] Querying past Leela for: {request.search_query}")
        start_time = activity.datetime.now()

        try:
            # 1. Fetch episodes (Assuming the manager returns objects with a 'similarity' field)
            hindsight = await self.memory.get_hindsight_segment(
                query=request.search_query,
                template_id=request.template_id,
            )

            # 2. CALCULATION: Fill 'avg_similarity_score'
            # Extract scores if they exist, otherwise default to 0.0
            scores = [float(h.get("similarity", 0.0)) for h in hindsight]
            avg_score = sum(scores) / len(scores) if scores else 0.0

            # 3. EXTRACTION: Pull Lessons
            lessons = [h.get("aha_moment") for h in hindsight if h.get("aha_moment")]

            response = HistoryResponse(
                success=True,
                correlation_id=request.session_id,
                episodes=hindsight,
                lessons_discovered=lessons,
                avg_similarity_score=round(avg_score, 4),  # 🎯 Filled
                error_message="None",  # 🎯 Explicitly unfilled
                telemetry={
                    "duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000,
                    "episode_count": len(hindsight)
                }
            )

            logger.info(f"✅ [HISTORY] Found {len(hindsight)} parallels. Avg Similarity: {avg_score:.2f}")
            return response

        except Exception as e:
            logger.error(f"📚 [HISTORY] Memory retrieval failed: {str(e)}")
            # 🎯 FILLING ERROR STATE
            return HistoryResponse(
                success=False,
                correlation_id=request.session_id,
                avg_similarity_score=0.0,
                error_message=f"Episodic Retrieval Error: {str(e)}",  # 🎯 Filled
                telemetry={"duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000}
            )

    @activity.defn(name=ActivityRoles.TACTICAL)
    async def analyze_tactical_context(self, bundle_input: Any) -> TacticalAuditReport:
        """
        SDK Default: Real-time Risk Assessment.
        🎯 SIGNATURE: Replaces 'Any' with 'TacticalBundle'.
        """
        raw = bundle_input[0] if isinstance(bundle_input, list) else bundle_input
        bundle = TacticalBundle.model_validate(raw)

        logger.info(f"🏛️ [TACTICAL] Auditing {len(bundle.proposed_plan.steps)} steps for {bundle.agent_name}")

        # 🟢 TEMPORAL BEST PRACTICE: Using activity.now() or datetime through Temporal
        start_time = activity.datetime.now()

        # 1. Hydrate the Audit Context
        audit_context = {
            "steps": bundle.proposed_plan.model_dump(),
            "facts": bundle.recon_intelligence.facts,
            "beliefs": bundle.recon_intelligence.beliefs,
            "past_lessons": bundle.history_intelligence.lessons_discovered
        }

        try:
            # 2. Invoke the Safety Officer (LLM)
            analysis = await self.llm.invoke_structured_model(
                user_input=f"Safety audit for mission: {bundle.proposed_plan.reflection}",
                system_prompt_template=TACTICAL_RISK_PROMPT,
                context=audit_context,
                response_model_name="RiskAnalysisReport"
            )

            # 3. Decision Logic
            decision = "PROCEED" if analysis.risk_score < bundle.risk_threshold else "HALT"

            response = TacticalAuditReport(
                success=True,
                correlation_id=bundle.session_id,
                decision=decision,
                risk_score=analysis.risk_score,
                justification=analysis.reasoning,
                suggested_modifications=getattr(analysis, "suggestions", []),
                error_message="None",  # 🎯 FIXED: Explicitly clear error state
                telemetry={
                    "duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000,
                    "audited_steps": len(bundle.proposed_plan.steps)
                }
            )

            logger.info(f"🏛️ [TACTICAL] Decision: {decision} (Risk: {analysis.risk_score})")
            return response

        except Exception as e:
            logger.error(f"🏛️ [TACTICAL] Audit failure: {str(e)}")
            # 🎯 FIXED: Populate error_message on failure
            return TacticalAuditReport(
                success=False,
                correlation_id=bundle.session_id,
                decision="HALT",
                risk_score=1.0,
                error_message=f"LLM_AUDIT_FAILURE: {str(e)}",
                justification="Audit system failure. Defensive HALT triggered to protect infrastructure.",
                telemetry={"duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000}
            )



    @activity.defn(name=ActivityRoles.PROPOSAL)
    async def formulate_mission_proposal(self, mission: AgentSubMission) -> MacroPlan:
        """
        SDK Default: Generates the plan.
        Note: This is usually called via /propose, but can be a durable activity.
        """
        logger.info(f"📋 [PROPOSAL] Formulating mission proposal for: {mission.sub_objective}")
        logger.info(f"📋 [PROPOSAL] Agent: {self.name} creating structured execution plan")
        
        try:
            # RECOMMENDED FIX
            plan = await self.llm.invoke_structured_model(
                system_prompt_template="You are the Architect. Generate a plan for: {goal}",
                context={"goal": mission.sub_objective},  # 🎯 Hydrate properly
                user_input=mission.sub_objective,
                response_model_name="MacroPlan"
            )
            logger.info(f"📋 [PROPOSAL] Generated plan with {len(plan.steps)} steps")
            logger.info(f"📋 [PROPOSAL] Plan confidence: {plan.confidence_score:.2f}")
            return plan
        except Exception as e:
            logger.error(f"📋 [PROPOSAL] Failed to generate mission proposal: {str(e)}")
            raise

    @activity.defn(name=ActivityRoles.INTERVENTION)
    async def execute_direct_intervention(self, step_input: Any) -> ActionOutcome:
        """
        🎯 DHARMA FIX: Universal Step Receiver.
        Handles single ActionStep, raw Dict, or List of inputs from Sutram.
        """
        logger.info(f"⚡ [INTERVENTION] Raw Input Type: {type(step_input)}")
        start_time = activity.datetime.now()

        try:
            # 1. NORMALIZATION: Extract the target if it arrived in a list
            if isinstance(step_input, list):
                logger.info(f"⚡ Batch of {len(step_input)} steps detected. Extracting primary.")
                raw_data = step_input[0] if step_input else {}
            else:
                raw_data = step_input

            # 2. VALIDATION: Manually hydrate the model to satisfy Pydantic
            # This bypasses Temporal's strict auto-decoding
            if not isinstance(raw_data, ActionStep):
                step = ActionStep.model_validate(raw_data)
            else:
                step = raw_data

            # 3. EXECUTION: Pass the valid object to your Muscle (StubMuscle)
            muscle_result = await self.activities_instance.execute_direct_intervention(step)

            # 4. WRAP: Build the standard Outcome object
            return ActionOutcome(
                success=True,
                correlation_id=step.session_id,
                status=muscle_result.get("status", "SUCCESS"),
                observation=muscle_result.get("observation", "Executed."),
                raw_result=muscle_result.get("data", {}),
                telemetry={
                    "duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000,
                    "tool_used": step.action_name
                }
            )

        except Exception as e:
            logger.error(f"❌ [INTERVENTION] Handshake crash: {str(e)}")
            # Return a valid failure object so the workflow can handle the error gracefully
            return ActionOutcome(
                success=False,
                error_message=f"Handshake failed: {str(e)}",
                status="FAILED"
            )

    @activity.defn(name=ActivityRoles.ATTAINMENT)
    async def verify_objective_attainment(self, check: AttainmentCheck) -> AttainmentReport:
        """
        SDK Default: Objective Attainment Inspector.
        🎯 SIGNATURE: Uses the ActionOutcome metrics/analysis to verify truth.
        """
        logger.info(f"🧐 [ATTAINMENT] Inspecting {check.step_id} (Mode: {check.verification_mode})")
        start_time = activity.datetime.now()

        try:
            # 1. Check for Muscle Implementation
            if hasattr(self.activities_instance, "verify_objective_attainment"):
                attained = await self.activities_instance.verify_objective_attainment(check)
            else:
                # 2. SDK Fallback: Use the metrics/analysis we just built!
                # If anomaly_detected is True, we fail attainment by default.
                is_anomaly = check.action_outcome.analysis.get("anomaly_detected", False)
                attained = check.action_outcome.success and not is_anomaly

            return AttainmentReport(
                success=True,
                correlation_id=check.session_id,
                attained=attained,
                certainty_score=0.9 if attained else 0.1,
                error_message="None",
                telemetry={"duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000}
            )

        except Exception as e:
            logger.error(f"❌ [ATTAINMENT] Inspection failure: {str(e)}")
            return AttainmentReport(
                success=False,
                correlation_id=check.session_id,
                attained=False,
                discrepancy_found=f"EXCEPTION: {str(e)}",  # 🎯 Fixed from bool to str
                error_message=str(e)
            )

    @activity.defn(name=ActivityRoles.DEBRIEF)
    async def summarize_intelligence_debrief(self, brief_input: Any) -> IntelligenceReport:
        """🎯 DHARMA FIX: Resilient Debrief (Empty-Safe)."""


        start_time = activity.datetime.now()

        try:
            # 1. Aggregation: Sum up the metrics from all steps
            if isinstance(brief_input, list):
                if not brief_input:
                    # 🎯 Handle empty case gracefully
                    logger.warning("📝 Debrief received empty step results. Generating null summary.")
                    return IntelligenceReport(
                        success=True,
                        correlation_id="test-session-123",
                        narrative_summary="No tactical steps were executed to summarize.",
                        final_status="SKIPPED"
                    )
                brief = brief_input[0]
            else:
                brief = brief_input

            logger.info(f"📝 [DEBRIEF] Synthesizing report for: {brief['original_objective']}")

            total_metrics = {}
            for outcome_dict in brief['step_results']:
                # Convert dict back to ActionOutcome object for easier handling
                outcome = ActionOutcome(**outcome_dict)
                for k, v in outcome.metrics.items():
                    total_metrics[k] = total_metrics.get(k, 0.0) + v

            # 2. Narrative Generation: Use the specialized Debrief Prompt
            # This uses the LLM to 'read' the outcomes and explain them
            analysis = await self.llm.invoke_unstructured_model(
                user_input=f"Analyze mission results for: {brief['original_objective']}",
                system_prompt=self._get_debrief_prompt_template(),
                context={
                    "objective": brief['original_objective'],
                    "outcomes": brief['step_results']  # Already dicts from model_dump()
                }
            )

            return IntelligenceReport(
                success=True,
                correlation_id=brief['session_id'],
                narrative_summary=analysis,
                key_takeaways=self._extract_takeaways(analysis),
                final_status="PARTIAL" if brief['is_partial_success'] else "SUCCESS",
                impact_metrics=total_metrics,
                error_message="None",
                telemetry={"duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000}
            )

        except Exception as e:
            logger.error(f"❌ [DEBRIEF] Synthesis failed: {str(e)}")
            return IntelligenceReport(
                success=False,
                correlation_id=brief['session_id'],
                narrative_summary="Technical failure during report generation.",
                error_message=str(e)
            )

    @activity.defn(name=ActivityRoles.AAR)
    async def commit_mission_after_action_report(self, report_input: Any) -> LearningAnchor:
        """
        🎯 DHARMA FIX: Resilient Wisdom Anchoring.
        Handles lists of outcomes by synthesizing a report on-the-fly.
        """
        logger.info(f"🗃️ [AAR] Input Type: {type(report_input)}")

        try:
            # 1. NORMALIZATION: Handle List vs Dict
            if isinstance(report_input, list):
                logger.info(f"📝 Synthesizing AAR from {len(report_input)} step results.")
                # Manufacture a valid report dictionary from the list
                raw_report = {
                    "mission_id": str(uuid.uuid4()),
                    "session_id": getattr(self, "current_session_id", "test-session"),
                    "template_id": "SYNT-001",
                    "agent_name": self.name,
                    "summary_brief": f"Mission completed with {len(report_input)} tactical steps.",
                    "execution_data": report_input,  # The list lands here
                    "success_score": 1.0,
                    "aha_moment": "Automated synthesis of batch execution results."
                }
            else:
                raw_report = report_input

            # 2. VALIDATION: Now Pydantic will be happy
            report = AfterActionReport.model_validate(raw_report)

            # 3. ANCHORING: Commit to VectorDB
            doc_id = f"aar-{report.mission_id}"
            await self.vector_client.upsert_atomic(
                collection="episodes",
                doc_id=doc_id,
                text=report.summary_brief,
                metadata={
                    "agent": self.name,
                    "success_score": report.success_score,
                    "template_id": report.template_id
                }
            )

            return LearningAnchor(
                success=True,
                correlation_id=report.session_id,
                memory_id=doc_id
            )

        except Exception as e:
            logger.error(f"❌ [AAR] Failure: {str(e)}")
            return LearningAnchor(
                success=False,
                correlation_id="ERROR",
                memory_id="FAILED",
                error_message=str(e)
            )

    @activity.defn(name=ActivityRoles.COMPLETION)
    async def transmit_mission_completion(self, manifest_input: Any) -> CallbackAck:
        """
        🎯 FINAL DHARMA FIX: Resilient Manifest Handshake.
        """
        logger.info(f"📡 [COMPLETION] Input Type: {type(manifest_input)}")
        start_time = activity.datetime.now() if not hasattr(activity, "datetime") else activity.datetime

        try:
            # 1. NORMALIZATION: Extract from list if necessary
            # Normalize list -> dict
            raw_manifest = manifest_input[0] if isinstance(manifest_input, list) else manifest_input

            # Manually Validate
            manifest = MissionManifest.model_validate(raw_manifest)

            # 3. PAYLOAD CONSTRUCTION
            payload = {
                "agent": self.name,
                "mission_id": manifest.mission_id,
                "report": manifest.final_report,
                "status": manifest.mission_status,
                "trace_id": manifest.trace_id,
                "completed_at": start_time.isoformat()
            }

            async with AsyncClient() as client:
                logger.info(f"📡 [COMPLETION] Calling Sutram at: {manifest.callback_url}")
                response = await client.post(manifest.callback_url, json=payload, timeout=30.0)

                success = response.is_success
                return CallbackAck(
                    success=success,
                    correlation_id=manifest.session_id,
                    orchestrator_received=success,
                    error_message="None" if success else f"HTTP_{response.status_code}"
                )

        except Exception as e:
            logger.error(f"❌ [COMPLETION] Failure: {str(e)}")
            return CallbackAck(success=False, error_message=str(e))

    @activity.defn(name=ActivityRoles.SUPPORT)
    async def recruit_specialist_support(self, request: SupportRequest) -> PeerSupportOutcome:
        """
        SDK Default: Peer Collaboration Handshake.
        🎯 SIGNATURE: Replaces Dict with 'SupportRequest' and 'PeerSupportOutcome'.
        """
        logger.info(f"🤝 [SUPPORT] Recruiting {request.target_specialty} for: {request.objective[:50]}...")
        start_time = activity.datetime.now()

        try:
            # 1. Access the A2A (Agent-to-Agent) Client
            # The A2A client handles the Consul discovery and NATS/HTTP routing
            result = await self.a2a.recruit_ranger(
                specialty=request.target_specialty,
                objective=request.objective,
                priority=request.priority,
                context=request.shared_context
            )

            return PeerSupportOutcome(
                success=True,
                correlation_id=request.session_id,
                peer_name=result.get("agent_name", "unknown_ranger"),
                mission_id=result.get("mission_id", "pending"),
                recruitment_status=result.get("status", "ACCEPTED"),
                peer_metadata=result.get("metadata", {}),
                error_message="None",
                telemetry={"duration_ms": (activity.datetime.now() - start_time).total_seconds() * 1000}
            )

        except Exception as e:
            logger.error(f"❌ [SUPPORT] Recruitment failed: {str(e)}")
            return PeerSupportOutcome(
                success=False,
                correlation_id=request.session_id,
                peer_name="None",
                mission_id="None",
                recruitment_status="FAILED",
                error_message=str(e)
            )


    async def _run_result_analytics(self, raw_output: Dict[str, Any]) -> Dict[str, float]:
        """
        Placeholder: Extract quantitative metrics from tool output.
        Hook for: Time-series ingestion, latency tracking, cost calculation.
        """
        # 🎯 Dummy Logic: In the future, this calls your TimeSeries service
        metrics = {
            "processing_time_ms": raw_output.get("latency", 0.0),
            "payload_size_kb": float(len(str(raw_output)) / 1024),
            "confidence_index": raw_output.get("confidence", 1.0)
        }

        # If the tool returned specific numeric data (e.g., price), promote it to metrics
        if "price" in raw_output:
            metrics["extracted_value"] = float(raw_output["price"])

        return metrics

    async def _check_anomaly_signatures(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Placeholder: Qualitative risk/anomaly analysis.
        Hook for: Outlier detection, pattern matching, safety violations.
        """
        # 🎯 Dummy Logic: Hook for your Risk Analytics engine
        analysis = {
            "anomaly_detected": False,
            "risk_tier": "LOW",
            "pattern_match": "STANDARD_EXECUTION"
        }

        # Simple heuristic: If the tool output is empty, it's an anomaly
        if not raw_output or (isinstance(raw_output, dict) and not raw_output.get("data")):
            analysis["anomaly_detected"] = True
            analysis["risk_tier"] = "MEDIUM"
            analysis["pattern_match"] = "NULL_RESPONSE_PATTERN"

        return analysis

    # guardianhub_sdk/agents/specialist_base.py

    def _get_debrief_prompt_template(self) -> str:
        """
        The personas and structure for the Rama (Debrief) phase.
        Ensures the LLM acts as a synthesizer, not just a logger.
        """
        return """
        Role: Sovereign Mission Scribe (Rama Persona)
        Objective: Synthesize the execution results of a mission into a strategic debrief.

        MISSION CONTEXT:
        - Goal: {objective}
        - Steps Taken: {outcomes}

        INSTRUCTIONS:
        1. Summarize the narrative: What was the 'Hero's Journey' of this mission?
        2. Identify Friction: Where did the reality differ from the plan?
        3. Highlight the 'Aha!': What did we learn that we didn't know during RECON?
        4. Verdict: Is the goal attained?

        OUTPUT FORMAT:
        Narrative summary first, followed by a 'TAKEAWAYS:' section with bullet points.
        """

    def _extract_takeaways(self, narrative: str) -> List[str]:
        """
        Heuristic to extract bullet points from the LLM narrative.
        This provides 'Quick Glance' intelligence for the Orchestrator.
        """
        takeaways = []
        try:
            # Look for common list markers after the 'TAKEAWAYS' header
            lines = narrative.split('\n')
            capture = False
            for line in lines:
                if "TAKEAWAYS" in line.upper():
                    capture = True
                    continue
                if capture and (line.strip().startswith(('-', '*', '•')) or (line.strip() and line[0].isdigit())):
                    # Clean the line of markers
                    clean_line = line.strip().lstrip('-*•0123456789. ').strip()
                    if clean_line:
                        takeaways.append(clean_line)

            # Fallback: If no markers found, take the first 3 meaningful sentences
            if not takeaways:
                sentences = narrative.split('.')
                takeaways = [s.strip() for s in sentences if len(s.strip()) > 20][:3]

        except Exception as e:
            logger.warning(f"⚠️ [DEBRIEF] Takeaway extraction failed: {str(e)}")
            takeaways = ["Manual review required for takeaways."]

        return takeaways

    # guardianhub_sdk/agents/specialist_base.py

    def _infer_aha_moment(self, narrative: str, data: List[Dict]) -> str:
        """
        Heuristic/LLM logic to distill a single 'Rule' from the mission.
        """
        # 🎯 Dummy Logic: In production, this would be a quick 1-shot LLM call
        # to summarize the 'Lesson' into a single sentence for Graph/Vector indexing.
        if "timeout" in narrative.lower():
            return "Observed network latency; recommend increasing retry backoff for this environment."

        failed_steps = [d for d in data if d.get("status") == "FAILED"]
        if failed_steps:
            return f"Mission friction encountered at step {failed_steps[0].get('step_id')}. Check tool dependencies."

        return "Standard execution successful. No anomalous patterns observed."
from datetime import timedelta
from typing import Dict, Any
from temporalio import workflow

# Contract Imports
from guardianhub.models.agent.contracts.discovery import DiscoveryRequest , DiscoveryResponse
from guardianhub.models.agent.contracts.history import HistoryRequest,HistoryResponse
from guardianhub.models.agent.contracts.tactical import TacticalBundle,TacticalAuditReport
from guardianhub.models.agent.contracts.action import ActionStep,ActionOutcome
from guardianhub.models.agent.contracts.attainment import AttainmentCheck,AttainmentReport
from guardianhub.models.agent.contracts.debrief import SummaryBrief,IntelligenceReport
from guardianhub.models.agent.contracts.learning import AfterActionReport,LearningAnchor
from guardianhub.models.agent.contracts.completion import MissionManifest,CallbackAck

from .agent_contract import ActivityRoles
from .constants import get_activity_options
from guardianhub.config.settings import settings
from ...models.template.agent_plan import MacroPlan

logger = workflow.logger

@workflow.defn(name="SpecialistMissionWorkflow")
class SpecialistMissionWorkflow:
    @workflow.run
    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        mapping = settings.workflow_settings.activity_mapping
        data = payload[0] if isinstance(payload, list) and payload else payload

        # 2. Extract the plan data
        raw_plan = data.get("macro_plan") or data.get("plan")

        # 🎯 THE FIX: If raw_plan is just the steps list, wrap it!
        if isinstance(raw_plan, list):
            logger.info("📦 Wrapping raw steps list into MacroPlan object")
            final_plan = {
                "steps": raw_plan,
                "reflection": data.get("rationale", "Synthesized from orchestrator"),
                "confidence_score": data.get("confidence_score", 1.0)
            }
        else:
            final_plan = raw_plan


        # 1. INITIALIZATION: Context Extraction
        trace_id = payload.get("trace_id")
        session_id = payload.get("session_id")
        agent_name = payload.get("agent_name", "specialist")
        template_id = payload.get("template_id", "TPL-GENERIC")
        sub_objective = payload.get("sub_objective")
        is_dry_run = payload.get("is_dry_run", False)
        depth_limit = payload.get("depth_limit", 5)

        # 2. RECONNAISSANCE: The Eyes (Avatar: Kurma)
        recon_request = DiscoveryRequest(
            session_id=session_id, trace_id=trace_id, template_id=template_id,
            agent_name=agent_name, sub_objective=sub_objective,
            environment=payload.get("environment", "production"),
            depth_limit=depth_limit
        )
        intelligence: DiscoveryResponse = await workflow.execute_activity(
            mapping[ActivityRoles.RECON], arg=recon_request, **get_activity_options(ActivityRoles.RECON)
        )

        # 3. HISTORY: The Leela (Avatar: Varaha)
        # We pull these from the payload so the Orchestrator can tune the "Wisdom Filter"
        history_limit = payload.get("history_limit", 5)
        min_success = payload.get("min_success_score", 0.7)  # 🎯 Defaulting to high-quality only

        history_request = HistoryRequest(
            session_id=session_id,
            trace_id=trace_id,
            template_id=template_id,
            agent_name=agent_name,
            search_query=sub_objective,
            limit=history_limit,
            min_success_score=min_success  # 🎯 FIXED: No more learning from failures
        )

        past_lessons: HistoryResponse = await workflow.execute_activity(
            mapping[ActivityRoles.HISTORY],
            arg=history_request,
            **get_activity_options(ActivityRoles.HISTORY)
        )

        # 4. TACTICAL AUDIT: The Safety Gate (Avatar: Narasimha)
        # Extract the risk appetite from the payload
        risk_threshold = payload.get("risk_threshold", 0.7)  # 🎯 Defaulting to a balanced stance

        validated_plan = MacroPlan.model_validate(final_plan)
        tactical_bundle = TacticalBundle(
            session_id=session_id,
            trace_id=trace_id,
            template_id=template_id,
            agent_name=agent_name,
            proposed_plan=validated_plan,
            recon_intelligence=intelligence,
            history_intelligence=past_lessons,
            risk_threshold=risk_threshold,  # 🎯 FIXED: Threshold is now mission-aware
            is_dry_run=is_dry_run
        )

        audit: TacticalAuditReport = await workflow.execute_activity(
            mapping[ActivityRoles.TACTICAL],
            arg=tactical_bundle,
            **get_activity_options(ActivityRoles.TACTICAL)
        )

        audit_decision = audit.decision if hasattr(audit, "decision") else audit.get("decision")
        if audit_decision == "HALT":
            # Use get() pattern for the message as well
            reason = audit.justification if hasattr(audit, "justification") else audit.get("justification",
                                                                                           "No reason provided")
            workflow.logger.warning(f"🛑 Mission Halted: {reason}")
            return {"status": "HALTED", "reason": reason}

        # 5. ITERATIVE INTERVENTION: The Hands (Avatars: Vamana, Parashurama)
        execution_results = []
        for step in payload.get("plan", {}).get("steps", []):
            action = ActionStep(
                session_id=session_id, trace_id=trace_id, template_id=template_id,
                agent_name=agent_name, action_name=step.get("tool_name"),
                action_input=step.get("tool_args"), step_id=step.get("step_id"),
                is_dry_run=is_dry_run
            )
            outcome: ActionOutcome = await workflow.execute_activity(
                mapping[ActivityRoles.INTERVENTION], arg=action, **get_activity_options(ActivityRoles.INTERVENTION)
            )

            check = AttainmentCheck(
                session_id=session_id, trace_id=trace_id, template_id=template_id,
                agent_name=agent_name, step_id=step.get("step_id"),
                verification_mode=step.get("verification_mode",None),
                action_name=step.get("tool_name"), action_outcome=outcome # 🎯 Passes full Outcome
            )
            report: AttainmentReport = await workflow.execute_activity(
                mapping[ActivityRoles.ATTAINMENT], arg=check, **get_activity_options(ActivityRoles.ATTAINMENT)
            )

            execution_results.append(report)

        # 🎯 These are now FUNCTIONAL parameters
        # 6. DEBRIEF: Narrative Synthesis (Avatar: Rama)
        total_steps = len(execution_results)
        success_count = sum(1 for r in execution_results if r.attained)
        any_step_failed = success_count < total_steps

        # 6. DEBRIEF
        debrief_brief = SummaryBrief(
            session_id=session_id,
            trace_id=trace_id,
            template_id=template_id,
            agent_name=agent_name,
            # 🎯 Ensure these are dicts, not objects
            step_results=[r.model_dump() for r in execution_results],
            original_objective=sub_objective,
            is_partial_success=any_step_failed,
            total_steps=total_steps,
            success_count=success_count
        )
        
        # 🎯 DEBUG: Log the debrief_brief object
        logger.info(f"🎯 [DEBRIEF] Created SummaryBrief: {type(debrief_brief)} - {debrief_brief}")

        final_report: IntelligenceReport = await workflow.execute_activity(
            mapping[ActivityRoles.DEBRIEF],
            args=[debrief_brief.model_dump()],
            **get_activity_options(ActivityRoles.DEBRIEF)
        )

        # 7. AAR: Learning Commitment (Avatar: Krishna)
        # 🎯 THE RESILIENT ACCESS FIX
        # Check if the report is an object with the attribute, otherwise use get()
        # In mission_skeleton.py around line 183
        # 🎯 THE FIX: Handle both Object and Dict formats
        def get_val(obj, key, default=None):
            if hasattr(obj, key):
                return getattr(obj, key)
            if isinstance(obj, dict):
                return obj.get(key, default)
            return default

        # Use the helper to extract values safely
        summary_text = get_val(final_report, "narrative_summary", "No summary available.")
        takeaways_list = get_val(final_report, "key_takeaways", [])

        flattened_aha = " | ".join(takeaways_list) if takeaways_list else "Mission completed with standard results."
        # Now use them in your final call
        aar_request = AfterActionReport(
            session_id=session_id,
            trace_id=trace_id,
            template_id=template_id,
            agent_name=agent_name,
            mission_id=session_id,
            summary_brief=summary_text,
            aha_moment=flattened_aha,  # 🎯 Now populated with synthesized wisdom
            execution_data=[r.model_dump() for r in execution_results],
            success_score=1.0 if all(r.attained for r in execution_results) else 0.5
        )
        # 🎯 FIXED: Returning the Sovereign LearningAnchor
        anchor: LearningAnchor = await workflow.execute_activity(
            mapping[ActivityRoles.AAR],
            args=[aar_request.model_dump()],
            **get_activity_options(ActivityRoles.AAR)
        )
        # In mission_skeleton.py around line 205
        # 🎯 THE FINAL LOGGING FIX
        if anchor:
            # Use .get() because Temporal serialized the object to a dict
            memory_id = anchor.memory_id if hasattr(anchor, 'memory_id') else anchor.get('memory_id', 'unknown')
            workflow.logger.info(f"🗃️ [AAR] Wisdom anchored at: {memory_id}")



        # 🎯 FUNCTIONAL USAGE:
        # We pass the memory_id back to Sutram.
        # This allows Sutram to 'pin' this specific lesson to the user's project graph.
        anchored_wisdom_id = memory_id if anchor.success else None

        # 8. COMPLETION: The Callback (Avatar: Buddha)

        # 🎯 DERIVE FINAL STATUS:
        # Based on our attainment checks, we determine the high-level signal.
        if all(r.attained for r in execution_results):
            final_status = "COMPLETED"
        elif any(r.attained for r in execution_results):
            final_status = "PARTIAL"
        else:
            final_status = "FAILED"

        manifest = MissionManifest(
            session_id=session_id,
            trace_id=trace_id,
            template_id=template_id,  # 🎯 Ensuring trace_id consistency
            agent_name=agent_name,
            mission_id=session_id,
            final_report={
                **final_report.model_dump(),
                "anchored_wisdom_id": anchored_wisdom_id,  # 🎯 Linking the memory
                "success_score": aar_request.success_score  # 🎯 Standardizing the rating
            },
            # 🎯 FIXED: Signaling the exact state to the Orchestrator
            mission_status=final_status,
            callback_url=payload.get("callback_url", settings.endpoints.SUTRAM_CALLBACK_URL)
        )

        # 8. COMPLETION: The Callback (Avatar: Buddha)
        ack: CallbackAck = await workflow.execute_activity(
            mapping[ActivityRoles.COMPLETION],
            arg=manifest,
            **get_activity_options(ActivityRoles.COMPLETION)
        )

        # 🎯 FUNCTIONAL USAGE: Recursive Continuity

        if not ack.orchestrator_received:
            workflow.logger.error(f"❌ [COMPLETION] Sutram failed to acknowledge: {ack.error_message}")


        # We extract the token. If it exists, it means Sutram has a 'Follow-up' ready.
        continuation_token = ack.next_mission_token if ack.success else None

        return {
            "status": final_status,
            "mission_id": session_id,
            "anchored_wisdom_id": anchored_wisdom_id,
            # 🎯 The Handover: Passing the baton to the next mission or the UI
            "next_steps_token": continuation_token,
            "report": final_report.narrative_summary
        }
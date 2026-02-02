This is the definitive **Sovereign Specialist Manifest**. It is designed so that a developer with nothing but the SDK source code and this README can go from "Zero" to "Attested Agent" in a single session.

---

# 🛸 GuardianHub SDK: The Sovereign Agent Engine

### *The Ultimate Technical Guide for Agent Engineering*

The GuardianHub SDK is a distributed framework that transforms domain-specific logic into **Sovereign Specialist Agents**. It provides the durable "Bone" (Temporal/API/Protocol) so you can focus on the "Muscle" (Infrastructure logic).

---

## 📜 The 10 Commandments (Activity Roles)

Every Specialist Agent is governed by these 10 roles. They form the **Sovereign Execution Contract**.

### 1. `RECON` (conduct_reconnaissance)

* **The Mission:** Eradicate the "Fog of War." Re-verify ground truth before acting.
* **Implementation:** Overriding this is **Mandatory**. Use `self.graph_client` to query your domain’s Digital Twin (Neo4j).
* **Gotcha:** Never trust the mission plan's assumptions. If the plan says "Server A," your Recon must confirm "Server A" exists and identify its dependencies.
* **Return:** A `List[Dict]` of validated facts.

### 2. `HISTORY` (retrieve_intelligence_history)

* **The Mission:** Gain "Hindsight." Look at past After-Action Reports (AARs) to avoid repeating mistakes.
* **Implementation:** SDK Fallback is usually sufficient. It uses `self.vector_client` to RAG-search the `episodes` collection.
* **Return:** Narratives of past success/failure in similar contexts.

### 3. `TACTICAL` (analyze_tactical_context)

* **The Mission:** The "Safety Officer." This is the circuit breaker between Recon and Action.
* **Implementation:** SDK Fallback uses LLM-driven risk scoring. Override this if you have **Hard Security Policies** (e.g., "Halt if the target CI is tagged #PRODUCTION").
* **Expectation:** Returns a `risk_score` (0.0-1.0). If > 0.8, the SDK triggers a `Workflow Interruption`.

### 4. `PROPOSAL` (formulate_mission_proposal)

* **The Mission:** The "Architect." Translates the high-level objective into actionable steps.
* **Implementation:** Handled via the `/propose` endpoint. It uses `MemoryManager` to fuse Hindsight and Recon into a `MacroPlan`.
* **Return:** A structured list of tool calls and their intended outcomes.

### 5. `INTERVENTION` (execute_direct_intervention)

* **The Mission:** The "Hands." This is where the world changes (AWS, K8s, ServiceNow).
* **Implementation:** **Mandatory Specialist Override**. This should be atomic and idempotent.
* **The Trick:** Use `self.get_client("custom_client")` if you need specialized domain libraries.

### 6. `ATTAINMENT` (verify_objective_attainment)

* **The Mission:** The "Validator." Prove the intervention actually worked.
* **Implementation:** **High Priority Override**. Re-query the infrastructure. If you changed a status to `STABLE`, confirm it is now `STABLE`.
* **Gotcha:** Do not just rely on the return code of the Intervention; perform a fresh sensory check.

### 7. `DEBRIEF` (summarize_intelligence_debrief)

* **The Mission:** The "Narrator." Distill raw activity logs into a human-readable intelligence report.
* **Implementation:** SDK Fallback uses LLM synthesis. Override if you need to output specific compliance JSON (e.g., NIST/SOC2 audit logs).

### 8. `AAR` (commit_mission_after_action_report)

* **The Mission:** The "Legacy." Commit the mission's outcome to long-term memory.
* **Implementation:** SDK Fallback uses `self.vector_client` to store a structured episode.
* **Return:** A unique `episode_id` for future `HISTORY` lookups.

### 9. `COMPLETION` (transmit_mission_completion)

* **The Mission:** The "Radio." Close the loop with the Sutram Orchestrator.
* **Implementation:** SDK Fallback uses Consul to find the Orchestrator's callback URL and POSTs the final debrief.

### 10. `SUPPORT` (recruit_specialist_support)

* **The Mission:** The "Diplomat." Peer-to-peer delegation.
* **Implementation:** Uses `self.a2a_client` to find a "Ranger" (another specialist) to handle a sub-objective you aren't equipped for.

---

## 🏗️ Technical Architecture: Bone & Muscle

### 🧪 The Discovery Handshake (Attestation)

The SDK uses **Late-Binding Structural Attestation**. When you pass your `activities_instance` to the `SovereignSpecialistBase`, the Kernel:

1. **Soul Extraction:** Reaches through Python’s read-only method proxies to the underlying `__func__`.
2. **Signature Promotion:** Explicitly pins `__temporal_activity_definition` and `_defn` to the function object.
3. **Gap Filling:** Symmetrically scans the SDK Base for missing roles and injects fallbacks.

```python
# THE DEVELOPER CONTRACT
class CMDBMuscle:
    def get_muscle_registry(self) -> dict:
        return {
            ActivityRoles.RECON: self.my_neo4j_query,       # OVERRIDE
            ActivityRoles.INTERVENTION: self.patch_cloud,  # OVERRIDE
            "custom_audit_tool": self.run_compliance       # EXTENSION
        }

```

---

## 🛠️ The Integrated Client Suite

Your agent (via `self`) has direct access to the Sovereign ecosystem:

* `self.graph_client`: Neo4j/Cypher for Topologies.
* `self.vector_client`: Qdrant/Milvus for Long-term Memory.
* `self.llm`: Structured reasoning and planning.
* `self.consul_client`: Dynamic service discovery.
* `self.a2a`: Secure peer-to-peer agent messaging.

---

## 🚦 The Mission Lifecycle

1. **PROPOSE:** `/v1/mission/propose` generates a `MacroPlan`.
2. **EXECUTE:** `/v1/mission/execute` launches a Temporal Workflow.
3. **LOOP:** Workflow iterates through: `RECON` -> `TACTICAL` -> `INTERVENTION` -> `ATTAINMENT`.
4. **SEAL:** `AAR` is written; `COMPLETION` is transmitted.

---
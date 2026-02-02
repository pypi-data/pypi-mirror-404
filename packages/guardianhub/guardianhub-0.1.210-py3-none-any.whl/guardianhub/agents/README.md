
---

# 🛸 GuardianHub SDK: The Sovereign Agent Engine

The GuardianHub SDK is a distributed framework designed to build **Sovereign Specialist Agents**. It provides the durable "Muscle" and cognitive "Brain" required for agents to perform complex, multi-step infrastructure audits and self-healing missions.

## (Core) Philosophy

* **Decoupled Intelligence:** The "General" (Orchestrator) manages strategy; "Colonels" (Specialists) own the domain expertise.
* **Durable by Default:** All agent missions are backed by Temporal workflows, ensuring resilience against network partitions and service restarts.
* **Registry-Driven:** Zero-code activity mapping via JSON configurations.
* **Memory-First:** Integrated Facts (Graph), Beliefs (Vector), and Episodes (Narrative) management.

---

## 🏛️ System Architecture

### 1. The Handshake (Propose)

Sutram (General) sends a mission brief to a Specialist. The Specialist clears the **Fog of War** using its local domain schema and returns a **MacroPlan**.

### 2. The Muscle (Execute)

Once approved, the Specialist triggers a durable **SovereignMissionWorkflow**. This workflow handles:

* **Sensory Injection:** Re-fetching ground truth before action.
* **ReAct Loop:** Executing tool calls with dynamic timeouts and retries.
* **A2A Exploration:** Peer-to-peer "Ranger" recruitment for missing data.

### 3. The Callback (Synthesis)

Upon completion, the agent synthesizes raw data into an Intelligence Report and notifies the Orchestrator via a standardized callback.

---

## 🛠️ Configuration-as-Logic

The SDK is driven by a `config.json` that defines the agent's operating parameters:

```json
{
  "specialist_settings": {
    "agent_name": "cmdb-specialist",
    "hop_limit": 3
  },
  "workflow_settings": {
    "activity_mapping": {
      "invoke_semantic_tool_activity": "run_servicenow_audit"
    },
    "long_activities": ["run_servicenow_audit"]
  }
}

```

---

## 🚀 Getting Started for Developers

1. **Install the SDK:** `pip install guardianhub[muscle]`
2. **Define Activities:** Create a class implementing the tools mapped in your JSON.
3. **Initialize the Colonel:** Pass your activities and clients to `SovereignSpecialistBase`.
4. **Ignite:** Use the `MuscleFactory` to start your Temporal worker and mount the router to your FastAPI app.

---

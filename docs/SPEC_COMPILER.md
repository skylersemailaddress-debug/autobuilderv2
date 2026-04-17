# Spec Compiler

AutobuilderV2 transforms declarative YAML spec files into a validated, executable build plan via a multi-stage compiler pipeline.

---

## Pipeline Stages

```
spec files (YAML)
      │
      ▼
  SpecLoader            — validates required files, normalises keys
      │
      ▼
  IR Compiler           — emits AppIR (intermediate representation)
      │
      ▼
  Generator             — produces template pack + validation plan
      │
      ▼
  Executor              — runs build against the plan
      │
      ▼
  Proof Stage           — certifies build output (platform hardening, governance)
```

---

## Spec Bundle Format

A spec bundle is a directory (or explicit set of files) containing:

| File | Required | Description |
|------|----------|-------------|
| `mission.yml` | Yes | Top-level product intent |
| `stack.yml` | Yes | Technology stack declaration |
| `features.yml` | Yes | Feature list with tier annotations |
| `constraints.yml` | No | Constraint overrides (latency, security, i18n) |
| `assets.yml` | No | Asset catalogues (images, sounds, data) |
| `navigation.yml` | No | Screen/route graph for UI apps |
| `state_machines.yml` | No | State machine definitions for reactive apps |

### `mission.yml` required keys

```yaml
app_name: <string>
app_type: <archetype_id>
```

### `stack.yml` required keys

```yaml
stack_id: <string>
```

### `features.yml` required keys

```yaml
features:
  - name: <string>
    tier: <first_class|bounded_prototype|structural_only|future>
```

Feature tiers determine build behaviour:

| Tier | Build behaviour |
|------|----------------|
| `first_class` | Fully implemented, tested, verified |
| `bounded_prototype` | Implemented with scope boundaries declared |
| `structural_only` | Scaffold only — no runtime logic |
| `future` | Excluded from build; recorded in proof as deferred |

---

## IR Contract

The compiler produces an `AppIR` object:

```python
@dataclass
class AppIR:
    app_name: str
    app_type: str
    stack_id: str
    features: list[dict]
    constraints: dict
    # optional extended fields (populated when spec files present)
    application_domains: list[str]
    assets: list[dict]
    runtime_targets: list[str]
    navigation_flows: list[dict]
    state_machines: list[dict]
```

---

## Support Matrix

### Archetype Lanes

| Lane ID | Description | Tier |
|---------|-------------|------|
| `first_class_commercial` | SaaS/e-commerce production apps | first_class |
| `first_class_mobile` | Cross-platform mobile (Flutter) | first_class |
| `first_class_game` | 2-D/3-D game projects (Godot) | first_class |
| `first_class_realtime` | Streaming / low-latency systems | first_class |
| `first_class_enterprise_agent` | Multi-agent enterprise orchestration | first_class |

### Supported Stacks

| Stack ID | Lane | Status |
|----------|------|--------|
| `react_stripe_firebase` | commercial | first_class |
| `nextjs_postgres` | commercial | first_class |
| `flutter_mobile` | mobile | first_class |
| `godot_game` | game | first_class |
| `kafka_flink` | realtime | first_class |
| `langgraph_agents` | enterprise_agent | first_class |
| `django_rest` | general | bounded_prototype |
| `vue_express` | general | bounded_prototype |
| `rust_embedded` | systems | structural_only |
| `quantum_sdk` | experimental | future |

### Feature Tier Semantics

- **first_class** — production-verified, proof-certified, included in shipping artefact
- **bounded_prototype** — scoped build, declared limitations in proof artefact
- **structural_only** — emitted as scaffold with documented placeholders
- **future** — excluded; deferred-feature record written to proof artefact

### Capability Family Maturity Contracts

| Capability Family | Maturity | Compiler Enforcement |
|---|---|---|
| commercial/mobile/game/realtime/enterprise lanes | first_class | lane contract must match app_type + allowed stack frontends + lane-specific validation expectations |
| chat-first builder | bounded_prototype | preview-first path with richer conversation-to-spec mapping, structured preview contract, and unsupported capability rejection |
| agent-runtime | bounded_prototype | approval-gated execution with blocked/completed semantics, bounded execution contract, and replay confidence metadata |
| self-extension/tool-factory | bounded_prototype | sandbox + stricter validation thresholds + registry/quarantine governance + operator-visible trust/rejection metadata |
| multimodal/world-state | structural_only | schema-only contract support plus schema consistency counters; no first-class live execution claims |
| security | bounded_prototype | commercial lane emits auth dependency scaffold, authorization header hook, RBAC placeholders, and security contract route |
| commerce | bounded_prototype | commercial lane emits plans route, billing webhook scaffold, entitlement service placeholder, billing admin route |
| cross-lane-composition | bounded_prototype | validates registered composition patterns, emits additive composition overlays, and rejects unsupported combinations explicitly |
| lifecycle | bounded_prototype | regeneration safety classification executes in build path; lifecycle decisions emitted as machine-readable artifact |
| enterprise-readiness | bounded_prototype | enterprise deployment/supportability/runbook/escalation artifacts emitted through proof enrichment |

### Truth And Limitations Policy

- Capability tables describe enforced contracts, not speculative future behavior.
- `bounded_prototype` means deterministic scaffold + contract enforcement with explicit runtime/operator boundaries.
- `structural_only` means schema and artifact support only; no claim of live side-effect execution.
- Regulated domain foundations are governance-aware templates and validation hooks, not autonomous compliance engines.

### Benchmark/Proof Semantics

- Benchmark scoring includes proof coverage, proof artifact coverage, failure-intelligence coverage, and breadth coverage.
- Proof/readiness outputs must be machine-readable and reproducible from deterministic signatures.

---

## Build and Ship Commands

### `build`

Compiles spec → IR → template pack → executes build → emits proof artefacts.

Output contract:

```json
{
  "command": "build",
  "status": "ok",
  "build_id": "<uuid>",
  "proof_artifacts": { }
}
```

Error output (exit code 2):

```json
{
  "command": "build",
  "status": "error",
  "error": "<message>"
}
```

### `ship`

Runs build → validation → proof certification → emits `package_artifact_summary.json`.

- Future-tier stacks are rejected at ship time.
- Writes final `package_artifact_summary.json` with `"ready"` status.

Output contract:

```json
{
  "command": "ship",
  "status": "ok",
  "build_status": "ok",
  "validation_result": { "status": "passed" },
  "proof_result": { "status": "certified — all platform hardening checks passed" }
}
```

---

## Command Safety Guarantees

All commands adhere to the following command safety guarantees:

1. **Idempotent reads** — `readiness`, `inspect`, `proof` never mutate system state.
2. **Explicit write surface** — only `build`, `ship`, `self-extend` write artefacts to disk.
3. **Exit codes** — `0` success, `1` internal error, `2` invalid input / missing spec files.
4. **JSON output contract** — every `--json` invocation returns a stable, versioned JSON schema.
5. **Future-tier gate** — `ship` refuses future-tier stacks; `build` degrades gracefully and records deferred features.

---

## Compiler Extension Points

| Hook | Location | Purpose |
|------|----------|---------|
| `SpecLoader.load()` | `specs/loader.py` | Normalise custom spec fields |
| `IRCompiler.compile()` | `ir/compiler.py` | Extend IR with domain fields |
| `get_lane_validation_plan()` | `generator/template_packs.py` | Override validation plan per lane |
| `enrich_proof_with_platform_hardening()` | `platform_hardening/proof_enrichment.py` | Add platform contracts to proof |

---

## Mission Orchestration Pipeline

The mission orchestration layer (`cli/mission.py`) extends the compiler pipeline with autonomous goal decomposition:

```
goal (natural language)
      │
      ▼
  _derive_capability_requirements()   — keyword → capability family routing
      │
      ▼
  Planner.create_plan()               — goal → task list with action_class metadata
      │
      ▼
  Executor.run_tasks_with_recovery()  — state transitions + evidence signatures
      │
      ▼
  _build_machine_readable_mission_plan()  — pause/resume semantics, run_id, signatures
      │
      ▼
  _build_operator_summary()           — human-readable next_action + honesty notes
```

### Capability Routing

Goals are keyword-matched against 14 capability families (auth, commerce, mobile, game, realtime, multimodal, mutation, agent, analytics, search, notification, storage, devops, i18n).  Each family maps to an acquisition route and maturity level.

### Mission Result Contract

```json
{
  "run_id": "<uuid>",
  "goal": "<string>",
  "status": "complete|partial|failed",
  "capability_requirements": [
    { "family": "<string>", "required": true, "acquisition_route": "<string>", "maturity": "<string>" }
  ],
  "mission_plan": {
    "plan_id": "<uuid>",
    "tasks": [],
    "pause_resume_semantics": { "supports_interruption_recovery": true }
  },
  "operator_summary": {
    "total_tasks": 0,
    "completed_tasks": 0,
    "next_action": "<string>",
    "honesty_note": "<string>"
  }
}
```

---

## Adapter Architecture

The adapter registry (`adapters/registry.py`) maps capability requirements to concrete integration adapters.

### Adapter Kinds

| Kind | Description | Examples |
|------|-------------|---------|
| `runtime` | Application runtime scaffolds | fastapi, nextjs, flutter, godot, websocket |
| `framework` | Data/infrastructure frameworks | postgres, docker_compose |
| `enterprise_connector` | External service integrations | stripe, sendgrid, s3, openai, ldap_sso |
| `tool_action` | Action-triggered integrations | webhook, approval_gate |
| `media_sensor` | Multimodal/sensor inputs | image_document, audio, sensor_event |

Adapters are validated on registration. `resolve_for_lane(lane_id, required_capabilities)` returns only validated adapters matching all required capabilities.

---

## Vertical Domain Packs

Six universal vertical domain packs extend the lane capability surface beyond the five first-class lanes:

| Pack ID | Maturity | Domain |
|---------|----------|--------|
| `vertical.operations_workflow.v1` | bounded_prototype | Internal ops tooling |
| `vertical.productivity_coordination.v1` | bounded_prototype | Team coordination |
| `vertical.monitoring_realtime.v1` | bounded_prototype | Metrics and alerting |
| `vertical.coaching_feedback.v1` | bounded_prototype | Structured feedback loops |
| `vertical.regulated_policy_bound.v1` | structural_only | Regulated domains (no automated compliance) |
| `vertical.enterprise_admin_reporting.v1` | bounded_prototype | Admin surfaces and reports |

All packs carry an `honesty_note` in metadata declaring operator wiring requirements.

---

## Benchmark Proof Semantics

Benchmark cases are categorised by proof dimension:

| Dimension | What it verifies |
|-----------|-----------------|
| `proof_coverage` | Proof artefact completeness and machine-readable signatures |
| `proof_artifact_coverage` | All per-lane artefacts are present and well-formed |
| `failure_intelligence_coverage` | Failure corpus classification and repair suggestions |
| `benchmark_breadth` | Scenario coverage across lanes, integrations, edge cases |
| `capability_routing` | Capability acquisition routes and maturity labels |
| `mission_orchestration` | Task decomposition, execution state, and recovery semantics |
| `adapter_resolution` | Adapter registry lane resolution |

---

## Known Limitations

- **No live code execution** — all build outputs are deterministic scaffolds, not executed binaries.
- **No network actuation** — adapters emit integration scaffolds; API calls require operator wiring.
- **Multimodal is structural_only** — audio/image/sensor contracts are schema-only; no runtime media processing.
- **Regulated domains require operator validation** — `vertical.regulated_policy_bound.v1` emits governance templates only; legal/compliance review is the operator's responsibility.
- **Auth/commerce require credential wiring** — generated auth and billing scaffolds need operator-supplied API keys and secrets to function.
- **No autonomous deployment** — ship command writes artefacts to disk; deployment to production infrastructure requires operator action.

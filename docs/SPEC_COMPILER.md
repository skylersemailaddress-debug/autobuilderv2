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

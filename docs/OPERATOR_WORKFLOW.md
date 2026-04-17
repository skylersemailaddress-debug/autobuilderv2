# Operator Workflow

This guide covers the end-to-end operator workflow for building, validating, and shipping applications with AutobuilderV2.

---

## Prerequisites

```bash
pip install -e ".[dev]"
autobuilder readiness --json          # verify all systems ready
```

---

## Step 1 — Author Spec Files

Create a spec bundle directory with the required YAML files:

```
my_app/
  mission.yml
  stack.yml
  features.yml
  constraints.yml   # optional
```

**`mission.yml`**

```yaml
app_name: My App
app_type: saas_web_app
```

**`stack.yml`**

```yaml
stack_id: react_stripe_firebase
```

**`features.yml`**

```yaml
features:
  - name: user_auth
    tier: first_class
  - name: payment_checkout
    tier: first_class
  - name: admin_dashboard
    tier: bounded_prototype
  - name: ai_recommendations
    tier: future
```

---

## Step 2 — Inspect Spec Bundle

```bash
autobuilder inspect specs/my_app --json
```

Returns the normalised spec bundle and any validation warnings before build time.

---

## Step 3 — Run Build

```bash
autobuilder build specs/my_app --json
```

Compiles spec → IR → template pack → proof artefacts.  Output includes `build_id` and `proof_artifacts`.

---

## Step 4 — Validate Generated App

```bash
autobuilder validate-app specs/my_app --json
```

Runs the lane-specific validation plan against the generated artefacts. Returns `{"status": "passed"}` on success.

---

## Step 5 — Certify Proof

```bash
autobuilder proof-app specs/my_app --json
```

Emits full proof certification including platform hardening, governance contract, commerce pack, and failure corpus.

---

## Step 6 — Ship

```bash
autobuilder ship specs/my_app --json
```

Runs build → validation → proof as a single atomic operation and writes `package_artifact_summary.json`.

Approval gate: if `control_plane/approvals.py` has pending approvals, `ship` will block until they are resolved.

---

## Approval / Governance Workflow

AutobuilderV2 integrates a control-plane approval gate for enterprise deployments.

```
operator triggers ship
        │
        ▼
  control_plane checks approvals
        │
   pending? ──yes──▶ block + log
        │no
        ▼
  build → validate → proof → package
        │
        ▼
  package_artifact_summary.json written
```

Approvals are stored in `state/approvals.json`. To inspect or clear:

```bash
autobuilder inspect approvals --json
```

---

## Support matrix scope

The operator must match the spec bundle's `app_type` and `stack_id` against the supported support matrix scope below.

| Lane | App Types | Stacks | Tier |
|------|-----------|--------|------|
| `first_class_commercial` | `saas_web_app`, `ecommerce_app` | `react_stripe_firebase`, `nextjs_postgres` | first_class |
| `first_class_mobile` | `mobile_app` | `flutter_mobile` | first_class |
| `first_class_game` | `game_app` | `godot_game` | first_class |
| `first_class_realtime` | `realtime_system` | `kafka_flink` | first_class |
| `first_class_enterprise_agent` | `enterprise_agent_system` | `langgraph_agents` | first_class |

**bounded_prototype stacks** (`django_rest`, `vue_express`) are supported for prototyping but cannot be shipped via the `ship` command.

**structural_only and future stacks** are rejected at build time for ship-path workflows.

### Capability family maturity

| Capability Family | Maturity | Operator Expectation |
|---|---|---|
| lane build/ship (commercial/mobile/game/realtime/enterprise) | first_class | full deterministic build + lane-specific validation + proof/readiness reporting with explicit bounded-runtime boundaries |
| chat-first builder | bounded_prototype | preview-first, richer conversation-to-spec mapping, structured preview contract, and explicit unsupported request rejection |
| agent-runtime | bounded_prototype | approval-gated steps, blocked/completed semantics, replay signature, bounded execution contract |
| self-extension/tool-factory | bounded_prototype | sandbox generation, stricter validation thresholding, registry/quarantine routing, operator-visible trust/rejection context |
| multimodal/world-state | structural_only | schema contract, snapshot validation, and schema consistency counters only |
| security | bounded_prototype | commercial lane emits auth dependency scaffold, authorization-header hook, RBAC placeholders, security contract route |
| commerce | bounded_prototype | commercial lane emits plans route, billing webhook scaffold, entitlement service placeholder, billing admin route |
| cross-lane-composition | bounded_prototype | composition patterns are validated, additive overlays are emitted, and unsupported combinations are explicitly rejected |
| lifecycle | bounded_prototype | build path emits lifecycle regeneration decisions; operator-modified production-critical files require approval |
| enterprise-readiness | bounded_prototype | proof artifacts include deployment/supportability/runbook/escalation readiness documents |

### Operator Truth Rules

1. Treat maturity tables as executable contract boundaries, not aspiration statements.
2. Require explicit operator approval for sensitive, destructive, or regulated-impact actions.
3. Interpret multimodal/world-state artifacts as contract readiness only unless maturity is raised by verified runtime behavior.
4. Validate benchmark/proof coverage metrics before promoting support claims.
5. Reject any workflow that claims support outside registered lane/capability contracts.

---

## Command Safety Guarantees

All commands adhere to the following command safety guarantees:

1. **Idempotent reads** — `readiness`, `inspect`, `proof` never mutate system state.
2. **Explicit write surface** — only `build`, `ship`, `self-extend` write artefacts to disk.
3. **Exit codes** — `0` success, `1` internal error, `2` invalid input / missing spec files.
4. **JSON output contract** — every `--json` invocation returns a stable JSON schema.
5. **Future-tier gate** — `ship` refuses future-tier stacks; `build` degrades gracefully.

---

## Governance Controls

| Control | Location | Purpose |
|---------|----------|---------|
| Approval gate | `control_plane/approvals.py` | Block ship until approvals cleared |
| Policy enforcement | `policies/` | Validate spec against policy rules |
| Proof certification | `platform_hardening/proof_enrichment.py` | Platform hardening sign-off |
| Observability | `observability/` | Emit structured execution logs |
| Mutation testing | `mutation/` | Verify test suite quality |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Missing required spec files` | Missing `mission.yml` or `stack.yml` | Create required files |
| `ship rejected: future-tier stack` | `stack_id` is in future tier | Switch to a supported stack |
| `approval pending` | Unapproved control-plane entry | Resolve via `inspect approvals` |
| `proof certification failed` | Platform hardening check failed | Review proof artefacts in `runs/` |

---

## Bootstrap

```bash
bash scripts/bootstrap_local.sh
```

Sets up a local virtual environment and installs all required dependencies.

---

## Cleanup Runtime

```bash
bash scripts/clean_runtime.sh
```

Removes generated artefacts and temporary run state.

---

## Packaging for Distribution

```bash
bash scripts/package_release.sh
```

Packages the current build output as a distributable release artefact.

---

## Benchmarking

```bash
autobuilder benchmark --json
```

Runs the full benchmark suite and returns scored results. Use this to validate mission throughput before shipping.

---

## Mission Replay

```bash
autobuilder mission --json
autobuilder resume --json
```

Run or resume an autonomous mission. All mission state is persisted under `runs/`.

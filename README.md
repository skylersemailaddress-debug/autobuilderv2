# AutobuilderV2

AutobuilderV2 is a **deterministic, spec-driven application build platform** with an autonomous execution kernel. It compiles canonical spec bundles into fully-structured target repositories, validates them through a provable artifact pipeline, and governs execution through operator-controlled approval gates.

---

## Quick Start

### Bootstrap

```bash
scripts/bootstrap_local.sh
```

Creates a virtual environment, installs dependencies, and prints next steps.

### Core Commands

```bash
# Check system readiness
python cli/autobuilder.py readiness --json

# Build a target repo from canonical specs
python cli/autobuilder.py build --spec specs --target /tmp/my-app --json

# Build + validate + emit proof artifacts
python cli/autobuilder.py ship --spec specs --target /tmp/my-app --json

# Run end-to-end proof workflow
python cli/autobuilder.py proof --json

# Start an autonomous mission
python cli/autobuilder.py mission "Your goal here" --json

# Inspect a saved run
python cli/autobuilder.py inspect <run_id> --json

# Resume a paused run (with optional approval)
python cli/autobuilder.py resume <run_id> --approve --json

# Run benchmarks
python cli/autobuilder.py benchmark --json

# Validate a previously built app
python cli/autobuilder.py validate-app --target /tmp/my-app --json

# Emit proof artifacts for a built app
python cli/autobuilder.py proof-app --target /tmp/my-app --json

# Chat-driven build preview
python cli/autobuilder.py chat-build --prompt "Build a SaaS task tracker" --target /tmp/preview --json

# Run an autonomous agent task
python cli/autobuilder.py agent-runtime --task "open app and save result" --approvals-json '{}' --json

# Extend a lane with a new capability
python cli/autobuilder.py self-extend --lane first_class_commercial --needs custom_validator --sandbox /tmp/sandbox --json
```

### Cleanup

```bash
scripts/clean_runtime.sh    # Remove runs, memory, and cache
scripts/package_release.sh  # Create distributable archive in dist/
```

---

## Architecture Overview

| Layer | Responsibility |
|---|---|
| **specs/** | Canonical spec bundle loader and validator |
| **ir/** | Intermediate Representation compiler (specs to IR) |
| **generator/** | Template pack execution (IR to target repo files) |
| **validator/** | Generated app proof artifact emitter |
| **platform_plugins/** | Lane plugin registry and resolution |
| **platform_hardening/** | Security governance, commerce, pack composition, failure corpus |
| **quality/** | Reliability scoring |
| **readiness/** | Readiness checks and report generation |
| **benchmarks/** | Benchmark harness and scoring |
| **cli/** | Unified command surface |
| **nexus/** | Autonomous execution kernel (Nexus mission mode) |
| **memory/** | Durable JSON memory with policy controls |

---

## Support Matrix

### Categories

| Category | Description |
|---|---|
| first_class | Full generation, validation, proof, repair, packaging, and determinism verification |
| bounded_prototype | Generation and validation only; repair is best-effort; no proof certification |
| structural_only | Scaffold structure only; no validation, repair, or proof |
| future | Planned; not yet implemented |

### Lanes

| Lane | App Types | Category |
|---|---|---|
| first_class_commercial | saas_web_app, workspace_app, internal_tool, api_service, workflow_system, copilot_chat_app | first_class |
| first_class_mobile | mobile_app | first_class |
| first_class_game | game_app | first_class |
| first_class_realtime | realtime_system | first_class |
| first_class_enterprise_agent | enterprise_agent_system | first_class |

### Supported Stacks (first_class lanes)

| Category | Stack | Tier |
|---|---|---|
| frontend | react_next | first_class |
| frontend | flutter_mobile | first_class |
| frontend | godot_game | first_class |
| backend | fastapi | first_class |
| database | postgres | first_class |
| deployment | docker_compose | first_class |

Stacks with tier `future` are rejected by the `ship` command.

### Advanced Capabilities

| Capability | Status |
|---|---|
| Determinism verification (repeat-build SHA256 match) | first_class |
| Proof artifact emission | first_class |
| Platform hardening (security governance, commerce pack, failure corpus, replay harness) | first_class |
| Reliability scoring | first_class |
| Autonomous mission execution (Nexus mode) | first_class |
| Approval gates and policy controls | first_class |
| Chat-first builder (conversation-to-spec, preview-first, project memory) | bounded_prototype |
| Agent-runtime (computer-use task modeling + approval-gated execution) | bounded_prototype |
| Self-extension/tool-factory (sandbox generation, validation, registry/quarantine) | bounded_prototype |
| Multimodal/world-state execution | structural_only |
| Multi-domain IR fields | first_class |

### Universal Capability Maturity Contracts

| Capability Family | Maturity | Contract |
|---|---|---|
| commercial web lane | first_class | deterministic build/ship/proof, full readiness and reliability reporting |
| mobile lane | first_class | flutter lane templates + lane validation + proof artifacts |
| game lane | first_class | godot lane templates + lane validation + proof artifacts |
| realtime/sensing lane | first_class | realtime scaffolds + world-state schema contract + proof artifacts |
| enterprise-agent/workflow lane | first_class | workflow scaffolds + approvals surfaces + proof artifacts |
| chat-first builder | bounded_prototype | preview-first deterministic flow, explicit unsupported-request rejection |
| agent-runtime | bounded_prototype | task model + approval gating + blocked/completed semantics + replay signature |
| self-extension/tool-factory | bounded_prototype | sandbox boundary, validation threshold, registry/quarantine, rollback references |
| multimodal/world-state | structural_only | schema normalization + world-state snapshot contracts only |

### Command Safety Guarantees

- All commands emit deterministic, repo-relative artifact paths.
- Mutation operations require explicit approval before execution.
- Rollback metadata is written before any destructive operation.
- The `ship` command rejects stacks with support_tier=future with a predictable error contract.
- All error responses include status=error and a command field.

---

## Command Output Contract

Every command that accepts `--json` returns a JSON object with at minimum:

```json
{
  "status": "ok",
  "command": "<command-name>"
}
```

Error responses always include an `"error"` field with a human-readable message.

---

## Operator Docs

| Document | Purpose |
|---|---|
| docs/SPEC_COMPILER.md | Canonical spec bundle format, IR contract, build mode behavior |
| docs/OPERATOR_WORKFLOW.md | Step-by-step operator workflow and governance controls |
| docs/NEXUS_EXECUTION.md | Nexus mission-mode behavior and interpretation guide |
| docs/NEXUS_MODE.md | Nexus mode architecture reference |
| docs/ARCHITECTURE.md | System architecture and component map |
| docs/ROADMAP.md | Planned future capabilities |
| docs/SYSTEM_DOCTRINE.md | Design principles and constraints |
| docs/ACCEPTANCE_CRITERIA.md | Acceptance criteria for all system behaviors |

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Type-check
mypy .
```

All tests are in `tests/`. The full suite must pass before committing.

---

## Local Bootstrap

```bash
bash scripts/bootstrap_local.sh
```

Sets up a virtual environment and installs all dependencies.

---

## Cleanup Runtime

```bash
bash scripts/clean_runtime.sh
```

Removes generated artefacts and temporary run state without touching source files.

---

## Package for Distribution

```bash
bash scripts/package_release.sh
```

Builds a distributable release artefact from the current state.

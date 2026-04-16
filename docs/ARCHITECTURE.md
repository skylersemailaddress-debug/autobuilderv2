# ARCHITECTURE

## Core Systems
- Orchestrator
- Planner
- State
- Memory
- Execution
- Mutation
- Debugger
- Validator
- Observability
- Control Plane
- Plugin Registry
- Platform Hardening Packs
- Security and Governance Contracts
- Commerce Contract Packs
- Runtime Verification and Repair Policies
- Failure Corpus and Replay Harness
- Computer-Use Agent Runtime
- Multimodal and World-State Schema Layer
- Self-Extension Meta-Builder and Tool Factory
- Capability Governance Registry and Rollback

## Run Lifecycle
1. Intake
2. Plan
3. Execute
4. Validate
5. Repair (if needed)
6. Complete

## Data Flow
Input -> Plan -> Tasks -> Execution -> Validation -> Output

Plugin build lanes resolve deterministically before generation:

Input -> Plugin Resolution -> Lane Generation -> Validation -> Stack Repair -> Runtime Verification -> Proof/Packaging

Current bounded first-class lanes:

- commercial web
- mobile
- game prototype
- realtime/sensing
- enterprise-agent/workflow

## Storage
- Run state
- Artifacts
- Logs
- Memory
- Failure corpus snapshots (`.autobuilder/failure_corpus.jsonl`)
- Replay harness snapshots (`.autobuilder/replay_harness.json`)
- Pack and contract artifacts (`.autobuilder/pack_composition.json`, `.autobuilder/security_governance_contract.json`, `.autobuilder/commerce_pack_contract.json`)

## Execution Model
- Task-based
- Retry-enabled
- Parallel where safe

## Recovery Model
- Checkpoints
- Rollback
- Resume

## Governance Model
- Auth/authz support contract points for generated lanes
- RBAC/ABAC-ready structures for future policy engines
- Secrets/config handling rules and safe-generation defaults
- Sensitive action policy hooks and approval workflow integration

## Determinism Model
- Deterministic plugin selection by lane-compatible metadata
- Deterministic pack composition profiles per lane
- Deterministic replay payload signatures for build/validate/proof workflows
- Deterministic computer-use plan and replay signatures
- Deterministic tool-candidate generation and validation scoring

## Autonomous Capability Growth Safeguards
- Sandbox-first candidate capability synthesis
- Validation thresholds before registration
- Optional approval gates for core-impact changes
- Quarantine path for rejected candidates
- Rollback support for active generated capabilities

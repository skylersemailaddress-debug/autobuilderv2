# AutobuilderV2 Changelog

All notable changes to AutobuilderV2 are documented in this file.

## [1.0.0-enterprise] - 2026-04-16

### Release Summary

Enterprise-ready stable release of AutobuilderV2 with clean local bootstrap, runtime artifact isolation, canonical operator workflows, and packaging support.

### Major Capabilities

#### Core Execution
- **Stateful Execution Kernel**: Autonomous task execution with durable run state saved to JSON
- **Task Planning**: Goal-driven task planning with repository context injection
- **Task Execution**: Supervised execution of planned tasks with artifact recording
- **Validation & Repair**: Deterministic validation with bounded repair loops

#### Operator Controls
- **Approval Gates**: High-risk operations pause awaiting operator approval
- **Resume Capability**: Approved operations resume cleanly from checkpoints
- **Run Inspection**: Live inspection of run state and execution history
- **Status Tracking**: Complete event logging and mission status tracking

#### Governance & Readiness
- **Readiness Checks**: Deterministic readiness evaluation gates
- **Quality Reports**: Validation evidence and quality metrics
- **Benchmarks**: Regression test runner and scoring analysis
- **Proof of Execution**: Deterministic proof that execution operates as designed

#### Advanced Features
- **Nexus0.5 Mission Mode**: Mission-specific metadata and governance controls
- **Policy Framework**: Flexible action policies and safety constraints
- **Memory System**: In-memory + durable JSON memory for cross-run context
- **Mutation Safety**: Safe AST-based code mutation and repair

### Local Setup & Operations

#### Bootstrap
Run once to set up a clean development environment:
```bash
scripts/bootstrap_local.sh
```

#### Canonical Operations
```bash
python cli/autobuilder.py mission "Your goal" --json
python cli/autobuilder.py readiness --json
python cli/autobuilder.py proof --json
python cli/autobuilder.py benchmark --json
python cli/autobuilder.py inspect <run_id> --json
python cli/autobuilder.py resume <run_id> --approve --json
```

#### Runtime Cleanup
Remove generated artifacts and runtime noise:
```bash
scripts/clean_runtime.sh
```

#### Packaging for Distribution
Create a clean distributable archive:
```bash
scripts/package_release.sh
```

### Artifact Isolation

- Source code, tests, and documentation remain pristine
- Runtime artifacts (runs/*.json, memory/*.json) cleanly isolated
- Robust .gitignore prevents accidental commits of generated noise
- Bootstrap and cleanup scripts ensure deterministic state

### Repository Hygiene

- Comprehensive .gitignore covering Python, testing, IDE, and runtime artifacts
- Clean source/runtime separation documented
- Deterministic bootstrap and cleanup workflows
- Enterprise packaging path for distribution

### Notes

This release establishes AutobuilderV2 as an enterprise-ready autonomous execution kernel suitable for locally-portable deployments, governed autonomy chains, and deterministic validation workflows.

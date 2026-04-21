# Remaining Microscopic Gaps — Must Finish

These are not optional polish items. They are locked edge-hardening requirements for the repository's final truth system.

## Gap 1 — Build and run verification depth
The system must not rely only on generated-output structural validation. It must prove real runtime behavior for generated artifacts.

Required:
- frontend build execution for supported classes where applicable
- backend process start verification
- HTTP health verification against the started backend
- failure on inability to prove runtime behavior

## Gap 2 — Artifact integrity linkage
Fresh artifacts are not enough. The repository must prove that evidence artifacts correspond to the current repo state.

Required:
- commit-aware or content-hash-aware linkage between current code and evidence artifacts
- failure when artifacts are fresh but not attributable to current repo state
- machine-readable integrity record in the evidence bundle

## Gap 3 — Parallel class isolation
Sequential in-process supported-class execution is not sufficient for final trust.

Required:
- isolated execution per supported app class, or equivalent contamination-safe proof
- failure when shared-state contamination risk cannot be ruled out
- explicit execution isolation strategy documented in repo

## Definition
These gaps are considered open until validators prove them. They are part of the final 10/10 truth barrier.

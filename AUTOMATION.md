# AutobuilderV2 Automation Mode

This repository is being set up so the majority of bootstrapping happens through committed files instead of manual terminal entry.

## Current state

- Core docs initialized
- Orchestration spine initialized
- State store initialized
- Validator initialized
- Tests passing in Codespaces after sync

## Working rule

Prefer pushing code and scripts into the repository over asking the operator to paste commands manually.

## Near-term objective

Turn the current scaffold into a runnable autonomous system with:

1. Persistent run records
2. CLI entrypoint
3. Task model
4. Planner stub
5. Execution loop
6. Repair loop
7. Structured validation evidence

## Operator workflow

1. Open Codespaces
2. Sync latest changes
3. Run the committed runner or test entrypoints
4. Review results

## Design principle

The human should do as little terminal work as possible. The repository should carry the setup and execution burden.

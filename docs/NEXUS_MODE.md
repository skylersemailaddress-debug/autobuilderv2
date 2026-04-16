# Nexus0.5 Mission Mode

Nexus mode is a controlled autonomous execution mode for AutobuilderV2 that targets the Nexus0.5 mission.

## What Nexus mode is

Nexus mode enables mission-specific execution behavior for Nexus0.5. It turns on repository-aware planning, persistent memory usage, approval handling, resumability metadata, and contract validation.

## How it changes run behavior

When Nexus mode is enabled:

- `repo_context` is actively used to influence planning and summary calculations.
- `memory_context` is preserved and applied across runs.
- `ActionPolicy` is engaged to determine whether approval pauses are required.
- contract validation is enabled for plan artifacts, task outputs, and run summaries.
- resumability metadata is recorded so interrupted runs can be resumed safely.

Nexus mode is enabled through the CLI with the `--nexus` flag.

## What is persisted

Nexus mode runs persist the following additional top-level record fields:

- `nexus_mode`: `true` when Nexus mode is enabled
- `project_name`: always `"Nexus0.5"` in Nexus mode
- `approvals_enabled`: whether approval logic is active
- `resumability_enabled`: whether resumability metadata is recorded
- `memory_enabled`: whether memory context is preserved
- `contract_validation_enabled`: whether contract checks are active

The run summary also persists:

- `project_name`
- `nexus_mode`
- `repo_mode`
- `approvals_enabled`
- `resumability_enabled`

## How approval pauses work

When Nexus mode is enabled, high-risk actions may trigger an approval request using `ActionPolicy` and `control_plane.approvals.require_approval`. A run paused for approval sets `awaiting_approval` in the run summary and record. Once approval is granted, the run may resume from the saved state.

## How resume should work

Resumability metadata is added to run records so the resume path can infer the next actionable stage. If a Nexus run is interrupted or paused, the saved record includes the context needed to resume execution rather than starting over.

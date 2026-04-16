# ACCEPTANCE CRITERIA

## System Level
- Must complete full app builds autonomously
- Must recover from failures without manual intervention
- Must validate outputs before completion
- Must support resume and continuity

## Enterprise Level
- Must provide audit logs
- Must enforce policies
- Must support secure execution
- Must generate deterministic loading/empty/error UI states for first-class web builds
- Must generate operator/admin/activity placeholder surfaces in first-class web builds
- Must generate health/readiness/version endpoints plus operator/admin/audit backend placeholders
- Must emit proof/readiness artifact files for generated apps
- Must fail build when generated-app enterprise validation checks do not pass
- Must attempt bounded auto-repair for common generated-app defects in first-class stack output
- Must emit machine-readable build/validation/proof status plus repaired/unrepaired issue details

## Launch Criteria
- Repeatable success across multiple builds
- Low failure rate
- Minimal human intervention required

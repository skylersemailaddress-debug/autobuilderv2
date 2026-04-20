# Incident Response Runbook

## Detection
- Monitor failed CI runs
- Monitor benchmark drops

## Triage
- Identify failing component
- Check logs and recent commits

## Mitigation
- Roll back to last valid artifact
- Disable failing feature if needed

## Recovery
- Re-run benchmarks
- Validate output lane

## Postmortem
- Record root cause
- Add regression test

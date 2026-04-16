# Operator Guide

## Inspect a Run

```
python -m cli.inspect runs/<run_id>.json
```

## Control States

- running: actively executing
- resumable: can be resumed
- awaiting_approval: waiting for human input
- complete: finished successfully
- failed: execution failed

## Usage

Use inspect to determine if a run needs approval or can resume.

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

## Run Lifecycle
1. Intake
2. Plan
3. Execute
4. Validate
5. Repair (if needed)
6. Complete

## Data Flow
Input -> Plan -> Tasks -> Execution -> Validation -> Output

## Storage
- Run state
- Artifacts
- Logs
- Memory

## Execution Model
- Task-based
- Retry-enabled
- Parallel where safe

## Recovery Model
- Checkpoints
- Rollback
- Resume

# SYSTEM DOCTRINE

## System Definition
AutobuilderV2 is a stateful autonomous software factory that plans, builds, tests, debugs, repairs, and delivers enterprise applications.

## What is a Run
A run is a fully traceable execution lifecycle from input request to validated output.

## Done Definition
A run is done only when all validation gates pass and the application is deployable.

## Launch-Ready Definition
An application is launch-ready when it passes build, test, security, and deployment validation with full auditability.

## Operating Modes
- build
- repair
- extend
- migrate
- audit

## Stop Conditions
- success
- policy violation
- unrecoverable failure

## Escalation Conditions
- repeated failure beyond threshold
- ambiguous root cause

## Approval Conditions
- destructive changes
- production deployment

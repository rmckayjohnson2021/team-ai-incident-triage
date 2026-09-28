# Ambiguous Outage Runbook

## Symptoms

- Multiple services report errors.
- Incident report lacks clear failure point.
- Impact is unclear.

## Evidence To Check

- Error timestamps
- Affected services
- Recent deployments
- Provider status pages
- Pipeline dependency graph

## Recommended Next Steps

Collect missing evidence, identify the first failing component, and route to human review before recommending remediation.

## Escalation Conditions

- Severity or blast radius is unclear.
- More than one service is affected.
- Evidence is insufficient.

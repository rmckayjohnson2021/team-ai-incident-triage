# Stale Dashboard Runbook

## Symptoms

- Dashboard shows old data.
- Data pipeline completed but BI refresh did not.

## Evidence To Check

- Last warehouse update
- Dashboard refresh timestamp
- BI tool refresh logs
- Failed scheduled jobs

## Recommended Next Steps

Confirm warehouse freshness, refresh the dashboard dataset, and notify users if the dashboard was stale during business hours.

## Escalation Conditions

- Executive or customer-facing dashboard is stale.
- Source data is also stale.

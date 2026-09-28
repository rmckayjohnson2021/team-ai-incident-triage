# Failed Import Runbook

## Symptoms

- Scheduled import did not complete.
- Downstream tables or dashboards are missing fresh data.

## Evidence To Check

- Source file arrival time
- File format and delimiter
- Row counts
- Parser error logs

## Recommended Next Steps

Validate the source file, compare row counts with the previous successful import, fix parser or mapping issues, then rerun the import after review.

## Escalation Conditions

- Customer-facing dashboard is stale.
- Multiple retries fail.
- Source data appears corrupt.

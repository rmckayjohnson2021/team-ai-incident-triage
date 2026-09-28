# Duplicate Records Runbook

## Symptoms

- Row counts increase unexpectedly.
- Primary key checks fail.
- Reports show duplicated transactions or customers.

## Evidence To Check

- Deduplication key
- Load window
- Upstream resend events
- Merge or upsert logs

## Recommended Next Steps

Identify duplicate keys, isolate the affected load window, stop downstream refreshes if needed, and rerun with corrected deduplication logic.

## Escalation Conditions

- Duplicate records affect financial reporting.
- Duplicate records have already reached customer-facing systems.

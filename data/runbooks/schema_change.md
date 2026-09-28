# Schema Change Runbook

## Symptoms

- Import fails after a new, missing, renamed, or type-changed column.
- Validation rejects source files.

## Evidence To Check

- Source schema
- Expected schema
- Column names and types
- Recent vendor or upstream release notes

## Recommended Next Steps

Compare actual and expected schemas, update mapping logic after review, rerun validation, then replay the affected import.

## Escalation Conditions

- Breaking change affects multiple pipelines.
- Required fields are missing.

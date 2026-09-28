# Evaluation Report

Dataset: `data\incidents\heldout_cases.jsonl`
Cases evaluated: **20**

## Summary

| Metric | Result |
| --- | ---: |
| Category accuracy | 95% |
| Severity accuracy | 100% |
| Runbook match rate | 95% |
| Review routing accuracy | 100% |
| Provider errors | 0 |
| Average latency | 8679 ms |
| Median latency | 8664 ms |
| Input tokens | 13784 |
| Output tokens | 23723 |

## Case Results

| ID | Expected Category | Actual Category | Severity | Runbook | Review Route | Latency |
| --- | --- | --- | --- | --- | --- | ---: |
| HELD-001 | schema_change | schema_change | sev2 -> sev2 | schema_change.md -> failed_import.md, schema_change.md | yes -> yes | 7310 ms |
| HELD-002 | schema_change | schema_change | sev2 -> sev2 | schema_change.md -> schema_change.md, failed_import.md, stale_dashboard.md | no -> no | 9167 ms |
| HELD-003 | schema_change | schema_change | sev2 -> sev2 | schema_change.md -> failed_import.md, schema_change.md | no -> no | 8579 ms |
| HELD-004 | schema_change | schema_change | sev2 -> sev2 | schema_change.md -> failed_import.md, schema_change.md | yes -> yes | 7552 ms |
| HELD-005 | failed_import | failed_import | sev3 -> sev3 | failed_import.md -> failed_import.md | no -> no | 5852 ms |
| HELD-006 | failed_import | failed_import | sev2 -> sev2 | failed_import.md -> failed_import.md | no -> no | 6808 ms |
| HELD-007 | failed_import | failed_import | sev2 -> sev2 | failed_import.md -> failed_import.md, schema_change.md, stale_dashboard.md | yes -> yes | 11796 ms |
| HELD-008 | failed_import | failed_import | sev3 -> sev3 | failed_import.md -> failed_import.md | no -> no | 10893 ms |
| HELD-009 | duplicate_records | schema_change | sev2 -> sev2 | duplicate_records.md -> duplicate_records.md, failed_import.md, schema_change.md | no -> no | 8749 ms |
| HELD-010 | duplicate_records | duplicate_records | sev3 -> sev3 | duplicate_records.md -> duplicate_records.md | no -> no | 9029 ms |
| HELD-011 | duplicate_records | duplicate_records | sev1 -> sev1 | duplicate_records.md -> duplicate_records.md, failed_import.md, stale_dashboard.md | yes -> yes | 8876 ms |
| HELD-012 | duplicate_records | duplicate_records | sev3 -> sev3 | duplicate_records.md -> duplicate_records.md, failed_import.md, schema_change.md | no -> no | 12179 ms |
| HELD-013 | stale_dashboard | stale_dashboard | sev2 -> sev2 | stale_dashboard.md -> stale_dashboard.md, failed_import.md, ambiguous_outage.md | no -> no | 8194 ms |
| HELD-014 | stale_dashboard | stale_dashboard | sev3 -> sev3 | stale_dashboard.md -> stale_dashboard.md | no -> no | 7188 ms |
| HELD-015 | stale_dashboard | stale_dashboard | sev3 -> sev3 | stale_dashboard.md -> stale_dashboard.md | no -> no | 8870 ms |
| HELD-016 | stale_dashboard | stale_dashboard | sev2 -> sev2 | stale_dashboard.md -> stale_dashboard.md, ambiguous_outage.md | yes -> yes | 10601 ms |
| HELD-017 | ambiguous_outage | ambiguous_outage | sev1 -> sev1 | ambiguous_outage.md -> ambiguous_outage.md, stale_dashboard.md, failed_import.md | yes -> yes | 9586 ms |
| HELD-018 | ambiguous_outage | ambiguous_outage | sev3 -> sev3 | ambiguous_outage.md -> stale_dashboard.md, failed_import.md, ambiguous_outage.md | yes -> yes | 5840 ms |
| HELD-019 | ambiguous_outage | ambiguous_outage | sev2 -> sev2 | ambiguous_outage.md -> stale_dashboard.md, failed_import.md, duplicate_records.md | yes -> yes | 8306 ms |
| HELD-020 | ambiguous_outage | ambiguous_outage | sev2 -> sev2 | ambiguous_outage.md -> ambiguous_outage.md, failed_import.md, schema_change.md | yes -> yes | 8209 ms |

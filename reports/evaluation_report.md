# Evaluation Report

Dataset: `data\incidents\heldout_cases.jsonl`
Cases evaluated: **20**

## Summary

| Metric | Result |
| --- | ---: |
| Category accuracy | 90% |
| Severity accuracy | 35% |
| Runbook match rate | 95% |
| Review routing accuracy | 70% |
| Provider errors | 0 |
| Average latency | 14175 ms |
| Median latency | 13739 ms |
| Input tokens | 10464 |
| Output tokens | 25632 |

## Case Results

| ID | Expected Category | Actual Category | Severity | Runbook | Review Route | Latency |
| --- | --- | --- | --- | --- | --- | ---: |
| HELD-001 | schema_change | schema_change | sev2 -> sev2 | schema_change.md -> failed_import.md, schema_change.md | yes -> no | 15960 ms |
| HELD-002 | schema_change | schema_change | sev2 -> sev2 | schema_change.md -> schema_change.md, failed_import.md, stale_dashboard.md | no -> no | 13086 ms |
| HELD-003 | schema_change | schema_change | sev2 -> unknown | schema_change.md -> failed_import.md, schema_change.md | no -> no | 10090 ms |
| HELD-004 | schema_change | schema_change | sev2 -> sev1 | schema_change.md -> failed_import.md, schema_change.md, stale_dashboard.md | yes -> no | 14163 ms |
| HELD-005 | failed_import | failed_import | sev3 -> sev2 | failed_import.md -> failed_import.md, schema_change.md, duplicate_records.md | no -> no | 18702 ms |
| HELD-006 | failed_import | failed_import | sev2 -> sev2 | failed_import.md -> failed_import.md, schema_change.md | no -> no | 13691 ms |
| HELD-007 | failed_import | failed_import | sev2 -> sev2 | failed_import.md -> failed_import.md, schema_change.md, stale_dashboard.md | yes -> no | 12392 ms |
| HELD-008 | failed_import | failed_import | sev3 -> sev2 | failed_import.md -> failed_import.md, schema_change.md | no -> no | 14924 ms |
| HELD-009 | duplicate_records | duplicate_records | sev2 -> sev1 | duplicate_records.md -> duplicate_records.md, failed_import.md, schema_change.md | no -> no | 13183 ms |
| HELD-010 | duplicate_records | duplicate_records | sev3 -> sev2 | duplicate_records.md -> duplicate_records.md, failed_import.md | no -> no | 16148 ms |
| HELD-011 | duplicate_records | duplicate_records | sev1 -> sev2 | duplicate_records.md -> duplicate_records.md, failed_import.md | yes -> no | 13787 ms |
| HELD-012 | duplicate_records | duplicate_records | sev3 -> sev2 | duplicate_records.md -> duplicate_records.md, failed_import.md, schema_change.md | no -> no | 16644 ms |
| HELD-013 | stale_dashboard | stale_dashboard | sev2 -> sev2 | stale_dashboard.md -> stale_dashboard.md, failed_import.md, ambiguous_outage.md | no -> no | 12220 ms |
| HELD-014 | stale_dashboard | stale_dashboard | sev3 -> sev3 | stale_dashboard.md -> stale_dashboard.md | no -> no | 18796 ms |
| HELD-015 | stale_dashboard | stale_dashboard | sev3 -> unknown | stale_dashboard.md -> stale_dashboard.md | no -> yes | 10061 ms |
| HELD-016 | stale_dashboard | stale_dashboard | sev2 -> sev2 | stale_dashboard.md -> stale_dashboard.md, failed_import.md, ambiguous_outage.md | yes -> no | 13685 ms |
| HELD-017 | ambiguous_outage | unknown | sev1 -> unknown | ambiguous_outage.md -> stale_dashboard.md, failed_import.md, ambiguous_outage.md | yes -> yes | 18391 ms |
| HELD-018 | ambiguous_outage | unknown | sev3 -> unknown | ambiguous_outage.md -> stale_dashboard.md, failed_import.md, ambiguous_outage.md | yes -> yes | 11375 ms |
| HELD-019 | ambiguous_outage | ambiguous_outage | sev2 -> unknown | ambiguous_outage.md -> stale_dashboard.md, failed_import.md, duplicate_records.md | yes -> yes | 15101 ms |
| HELD-020 | ambiguous_outage | ambiguous_outage | sev2 -> unknown | ambiguous_outage.md -> ambiguous_outage.md, failed_import.md, schema_change.md | yes -> yes | 11107 ms |

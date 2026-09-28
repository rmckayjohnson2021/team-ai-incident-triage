from pathlib import Path

from app.triage.execution import ModelResult
from app.triage.review_log import (
    append_review,
    create_review_record,
    load_reviews,
    render_review_report,
    summarize_reviews,
)
from app.triage.schemas import IncidentAnalysis
from app.triage.workflow import TriageRun


def fake_run() -> TriageRun:
    return TriageRun(
        analysis=IncidentAnalysis(
            category="schema_change",
            severity="sev2",
            summary="Unexpected vendor column blocked the import.",
            evidence=["The vendor added loyalty_tier."],
            recommendation="Validate the schema mapping, then rerun the import.",
            source_runbooks=["schema_change.md"],
            route="strong_model",
            route_reason="Schema-change evidence matched the runbook.",
            review_status="approved",
        ),
        retrieved_sources=[],
        model_result=ModelResult(text="{}", latency_ms=120, input_tokens=10, output_tokens=20),
        total_latency_ms=150,
        prompt="prompt",
    )


def test_review_log_round_trip(tmp_path: Path):
    path = tmp_path / "triage_reviews.jsonl"
    record = create_review_record(
        run=fake_run(),
        incident_id="DEV-001",
        case_label="Development | DEV-001 | Schema change",
        incident_text="The vendor added loyalty_tier and the import failed.",
        outcome="edited",
        reason_tags=["missing_runbook_guidance", "wrong_severity"],
        corrected_category="schema_change",
        corrected_severity="sev3",
        reviewer_note="Severity was localized.",
        proposed_runbook_update="Add a mapping check for optional vendor columns.",
        promote_to_eval=True,
    )

    append_review(record, path)
    loaded = load_reviews(path)

    assert loaded == [record]
    assert loaded[0].incident_text_hash
    assert "loyalty_tier" not in loaded[0].model_dump_json()


def test_summarize_reviews_counts_learning_signals():
    record = create_review_record(
        run=fake_run(),
        incident_id="DEV-001",
        case_label="Development | DEV-001 | Schema change",
        incident_text="incident",
        outcome="rejected",
        reason_tags=["wrong_category", "should_have_required_human_review"],
        corrected_category="failed_import",
        corrected_severity="sev2",
        promote_to_eval=True,
    )

    summary = summarize_reviews([record])

    assert summary.total_reviews == 1
    assert summary.outcome_counts["rejected"] == 1
    assert summary.category_corrections == 1
    assert summary.severity_corrections == 0
    assert summary.human_review_routing_concerns == 1
    assert summary.promoted_eval_candidates == 1


def test_render_review_report_includes_backlog_sections():
    record = create_review_record(
        run=fake_run(),
        incident_id="DEV-001",
        case_label="Development | DEV-001 | Schema change",
        incident_text="incident",
        outcome="edited",
        reason_tags=["missing_runbook_guidance"],
        corrected_category="schema_change",
        corrected_severity="sev2",
        proposed_runbook_update="Clarify when to retry after schema review.",
    )

    report = render_review_report([record], Path("data/reviews/triage_reviews.jsonl"))

    assert "# Review Learning Report" in report
    assert "| Edited | 1 |" in report
    assert "## Proposed Runbook Updates" in report
    assert "Clarify when to retry" in report

import json
from pathlib import Path

from app.triage import evaluation
from app.triage.execution import ModelResult
from app.triage.schemas import IncidentAnalysis
from app.triage.workflow import TriageRun


def sample_case() -> dict[str, object]:
    return {
        "incident_id": "HELD-T01",
        "title": "Vendor file added a required column",
        "description": "The import failed after a new column appeared in the source file.",
        "expected_category": "schema_change",
        "expected_severity": "sev2",
        "expected_runbook": "schema_change.md",
        "should_escalate": False,
    }


def fake_run() -> TriageRun:
    return TriageRun(
        analysis=IncidentAnalysis(
            category="schema_change",
            severity="sev2",
            summary="The incident matches a schema change.",
            evidence=["The source file added a new column."],
            recommendation="Validate the schema mapping and rerun after review.",
            source_runbooks=["schema_change.md"],
            route="strong_model",
            route_reason="Schema-change evidence was retrieved.",
            review_status="approved",
        ),
        retrieved_sources=[],
        model_result=ModelResult(
            text="{}",
            latency_ms=120,
            input_tokens=50,
            output_tokens=25,
        ),
        total_latency_ms=150,
        prompt="incident prompt",
    )


def test_load_cases_reads_jsonl(tmp_path: Path):
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text(json.dumps(sample_case()) + "\n", encoding="utf-8")

    cases = evaluation.load_cases(dataset)

    assert len(cases) == 1
    assert cases[0]["incident_id"] == "HELD-T01"


def test_evaluate_cases_scores_expected_labels(monkeypatch):
    monkeypatch.setattr(evaluation, "triage_incident_with_context", lambda _text: fake_run())

    rows = evaluation.evaluate_cases([sample_case()], limit=None)
    summary = evaluation.score_rows(rows)

    assert rows[0].category_match is True
    assert rows[0].severity_match is True
    assert rows[0].runbook_match is True
    assert rows[0].review_match is True
    assert summary.category_accuracy == 1
    assert summary.total_input_tokens == 50
    assert summary.total_output_tokens == 25


def test_render_markdown_includes_summary_table(monkeypatch):
    monkeypatch.setattr(evaluation, "triage_incident_with_context", lambda _text: fake_run())

    rows = evaluation.evaluate_cases([sample_case()], limit=1)
    markdown = evaluation.render_markdown(
        evaluation.score_rows(rows),
        rows,
        Path("data/incidents/heldout_cases.jsonl"),
    )

    assert "# Evaluation Report" in markdown
    assert "| Category accuracy | 100% |" in markdown
    assert "| HELD-T01 | schema_change | schema_change |" in markdown

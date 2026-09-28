from app.triage.schemas import IncidentAnalysis


def test_schema_accepts_valid_result():
    result = IncidentAnalysis(
        category="schema_change",
        severity="sev2",
        summary="A vendor schema changed.",
        evidence=["new column"],
        recommendation="Validate mapping and rerun after review.",
        source_runbooks=["schema_change.md"],
        route="strong_model",
        route_reason="Schema change requires stronger model in starter.",
        review_status="approved",
    )

    assert result.category == "schema_change"

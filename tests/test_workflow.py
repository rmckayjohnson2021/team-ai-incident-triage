from app.triage.schemas import IncidentAnalysis
from app.triage.workflow import calibrate_analysis


def base_analysis(**overrides):
    data = {
        "category": "schema_change",
        "severity": "unknown",
        "summary": "Summary",
        "evidence": [],
        "recommendation": "Recommendation",
        "source_runbooks": ["schema_change.md"],
        "route": "strong_model",
        "route_reason": "Evidence matched a runbook.",
        "review_status": "approved",
    }
    data.update(overrides)
    return IncidentAnalysis(**data)


def test_calibration_routes_required_schema_change_to_review():
    analysis = calibrate_analysis(
        "The required reason_code column disappeared and chargeback reporting depends on it.",
        [{"name": "schema_change.md"}],
        base_analysis(),
    )

    assert analysis.severity == "sev2"
    assert analysis.route == "human_review"
    assert analysis.review_status == "human_review_required"


def test_calibration_marks_ambiguous_outage_as_review_and_sev1():
    analysis = calibrate_analysis(
        "Several pipelines failed after warehouse maintenance and no clear first failing component exists.",
        [{"name": "ambiguous_outage.md"}],
        base_analysis(category="unknown", source_runbooks=[]),
    )

    assert analysis.category == "ambiguous_outage"
    assert analysis.severity == "sev1"
    assert analysis.review_status == "human_review_required"
    assert "ambiguous_outage.md" in analysis.source_runbooks


def test_calibration_keeps_routine_late_file_approved():
    analysis = calibrate_analysis(
        "The vendor sales file arrived late and appeared in SFTP after the import window closed.",
        [{"name": "failed_import.md"}],
        base_analysis(category="failed_import", source_runbooks=["failed_import.md"]),
    )

    assert analysis.severity == "sev3"
    assert analysis.route == "strong_model"
    assert analysis.review_status == "approved"


def test_calibration_recovers_routine_duplicate_replay():
    analysis = calibrate_analysis(
        "Duplicate product reviews after moderation replay. review_id is duplicated in the review_fact table.",
        [{"name": "duplicate_records.md"}],
        base_analysis(
            category="unknown",
            severity="unknown",
            source_runbooks=["duplicate_records.md"],
            route="human_review",
            review_status="human_review_required",
        ),
    )

    assert analysis.category == "duplicate_records"
    assert analysis.severity == "sev3"
    assert analysis.review_status == "approved"


def test_calibration_does_not_treat_dashboard_as_board_reporting():
    analysis = calibrate_analysis(
        "Regional operations dashboard shows stale store counts for the Northeast region.",
        [{"name": "stale_dashboard.md"}],
        base_analysis(category="stale_dashboard", severity="sev2", source_runbooks=["stale_dashboard.md"]),
    )

    assert analysis.severity == "sev3"


def test_calibration_corrects_schema_category_from_column_evidence():
    analysis = calibrate_analysis(
        "The invoice import loaded zero rows because a tax_country field was inserted before amount_due.",
        [{"name": "failed_import.md"}, {"name": "schema_change.md"}],
        base_analysis(category="failed_import", severity="sev2", source_runbooks=["failed_import.md"]),
    )

    assert analysis.category == "schema_change"
    assert analysis.severity == "sev2"
    assert "schema_change.md" in analysis.source_runbooks


def test_calibration_corrects_failed_import_access_issue():
    analysis = calibrate_analysis(
        "The store traffic import failed because the service account received permission denied.",
        [{"name": "failed_import.md"}, {"name": "stale_dashboard.md"}],
        base_analysis(category="unknown", severity="unknown", source_runbooks=["failed_import.md"]),
    )

    assert analysis.category == "failed_import"
    assert analysis.severity == "sev2"
    assert analysis.review_status == "human_review_required"


def test_calibration_approves_routine_duplicate_financial_adjustment():
    analysis = calibrate_analysis(
        "Duplicate order adjustments after manual replay caused margin reporting to double-count adjustments.",
        [{"name": "duplicate_records.md"}],
        base_analysis(
            category="duplicate_records",
            severity="sev2",
            source_runbooks=["duplicate_records.md"],
            route="human_review",
            review_status="human_review_required",
        ),
    )

    assert analysis.category == "duplicate_records"
    assert analysis.severity == "sev2"
    assert analysis.review_status == "approved"


def test_calibration_approves_routine_schema_type_change():
    analysis = calibrate_analysis(
        "Web events export changed session_duration from integer to string and affects a dashboard.",
        [{"name": "schema_change.md"}, {"name": "stale_dashboard.md"}],
        base_analysis(
            category="schema_change",
            severity="sev2",
            source_runbooks=["schema_change.md"],
            route="human_review",
            review_status="human_review_required",
        ),
    )

    assert analysis.category == "schema_change"
    assert analysis.severity == "sev2"
    assert analysis.review_status == "approved"


def test_calibration_keeps_row_count_validation_as_failed_import():
    analysis = calibrate_analysis(
        "The file loaded into quarantine because row count validation failed with 30 percent fewer rows.",
        [{"name": "failed_import.md"}, {"name": "schema_change.md"}],
        base_analysis(category="schema_change", severity="sev2", source_runbooks=["schema_change.md"]),
    )

    assert analysis.category == "failed_import"
    assert analysis.severity == "sev3"


def test_calibration_does_not_treat_several_adjustments_as_ambiguous():
    analysis = calibrate_analysis(
        "Duplicate adjustment_id values after manual replay double-count several adjustments.",
        [{"name": "duplicate_records.md"}, {"name": "ambiguous_outage.md"}],
        base_analysis(category="unknown", severity="unknown", source_runbooks=["duplicate_records.md"]),
    )

    assert analysis.category == "duplicate_records"
    assert analysis.severity == "sev2"


def test_calibration_detects_conflicting_alerts_as_ambiguous_without_retrieved_runbook():
    analysis = calibrate_analysis(
        "Conflicting alerts from imports and dashboard refresh jobs appeared and no owner confirmed the cause.",
        [{"name": "stale_dashboard.md"}, {"name": "failed_import.md"}],
        base_analysis(category="stale_dashboard", severity="sev3", source_runbooks=["stale_dashboard.md"]),
    )

    assert analysis.category == "ambiguous_outage"
    assert analysis.severity == "sev2"
    assert analysis.review_status == "human_review_required"

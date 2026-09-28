import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.triage.execution import configured_model
from app.triage.schemas import Category, Severity
from app.triage.workflow import TriageRun

DEFAULT_REVIEW_LOG = Path("data/reviews/triage_reviews.jsonl")

ReviewOutcome = Literal["accepted", "edited", "rejected"]
ReviewReason = Literal[
    "wrong_category",
    "wrong_severity",
    "missing_runbook_guidance",
    "weak_evidence",
    "should_have_required_human_review",
    "should_not_have_required_human_review",
    "recommendation_not_actionable",
    "provider_or_format_issue",
]

REVIEW_OUTCOMES: tuple[ReviewOutcome, ...] = ("accepted", "edited", "rejected")
REVIEW_REASON_TAGS: tuple[ReviewReason, ...] = (
    "wrong_category",
    "wrong_severity",
    "missing_runbook_guidance",
    "weak_evidence",
    "should_have_required_human_review",
    "should_not_have_required_human_review",
    "recommendation_not_actionable",
    "provider_or_format_issue",
)


class TriageReviewRecord(BaseModel):
    incident_id: str
    case_label: str
    incident_text_hash: str
    outcome: ReviewOutcome
    reason_tags: list[ReviewReason] = Field(default_factory=list)
    reviewer_note: str = ""
    predicted_category: Category
    corrected_category: Category
    predicted_severity: Severity
    corrected_severity: Severity
    predicted_route: str
    predicted_review_status: str
    source_runbooks: list[str] = Field(default_factory=list)
    proposed_runbook_update: str = ""
    promote_to_eval: bool = False
    model: str
    workflow_version: str
    created_at: str


@dataclass
class ReviewSummary:
    total_reviews: int
    outcome_counts: Counter[str]
    reason_counts: Counter[str]
    category_corrections: int
    severity_corrections: int
    missing_runbook_guidance: int
    human_review_routing_concerns: int
    proposed_updates: int
    promoted_eval_candidates: int


def incident_fingerprint(incident_text: str) -> str:
    return hashlib.sha256(incident_text.encode("utf-8")).hexdigest()[:16]


def create_review_record(
    *,
    run: TriageRun,
    incident_id: str,
    case_label: str,
    incident_text: str,
    outcome: ReviewOutcome,
    reason_tags: list[ReviewReason],
    corrected_category: Category,
    corrected_severity: Severity,
    reviewer_note: str = "",
    proposed_runbook_update: str = "",
    promote_to_eval: bool = False,
) -> TriageReviewRecord:
    analysis = run.analysis
    return TriageReviewRecord(
        incident_id=incident_id,
        case_label=case_label,
        incident_text_hash=incident_fingerprint(incident_text),
        outcome=outcome,
        reason_tags=reason_tags,
        reviewer_note=reviewer_note.strip(),
        predicted_category=analysis.category,
        corrected_category=corrected_category,
        predicted_severity=analysis.severity,
        corrected_severity=corrected_severity,
        predicted_route=analysis.route,
        predicted_review_status=analysis.review_status,
        source_runbooks=list(analysis.source_runbooks),
        proposed_runbook_update=proposed_runbook_update.strip(),
        promote_to_eval=promote_to_eval,
        model=configured_model(),
        workflow_version=analysis.workflow_version,
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def append_review(record: TriageReviewRecord, path: Path = DEFAULT_REVIEW_LOG) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(record.model_dump_json() + "\n")


def load_reviews(path: Path = DEFAULT_REVIEW_LOG) -> list[TriageReviewRecord]:
    if not path.exists():
        return []

    records: list[TriageReviewRecord] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(TriageReviewRecord.model_validate_json(stripped))
            except (ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid review log record at {path}:{line_number}") from exc
    return records


def summarize_reviews(reviews: list[TriageReviewRecord]) -> ReviewSummary:
    reason_counts: Counter[str] = Counter()
    for review in reviews:
        reason_counts.update(review.reason_tags)

    return ReviewSummary(
        total_reviews=len(reviews),
        outcome_counts=Counter(review.outcome for review in reviews),
        reason_counts=reason_counts,
        category_corrections=sum(review.predicted_category != review.corrected_category for review in reviews),
        severity_corrections=sum(review.predicted_severity != review.corrected_severity for review in reviews),
        missing_runbook_guidance=reason_counts["missing_runbook_guidance"],
        human_review_routing_concerns=reason_counts["should_have_required_human_review"]
        + reason_counts["should_not_have_required_human_review"],
        proposed_updates=sum(bool(review.proposed_runbook_update) for review in reviews),
        promoted_eval_candidates=sum(review.promote_to_eval for review in reviews),
    )


def render_review_report(reviews: list[TriageReviewRecord], source_path: Path = DEFAULT_REVIEW_LOG) -> str:
    summary = summarize_reviews(reviews)
    lines = [
        "# Review Learning Report",
        "",
        f"Source: `{source_path}`",
        f"Reviews analyzed: **{summary.total_reviews}**",
        "",
        "## Summary",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        f"| Accepted | {summary.outcome_counts['accepted']} |",
        f"| Edited | {summary.outcome_counts['edited']} |",
        f"| Rejected | {summary.outcome_counts['rejected']} |",
        f"| Category corrections | {summary.category_corrections} |",
        f"| Severity corrections | {summary.severity_corrections} |",
        f"| Missing runbook guidance flags | {summary.missing_runbook_guidance} |",
        f"| Human-review routing concerns | {summary.human_review_routing_concerns} |",
        f"| Proposed runbook updates | {summary.proposed_updates} |",
        f"| Promoted eval candidates | {summary.promoted_eval_candidates} |",
    ]

    if summary.reason_counts:
        lines.extend(["", "## Top Feedback Reasons", "", "| Reason | Count |", "| --- | ---: |"])
        for reason, count in summary.reason_counts.most_common():
            lines.append(f"| {reason} | {count} |")

    updates = [review for review in reviews if review.proposed_runbook_update]
    if updates:
        lines.extend(["", "## Proposed Runbook Updates", ""])
        for review in updates:
            lines.append(f"- `{review.incident_id}` ({review.corrected_category}): {review.proposed_runbook_update}")

    eval_candidates = [review for review in reviews if review.promote_to_eval]
    if eval_candidates:
        lines.extend(["", "## Candidate Evaluation Cases", ""])
        for review in eval_candidates:
            lines.append(
                f"- `{review.incident_id}`: {review.outcome}; "
                f"{review.predicted_category}/{review.predicted_severity} -> "
                f"{review.corrected_category}/{review.corrected_severity}"
            )

    if not reviews:
        lines.extend(
            [
                "",
                "## Next Step",
                "",
                "Run triage in the Streamlit app, save reviewer feedback, then rerun this report.",
            ]
        )

    return "\n".join(lines) + "\n"

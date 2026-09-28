import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

from app.triage.workflow import TriageRun, triage_incident_with_context

DEFAULT_DATASET = Path("data/incidents/heldout_cases.jsonl")
DEFAULT_REPORT = Path("reports/evaluation_report.md")
DEFAULT_LIMIT = 3


@dataclass
class EvaluationRow:
    incident_id: str
    title: str
    expected_category: str
    actual_category: str
    category_match: bool
    expected_severity: str
    actual_severity: str
    severity_match: bool
    expected_runbook: str
    source_runbooks: list[str]
    runbook_match: bool
    expected_human_review: bool
    actual_human_review: bool
    review_match: bool
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    provider_error: str | None


@dataclass
class EvaluationSummary:
    total_cases: int
    category_accuracy: float
    severity_accuracy: float
    runbook_match_rate: float
    review_routing_accuracy: float
    provider_error_count: int
    average_latency_ms: float
    median_latency_ms: float
    total_input_tokens: int | None
    total_output_tokens: int | None


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                cases.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return cases


def incident_text(case: dict[str, Any]) -> str:
    title = str(case.get("title", "")).strip()
    description = str(case.get("description", "")).strip()
    return f"{title}\n\n{description}".strip()


def is_human_review(run: TriageRun) -> bool:
    analysis = run.analysis
    return analysis.review_status == "human_review_required" or analysis.route == "human_review"


def normalize_runbook(name: str) -> str:
    return Path(name).name.lower()


def evaluate_case(case: dict[str, Any]) -> EvaluationRow:
    run = triage_incident_with_context(incident_text(case))
    analysis = run.analysis
    model_result = run.model_result

    expected_runbook = str(case["expected_runbook"])
    source_runbooks = list(analysis.source_runbooks)
    normalized_sources = {normalize_runbook(name) for name in source_runbooks}
    expected_human_review = bool(case.get("should_escalate", False))
    actual_human_review = is_human_review(run)

    return EvaluationRow(
        incident_id=str(case["incident_id"]),
        title=str(case["title"]),
        expected_category=str(case["expected_category"]),
        actual_category=analysis.category,
        category_match=analysis.category == case["expected_category"],
        expected_severity=str(case["expected_severity"]),
        actual_severity=analysis.severity,
        severity_match=analysis.severity == case["expected_severity"],
        expected_runbook=expected_runbook,
        source_runbooks=source_runbooks,
        runbook_match=normalize_runbook(expected_runbook) in normalized_sources,
        expected_human_review=expected_human_review,
        actual_human_review=actual_human_review,
        review_match=expected_human_review == actual_human_review,
        latency_ms=run.total_latency_ms,
        input_tokens=model_result.input_tokens if model_result else None,
        output_tokens=model_result.output_tokens if model_result else None,
        provider_error=model_result.error if model_result else None,
    )


def evaluate_cases(cases: list[dict[str, Any]], limit: int | None) -> list[EvaluationRow]:
    selected_cases = cases if limit is None else cases[:limit]
    return [evaluate_case(case) for case in selected_cases]


def ratio(matches: int, total: int) -> float:
    return matches / total if total else 0.0


def sum_known(values: list[int | None]) -> int | None:
    known = [value for value in values if value is not None]
    return sum(known) if known else None


def score_rows(rows: list[EvaluationRow]) -> EvaluationSummary:
    total = len(rows)
    latencies = [row.latency_ms for row in rows]
    return EvaluationSummary(
        total_cases=total,
        category_accuracy=ratio(sum(row.category_match for row in rows), total),
        severity_accuracy=ratio(sum(row.severity_match for row in rows), total),
        runbook_match_rate=ratio(sum(row.runbook_match for row in rows), total),
        review_routing_accuracy=ratio(sum(row.review_match for row in rows), total),
        provider_error_count=sum(row.provider_error is not None for row in rows),
        average_latency_ms=sum(latencies) / total if total else 0.0,
        median_latency_ms=median(latencies) if latencies else 0.0,
        total_input_tokens=sum_known([row.input_tokens for row in rows]),
        total_output_tokens=sum_known([row.output_tokens for row in rows]),
    )


def percent(value: float) -> str:
    return f"{value:.0%}"


def token_text(value: int | None) -> str:
    return str(value) if value is not None else "not reported"


def bool_mark(value: bool) -> str:
    return "yes" if value else "no"


def render_markdown(summary: EvaluationSummary, rows: list[EvaluationRow], dataset: Path) -> str:
    lines = [
        "# Evaluation Report",
        "",
        f"Dataset: `{dataset}`",
        f"Cases evaluated: **{summary.total_cases}**",
        "",
        "## Summary",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        f"| Category accuracy | {percent(summary.category_accuracy)} |",
        f"| Severity accuracy | {percent(summary.severity_accuracy)} |",
        f"| Runbook match rate | {percent(summary.runbook_match_rate)} |",
        f"| Review routing accuracy | {percent(summary.review_routing_accuracy)} |",
        f"| Provider errors | {summary.provider_error_count} |",
        f"| Average latency | {summary.average_latency_ms:.0f} ms |",
        f"| Median latency | {summary.median_latency_ms:.0f} ms |",
        f"| Input tokens | {token_text(summary.total_input_tokens)} |",
        f"| Output tokens | {token_text(summary.total_output_tokens)} |",
        "",
        "## Case Results",
        "",
        (
            "| ID | Expected Category | Actual Category | Severity | Runbook | "
            "Review Route | Latency |"
        ),
        "| --- | --- | --- | --- | --- | --- | ---: |",
    ]

    for row in rows:
        severity = f"{row.expected_severity} -> {row.actual_severity}"
        runbook = f"{row.expected_runbook} -> {', '.join(row.source_runbooks) or 'none'}"
        review = f"{bool_mark(row.expected_human_review)} -> {bool_mark(row.actual_human_review)}"
        lines.append(
            f"| {row.incident_id} | {row.expected_category} | {row.actual_category} | "
            f"{severity} | {runbook} | {review} | {row.latency_ms} ms |"
        )

    errors = [row for row in rows if row.provider_error]
    if errors:
        lines.extend(["", "## Provider Errors", ""])
        for row in errors:
            lines.append(f"- `{row.incident_id}`: {row.provider_error}")

    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate held-out incident triage cases.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Number of cases to evaluate. Defaults to 3 to limit API spend.",
    )
    parser.add_argument("--all", action="store_true", help="Evaluate every held-out case.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.limit is not None and args.limit < 1:
        raise ValueError("--limit must be at least 1")

    cases = load_cases(args.dataset)
    limit = None if args.all else args.limit
    rows = evaluate_cases(cases, limit)
    summary = score_rows(rows)
    report = render_markdown(summary, rows, args.dataset)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote evaluation report to {args.output}")


if __name__ == "__main__":
    main()

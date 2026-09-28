import json
from dataclasses import dataclass
from time import perf_counter

from pydantic import ValidationError

from app.triage.execution import ModelResult, call_model
from app.triage.retrieval import retrieve_runbooks
from app.triage.schemas import IncidentAnalysis


@dataclass
class TriageRun:
    analysis: IncidentAnalysis
    retrieved_sources: list[dict[str, str]]
    model_result: ModelResult | None
    total_latency_ms: int
    prompt: str


def build_prompt(incident_text: str, sources: list[dict[str, str]]) -> str:
    source_blocks = "\n\n".join(
        f"Source: {source['name']}\n"
        f"Relevant section: {source.get('heading', 'Runbook')}\n"
        f"Snippet: {source['snippet']}"
        for source in sources
    )
    return (
        "You are triaging a synthetic data-pipeline incident.\n"
        "Use only the approved runbook snippets below.\n"
        "Return structured JSON matching the IncidentAnalysis schema.\n\n"
        f"Incident:\n{incident_text}\n\n"
        f"Approved runbook evidence:\n{source_blocks or 'No relevant runbook evidence found.'}\n"
    )


def human_review_result(
    *,
    summary: str,
    recommendation: str,
    route_reason: str,
    sources: list[dict[str, str]] | None = None,
) -> IncidentAnalysis:
    return IncidentAnalysis(
        category="unknown",
        severity="unknown",
        summary=summary,
        evidence=[],
        recommendation=recommendation,
        source_runbooks=[source["name"] for source in sources or []],
        route="human_review",
        route_reason=route_reason,
        review_status="human_review_required",
    )


def triage_incident_with_context(incident_text: str) -> TriageRun:
    start = perf_counter()
    prompt = ""

    if not incident_text.strip():
        analysis = human_review_result(
            summary="No incident text was provided.",
            recommendation="Provide an incident description before triage.",
            route_reason="Empty input.",
        )
        return TriageRun(
            analysis=analysis,
            retrieved_sources=[],
            model_result=None,
            total_latency_ms=int((perf_counter() - start) * 1000),
            prompt=prompt,
        )

    sources = retrieve_runbooks(incident_text, limit=3)
    prompt = build_prompt(incident_text, sources)
    model_result = call_model(prompt)

    try:
        payload = json.loads(model_result.text)
        analysis = IncidentAnalysis.model_validate(payload)
    except (json.JSONDecodeError, ValidationError):
        analysis = human_review_result(
            summary="Model output could not be validated.",
            recommendation="Route this incident to human review.",
            route_reason="Invalid structured output.",
            sources=sources,
        )
    else:
        if not analysis.source_runbooks and sources:
            analysis.source_runbooks = [source["name"] for source in sources]
        if not sources and analysis.review_status == "approved":
            analysis.review_status = "human_review_required"
            analysis.route = "human_review"
            analysis.route_reason = "No approved runbook evidence was retrieved."

    return TriageRun(
        analysis=analysis,
        retrieved_sources=sources,
        model_result=model_result,
        total_latency_ms=int((perf_counter() - start) * 1000),
        prompt=prompt,
    )


def triage_incident(incident_text: str) -> IncidentAnalysis:
    return triage_incident_with_context(incident_text).analysis

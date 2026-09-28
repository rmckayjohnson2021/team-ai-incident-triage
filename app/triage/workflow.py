import json

from pydantic import ValidationError

from app.triage.execution import call_model
from app.triage.retrieval import retrieve_runbooks
from app.triage.schemas import IncidentAnalysis


def triage_incident(incident_text: str) -> IncidentAnalysis:
    if not incident_text.strip():
        return IncidentAnalysis(
            category="unknown",
            severity="unknown",
            summary="No incident text was provided.",
            evidence=[],
            recommendation="Provide an incident description before triage.",
            source_runbooks=[],
            route="human_review",
            route_reason="Empty input.",
            review_status="human_review_required",
        )

    sources = retrieve_runbooks(incident_text)
    prompt = f"Incident:\n{incident_text}\n\nRunbooks:\n{sources}\n"
    result = call_model(prompt)

    try:
        payload = json.loads(result.text)
        analysis = IncidentAnalysis.model_validate(payload)
    except (json.JSONDecodeError, ValidationError):
        return IncidentAnalysis(
            category="unknown",
            severity="unknown",
            summary="Model output could not be validated.",
            evidence=[],
            recommendation="Route this incident to human review.",
            source_runbooks=[source["name"] for source in sources],
            route="human_review",
            route_reason="Invalid structured output.",
            review_status="human_review_required",
        )

    if not analysis.source_runbooks and sources:
        analysis.source_runbooks = [source["name"] for source in sources]

    return analysis

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "failed_import",
    "duplicate_records",
    "schema_change",
    "stale_dashboard",
    "ambiguous_outage",
    "unknown",
]

Severity = Literal["sev1", "sev2", "sev3", "sev4", "unknown"]
Route = Literal["strong_model", "fast_model", "human_review"]
ReviewStatus = Literal["approved", "human_review_required"]


class IncidentAnalysis(BaseModel):
    category: Category
    severity: Severity
    summary: str
    evidence: list[str] = Field(default_factory=list)
    recommendation: str
    source_runbooks: list[str] = Field(default_factory=list)
    route: Route = "strong_model"
    route_reason: str
    review_status: ReviewStatus
    workflow_version: str = "v1.0.0"

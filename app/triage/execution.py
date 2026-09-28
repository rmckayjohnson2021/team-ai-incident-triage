from dataclasses import dataclass
from time import perf_counter


@dataclass
class ModelResult:
    text: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None


def call_model(prompt: str, model: str = "placeholder") -> ModelResult:
    start = perf_counter()
    # Replace this placeholder with a provider call after the local workflow works.
    text = '{"category":"unknown","severity":"unknown","summary":"Provider not configured.","evidence":[],"recommendation":"Route to human review until provider is configured.","source_runbooks":[],"route":"human_review","route_reason":"Provider placeholder response.","review_status":"human_review_required","workflow_version":"v1.0.0"}'
    return ModelResult(text=text, latency_ms=int((perf_counter() - start) * 1000))

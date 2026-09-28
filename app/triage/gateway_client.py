import os
import sys
from pathlib import Path

from app.triage.execution import ModelResult, fallback_payload, truncate

PLACEHOLDER_VALUES = {"", "replace_me", "your_openai_api_key_here"}
DEFAULT_GATEWAY_PATH = Path("C:/Dev/repos/llm-cost-eval-gateway")


def gateway_repo_path() -> Path:
    configured = os.getenv("GATEWAY_REPO_PATH", "").strip()
    return Path(configured) if configured and configured not in PLACEHOLDER_VALUES else DEFAULT_GATEWAY_PATH


def gateway_route_policy() -> str:
    return os.getenv("GATEWAY_ROUTE_POLICY", "routed").strip() or "routed"


def gateway_ledger_path() -> str | None:
    value = os.getenv("GATEWAY_LEDGER_PATH", "").strip()
    return value or None


def ensure_gateway_import_path() -> None:
    path = gateway_repo_path()
    if not path.exists():
        raise RuntimeError(f"Gateway repo path does not exist: {path}")
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


def call_gateway(prompt: str, model: str | None = None) -> ModelResult:
    try:
        ensure_gateway_import_path()
        from gateway.executor import execute
        from gateway.schemas import ModelRequest

        request = ModelRequest(
            app_name="runbookops-ai",
            workflow_version="v1.0.0",
            simulated_user_id="local-demo-user",
            simulated_team_id="local-demo-team",
            input_text=prompt,
            max_output_tokens=2000,
            route_policy=gateway_route_policy(),
            metadata={"requested_model": model or ""},
        )
        response = execute(request, ledger_path=gateway_ledger_path())
    except (ImportError, RuntimeError, ValueError) as exc:
        detail = truncate(str(exc).replace("\n", " ").strip() or type(exc).__name__)
        return ModelResult(
            text=fallback_payload(
                f"Gateway call failed: {detail}",
                "Route this incident to human review and verify the local gateway configuration.",
            ),
            latency_ms=0,
            error=type(exc).__name__,
            error_detail=detail,
        )

    if response.status != "success":
        detail = response.error_type or response.route_reason
        return ModelResult(
            text=fallback_payload(
                f"Gateway returned {response.status}: {detail}",
                "Route this incident to human review and inspect gateway routing, budget, or provider configuration.",
            ),
            latency_ms=response.latency_ms,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            error=response.error_type or response.status,
            error_detail=response.route_reason,
        )

    return ModelResult(
        text=response.text,
        latency_ms=response.latency_ms,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )

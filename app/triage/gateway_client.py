import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.triage.execution import ModelResult, fallback_payload, truncate

PLACEHOLDER_VALUES = {"", "replace_me", "your_openai_api_key_here", "your_gateway_api_key_here"}
DEFAULT_GATEWAY_PATH = Path("C:/Dev/repos/llm-cost-eval-gateway")
DEFAULT_GATEWAY_BASE_URL = "http://127.0.0.1:8600"
DEFAULT_GATEWAY_API_KEY = "local-dev-key"


def gateway_repo_path() -> Path:
    configured = os.getenv("GATEWAY_REPO_PATH", "").strip()
    return Path(configured) if configured and configured not in PLACEHOLDER_VALUES else DEFAULT_GATEWAY_PATH


def gateway_base_url() -> str:
    configured = os.getenv("GATEWAY_BASE_URL", DEFAULT_GATEWAY_BASE_URL).strip()
    value = configured if configured not in PLACEHOLDER_VALUES else DEFAULT_GATEWAY_BASE_URL
    return value.rstrip("/")


def gateway_api_key() -> str:
    configured = os.getenv("GATEWAY_API_KEY", DEFAULT_GATEWAY_API_KEY).strip()
    return configured if configured not in PLACEHOLDER_VALUES else DEFAULT_GATEWAY_API_KEY


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


def gateway_request_payload(prompt: str, model: str | None = None, routing_text: str | None = None) -> dict[str, object]:
    return {
        "app_name": "runbookops-ai",
        "workflow_version": "v1.0.0",
        "simulated_user_id": "local-demo-user",
        "simulated_team_id": "local-demo-team",
        "input_text": prompt,
        "max_output_tokens": 2000,
        "route_policy": gateway_route_policy(),
        "metadata": {"requested_model": model or "", "routing_text": routing_text or ""},
    }


def model_result_from_gateway_response(response: Any) -> ModelResult:
    status = response.status
    if status != "success":
        detail = getattr(response, "error_type", None) or getattr(response, "route_reason", "")
        return ModelResult(
            text=fallback_payload(
                f"Gateway returned {status}: {detail}",
                "Route this incident to human review and inspect gateway routing, budget, or provider configuration.",
            ),
            latency_ms=getattr(response, "latency_ms", 0),
            input_tokens=getattr(response, "input_tokens", None),
            output_tokens=getattr(response, "output_tokens", None),
            error=getattr(response, "error_type", None) or status,
            error_detail=getattr(response, "route_reason", ""),
        )

    return ModelResult(
        text=response.text,
        latency_ms=getattr(response, "latency_ms", 0),
        input_tokens=getattr(response, "input_tokens", None),
        output_tokens=getattr(response, "output_tokens", None),
    )


def call_gateway_http(prompt: str, model: str | None = None, routing_text: str | None = None) -> ModelResult:
    payload = json.dumps(gateway_request_payload(prompt, model, routing_text)).encode("utf-8")
    request = urllib.request.Request(
        f"{gateway_base_url()}/v1/execute",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Gateway-API-Key": gateway_api_key(),
        },
        method="POST",
    )
    timeout = float(os.getenv("GATEWAY_HTTP_TIMEOUT_SECONDS", "10"))

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = truncate(exc.read().decode("utf-8", errors="replace") or str(exc))
        return ModelResult(
            text=fallback_payload(
                f"Gateway HTTP call failed with status {exc.code}: {detail}",
                "Route this incident to human review and verify the gateway API key and service configuration.",
            ),
            latency_ms=0,
            error="GatewayHttpError",
            error_detail=detail,
        )
    except (OSError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"Gateway HTTP service is unavailable at {gateway_base_url()}: {exc}") from exc

    class Response:
        def __init__(self, values: dict[str, object]) -> None:
            self.__dict__.update(values)

    return model_result_from_gateway_response(Response(response_payload))


def call_gateway_local(prompt: str, model: str | None = None, routing_text: str | None = None) -> ModelResult:
    try:
        ensure_gateway_import_path()
        from gateway.executor import execute
        from gateway.schemas import ModelRequest

        request = ModelRequest(**gateway_request_payload(prompt, model, routing_text))
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

    return model_result_from_gateway_response(response)


def call_gateway(prompt: str, model: str | None = None, routing_text: str | None = None) -> ModelResult:
    try:
        return call_gateway_http(prompt, model, routing_text)
    except RuntimeError:
        return call_gateway_local(prompt, model, routing_text)

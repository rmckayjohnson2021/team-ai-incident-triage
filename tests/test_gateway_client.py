import json
import textwrap

from app.triage.gateway_client import call_gateway


def write_fake_gateway(root):
    gateway_dir = root / "gateway"
    gateway_dir.mkdir()
    (gateway_dir / "__init__.py").write_text("", encoding="utf-8")
    (gateway_dir / "schemas.py").write_text(
        textwrap.dedent(
            """
            class ModelRequest:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
            """
        ),
        encoding="utf-8",
    )
    (gateway_dir / "executor.py").write_text(
        textwrap.dedent(
            """
            class Response:
                status = "success"
                text = '{"category":"schema_change","severity":"sev2","summary":"ok","evidence":[],"recommendation":"ok","source_runbooks":[],"route":"strong_model","route_reason":"ok","review_status":"approved","workflow_version":"v1.0.0"}'
                latency_ms = 11
                input_tokens = 22
                output_tokens = 33
                error_type = None
                route_reason = "ok"

            def execute(request, ledger_path=None):
                return Response()
            """
        ),
        encoding="utf-8",
    )


def test_call_gateway_maps_successful_response(monkeypatch, tmp_path):
    write_fake_gateway(tmp_path)
    monkeypatch.setenv("GATEWAY_REPO_PATH", str(tmp_path))
    monkeypatch.setenv("GATEWAY_ROUTE_POLICY", "routed")

    result = call_gateway("incident prompt")

    assert result.latency_ms == 11
    assert result.input_tokens == 22
    assert result.output_tokens == 33
    assert json.loads(result.text)["category"] == "schema_change"


def test_call_gateway_returns_fallback_when_gateway_path_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("GATEWAY_REPO_PATH", str(tmp_path / "missing"))

    result = call_gateway("incident prompt")
    payload = json.loads(result.text)

    assert result.error == "RuntimeError"
    assert payload["route"] == "human_review"
    assert payload["review_status"] == "human_review_required"

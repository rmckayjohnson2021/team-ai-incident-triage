import json
import textwrap

from app.triage import gateway_client


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

    result = gateway_client.call_gateway_local("incident prompt")

    assert result.latency_ms == 11
    assert result.input_tokens == 22
    assert result.output_tokens == 33
    assert json.loads(result.text)["category"] == "schema_change"


def test_call_gateway_returns_fallback_when_gateway_path_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("GATEWAY_REPO_PATH", str(tmp_path / "missing"))

    result = gateway_client.call_gateway_local("incident prompt")
    payload = json.loads(result.text)

    assert result.error == "RuntimeError"
    assert payload["route"] == "human_review"
    assert payload["review_status"] == "human_review_required"


def test_call_gateway_http_posts_to_execute_endpoint(monkeypatch):
    monkeypatch.setenv("GATEWAY_BASE_URL", "http://gateway.test")
    monkeypatch.setenv("GATEWAY_API_KEY", "test-key")

    class FakeHttpResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps(
                {
                    "run_id": "run-1",
                    "route": "strong_model",
                    "status": "success",
                    "provider": "mock",
                    "model": "mock-strong",
                    "text": '{"category":"schema_change"}',
                    "route_reason": "ok",
                    "attempts": 1,
                    "input_tokens": 44,
                    "output_tokens": 55,
                    "reserved_cost_usd": 0.01,
                    "estimated_cost_usd": 0.001,
                    "latency_ms": 66,
                    "error_type": None,
                }
            ).encode("utf-8")

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = request.headers
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeHttpResponse()

    monkeypatch.setattr(gateway_client.urllib.request, "urlopen", fake_urlopen)

    result = gateway_client.call_gateway_http("incident prompt", routing_text="raw incident")

    assert result.latency_ms == 66
    assert result.input_tokens == 44
    assert captured["url"] == "http://gateway.test/v1/execute"
    assert captured["headers"]["X-gateway-api-key"] == "test-key"
    assert captured["payload"]["metadata"]["routing_text"] == "raw incident"

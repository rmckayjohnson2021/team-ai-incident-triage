import json

from app.triage import execution


def test_call_model_returns_human_review_when_key_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = execution.call_model("incident text")
    payload = json.loads(result.text)

    assert result.error == "missing_api_key"
    assert result.error_detail
    assert payload["route"] == "human_review"
    assert payload["review_status"] == "human_review_required"


def test_call_model_uses_responses_api(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("DEFAULT_STRONG_MODEL", "test-model")

    class FakeUsage:
        input_tokens = 12
        output_tokens = 34

    class FakeResponse:
        output_text = json.dumps(
            {
                "category": "schema_change",
                "severity": "sev2",
                "summary": "The source schema changed.",
                "evidence": ["unexpected column"],
                "recommendation": "Validate the schema mapping and rerun after review.",
                "source_runbooks": ["schema_change.md"],
                "route": "strong_model",
                "route_reason": "Schema validation failed.",
                "review_status": "approved",
                "workflow_version": "v1.0.0",
            }
        )
        usage = FakeUsage()

    class FakeResponses:
        def __init__(self):
            self.kwargs = None

        def create(self, **kwargs):
            self.kwargs = kwargs
            return FakeResponse()

    class FakeClient:
        responses = FakeResponses()

        def __init__(self, api_key):
            self.api_key = api_key

    monkeypatch.setattr(execution, "OpenAI", FakeClient)

    result = execution.call_model("incident prompt")
    payload = json.loads(result.text)

    assert payload["category"] == "schema_change"
    assert result.input_tokens == 12
    assert result.output_tokens == 34
    assert FakeClient.responses.kwargs["model"] == "test-model"
    assert FakeClient.responses.kwargs["max_output_tokens"] == 2000
    assert FakeClient.responses.kwargs["text"]["format"]["type"] == "json_schema"


def test_call_model_returns_sanitized_provider_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-test-key")
    monkeypatch.setenv("DEFAULT_STRONG_MODEL", "test-model")

    class FakeResponses:
        def create(self, **kwargs):
            raise ValueError("bad request with secret-test-key")

    class FakeClient:
        responses = FakeResponses()

        def __init__(self, api_key):
            self.api_key = api_key

    monkeypatch.setattr(execution, "OpenAI", FakeClient)

    result = execution.call_model("incident prompt")
    payload = json.loads(result.text)

    assert result.error == "ValueError"
    assert "secret-test-key" not in result.error_detail
    assert "[redacted_api_key]" in result.error_detail
    assert payload["route_reason"].startswith("Provider call failed for model test-model")


def test_extract_response_text_handles_dict_content():
    class FakeItem:
        def __init__(self):
            self.content = [{"type": "output_text", "text": '{"ok": true}'}]

    class FakeResponse:
        def __init__(self):
            self.output_text = None
            self.output = [FakeItem()]

    assert execution.extract_response_text(FakeResponse()) == '{"ok": true}'

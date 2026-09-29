from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_run_triage_keeps_app_visible_after_rerun(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "replace_me")
    monkeypatch.setenv("DEFAULT_STRONG_MODEL", "gpt-5-mini")

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py").run(timeout=30)

    assert not app.exception
    run_button = next(button for button in app.button if button.label == "Run triage")

    run_button.click().run(timeout=30)

    assert not app.exception
    assert "triage_run" in app.session_state.to_dict()
    assert any(button.label == "Rerun triage" for button in app.button)
    assert any(header.value == "RunbookOps AI" for header in app.header)
    assert any(subheader.value == "Review outcome" for subheader in app.subheader)

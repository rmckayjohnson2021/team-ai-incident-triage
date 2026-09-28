from pathlib import Path

from app.triage.workflow import triage_incident


def main() -> None:
    heldout = Path("data/incidents/heldout_cases.jsonl")
    report = Path("reports/evaluation_report.md")
    report.parent.mkdir(exist_ok=True)
    report.write_text(
        "# Evaluation Report\n\n"
        "Starter evaluation placeholder. Replace with held-out evaluation results.\n\n"
        f"Data file: {heldout}\n",
        encoding="utf-8",
    )
    triage_incident("Starter smoke test incident.")


if __name__ == "__main__":
    main()

# Team AI Incident Triage

Repository: https://github.com/rmckayjohnson2021/team-ai-incident-triage

## Overview

Team AI Incident Triage is a local AI workflow app for synthetic data-pipeline incidents. A user submits an incident report, the app retrieves relevant guidance from approved runbooks, classifies the incident, recommends a next step, and marks whether human review is required.

This project demonstrates how to build a practical, reviewable AI workflow for team operations.

## Capability Signal

> I can build a practical AI workflow that turns messy operational text into structured, sourced, reviewable recommendations.

## What It Does

- Accepts synthetic incident reports.
- Retrieves relevant Markdown runbooks.
- Produces structured triage output.
- Cites supporting runbooks.
- Flags uncertain or unsupported cases for human review.
- Evaluates performance on held-out synthetic incidents.

## What It Does Not Do

- It does not execute remediation.
- It does not use real incident data.
- It does not prove production reliability.
- It does not include production authentication or authorization.
- It does not replace human incident owners.

## Tech Stack

- Python
- Streamlit
- Pydantic
- pytest
- Ruff
- Markdown runbooks
- JSONL synthetic incident data

## Project Structure

```text
team-ai-incident-triage/
  app/
    streamlit_app.py
    triage/
      schemas.py
      retrieval.py
      execution.py
      workflow.py
      evaluation.py
  data/
    incidents/
    runbooks/
  reports/
  tests/
```

## Setup

```powershell
uv sync
Copy-Item .env.example .env
```

Edit `.env` and add local values. Do not commit `.env`.

Minimum `.env` values for provider-backed triage:

```env
OPENAI_API_KEY=your_api_key_here
DEFAULT_STRONG_MODEL=gpt-5-mini
```

If `OPENAI_API_KEY` is missing or still set to `replace_me`, the app stays runnable and routes incidents to human review with a clear provider-not-configured status.

## Run the App

```powershell
uv run streamlit run streamlit_app.py
```

## Run Tests

```powershell
uv run pytest
uv run ruff check .
```

## Run Evaluation

```powershell
uv run python -m app.triage.evaluation
```

By default, evaluation runs the first 3 held-out incidents to keep API usage
intentional. To evaluate the full 20-case held-out set:

```powershell
uv run python -m app.triage.evaluation --all
```

The evaluator writes a Markdown report to `reports/evaluation_report.md`. Use
`--limit 5` for a larger sample or `--output reports/my_report.md` for a custom
report path.

## Output Schema

Each result should include:

- category
- severity
- summary
- evidence
- recommendation
- source runbooks
- route
- route reason
- review status
- workflow version

## Demo Scenarios

1. Routine failed import with a sourced recommendation.
2. Ambiguous outage routed to human review.
3. Incident text containing malicious instructions that the workflow ignores.

## Evaluation

The evaluation uses held-out synthetic incidents and reports:

- category accuracy
- severity match
- source/runbook match rate
- recommendation acceptability
- human-review rate
- invalid-output rate
- latency

## Limitations

This is a workflow demonstration using synthetic data. Production use would require:

- real authentication
- server-enforced authorization
- team isolation
- larger evaluation datasets
- monitoring
- incident-owner review
- provider-failure playbooks

## Companion Project

This app is designed to integrate with `llm-cost-eval-gateway`, a reusable gateway for model execution, budget enforcement, routing, retries, and evaluation.

import json
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.triage.workflow import TriageRun, triage_incident_with_context

INCIDENT_DIR = PROJECT_ROOT / "data" / "incidents"
LOGO_PATH = PROJECT_ROOT / "app" / "assets" / "triage_logo.svg"
LOGO_MARK_PATH = PROJECT_ROOT / "app" / "assets" / "triage_mark.svg"
APP_DISPLAY_NAME = "RunbookOps Triage"
APP_TAGLINE = "AI-assisted incident triage console"
OWNER_NAME = "Ryan Johnson"
OWNER_EMAIL = "rmckayjohnson2021@gmail.com"
GITHUB_PROFILE_URL = "https://github.com/rmckayjohnson2021"
REPO_URL = "https://github.com/rmckayjohnson2021/team-ai-incident-triage"
COMPANION_REPO_URL = "https://github.com/rmckayjohnson2021/llm-cost-eval-gateway"

CATEGORY_LABELS = {
    "ambiguous_outage": "Ambiguous outage",
    "duplicate_records": "Duplicate records",
    "failed_import": "Failed import",
    "schema_change": "Schema change",
    "stale_dashboard": "Stale dashboard",
    "unknown": "Unknown",
}

CATEGORY_COLORS = {
    "ambiguous_outage": "orange",
    "duplicate_records": "violet",
    "failed_import": "red",
    "schema_change": "blue",
    "stale_dashboard": "green",
    "unknown": "gray",
}

SEVERITY_COLORS = {
    "sev1": "red",
    "sev2": "orange",
    "sev3": "yellow",
    "sev4": "green",
    "unknown": "gray",
}

REVIEW_BADGES = {
    "approved": ("Approved", ":material/check_circle:", "green"),
    "human_review_required": ("Human review", ":material/rate_review:", "orange"),
}

HELP_TEXT = {
    "retrieval_augmented": "The app retrieves relevant approved runbook snippets before asking the model to classify the incident.",
    "structured_output": "The model response is validated against a Pydantic schema so the workflow can be tested and evaluated.",
    "evaluation_ready": "Held-out incidents can be scored with the evaluation runner to measure category, severity, runbook, and routing quality.",
    "synthetic_data": "All examples are generated demo records. No real customer or production incident data is used.",
    "human_loop": "Unclear, risky, unsupported, or provider-failed cases are routed to human review instead of auto-approval.",
    "runbook_grounded": "Recommendations should be based on retrieved Markdown runbooks, not unsupported model guesses.",
    "sample_incident": "Choose a synthetic scenario. Changing this field does not call the model until you click Run triage.",
    "incident_report": "Edit the incident text to test how the workflow handles messy operational language and missing details.",
    "expected_label": "Ground-truth labels are shown for review and evaluation, not given to the model prompt.",
    "run_triage": "Retrieves runbooks, builds the prompt, calls the configured model, validates JSON output, and displays the decision.",
    "triage_decision": "The top-level decision shows whether the result was approved or should be reviewed by a human.",
    "category": "The model-selected incident type, normalized to one of the runbook categories.",
    "severity": "The model-assigned operational severity from SEV1 to SEV4, or Unknown when evidence is insufficient.",
    "total_latency": "End-to-end workflow time, including retrieval, prompt construction, model call, and validation.",
    "model_latency": "Provider call latency only. This excludes local retrieval and UI rendering.",
    "referenced_runbooks": "Runbooks the model cited as sources for its decision. These should align with retrieved evidence.",
    "evidence": "Specific facts from the incident or runbook snippets used to justify the recommendation.",
    "provider_diagnostic": "A safe diagnostic shown when the model provider is unavailable or returns invalid output.",
    "recommendation": "The operational next step proposed by the workflow. It should be concrete, scoped, and runbook-grounded.",
    "summary": "A concise restatement of the incident in normalized operational language.",
    "route_reason": "Why the workflow chose the route, such as strong model approval or human review.",
    "retrieved_evidence": "The retrieval layer's ranked snippets before model reasoning. Use this to debug grounding quality.",
    "structured_output_panel": "The validated JSON object produced by the workflow for tests, logging, and evaluation.",
    "prompt_preview": "The prompt sent to the model, including incident text and approved runbook snippets.",
    "sample_metadata": "Metadata for the selected synthetic case, useful during demos and held-out evaluation review.",
    "project_artifact": "Project context: what the workflow demonstrates and where to inspect the source.",
}


@st.cache_data
def load_incidents() -> list[dict[str, str]]:
    cases: list[dict[str, str]] = []
    for split, filename in (("Development", "dev_cases.jsonl"), ("Held-out", "heldout_cases.jsonl")):
        path = INCIDENT_DIR / filename
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                record["split"] = split
                cases.append(record)
    return cases


def case_label(case: dict[str, str]) -> str:
    return f"{case['split']} | {case['incident_id']} | {case['title']}"


def split_count(cases: list[dict[str, str]], split: str) -> int:
    return sum(case["split"] == split for case in cases)


def category_coverage(cases: list[dict[str, str]]) -> str:
    categories = {case["expected_category"] for case in cases}
    return f"{len(categories)}/5"


def render_badge(label: str, *, icon: str | None = None, color: str = "blue", help: str | None = None) -> None:
    st.badge(label, icon=icon, color=color, help=help)


def render_status_badges(run: TriageRun) -> None:
    analysis = run.analysis
    status_label, status_icon, status_color = REVIEW_BADGES.get(
        analysis.review_status,
        ("Unknown", ":material/help:", "gray"),
    )

    with st.container(horizontal=True, gap="small", vertical_alignment="center"):
        render_badge(
            status_label,
            icon=status_icon,
            color=status_color,
            help=HELP_TEXT["triage_decision"],
        )
        render_badge(
            CATEGORY_LABELS.get(analysis.category, analysis.category),
            icon=":material/category:",
            color=CATEGORY_COLORS.get(analysis.category, "gray"),
            help=HELP_TEXT["category"],
        )
        render_badge(
            analysis.severity.upper(),
            icon=":material/priority_high:",
            color=SEVERITY_COLORS.get(analysis.severity, "gray"),
            help=HELP_TEXT["severity"],
        )
        render_badge(
            analysis.route.replace("_", " ").title(),
            icon=":material/alt_route:",
            color="primary",
            help=HELP_TEXT["route_reason"],
        )


def render_metric_row(run: TriageRun) -> None:
    analysis = run.analysis
    model_latency = run.model_result.latency_ms if run.model_result else 0
    input_tokens = run.model_result.input_tokens if run.model_result else None
    output_tokens = run.model_result.output_tokens if run.model_result else None

    cols = st.columns(4, gap="medium")
    cols[0].metric(
        "Category",
        CATEGORY_LABELS.get(analysis.category, analysis.category),
        help=HELP_TEXT["category"],
        icon=":material/category:",
        border=True,
    )
    cols[1].metric(
        "Severity",
        analysis.severity.upper(),
        help=HELP_TEXT["severity"],
        icon=":material/priority_high:",
        border=True,
    )
    cols[2].metric(
        "Total latency",
        f"{run.total_latency_ms} ms",
        help=HELP_TEXT["total_latency"],
        icon=":material/timer:",
        border=True,
    )
    cols[3].metric(
        "Model latency",
        f"{model_latency} ms",
        help=HELP_TEXT["model_latency"],
        icon=":material/cloud_sync:",
        border=True,
    )

    token_note = "Token usage not reported by provider."
    if input_tokens is not None or output_tokens is not None:
        token_note = f"Input tokens: {input_tokens or 0} | Output tokens: {output_tokens or 0}"
    st.caption(token_note)


def render_retrieved_sources(run: TriageRun) -> None:
    if not run.retrieved_sources:
        st.caption("No approved runbook evidence was retrieved.")
        return

    for source in run.retrieved_sources:
        with st.container(border=True):
            top = st.columns([0.58, 0.27, 0.15], vertical_alignment="center")
            top[0].markdown(f"**:material/article: {source['name']}**")
            top[1].caption(source.get("heading", "Runbook"))
            top[2].caption(f"Score {source.get('score', '0')}")
            st.markdown(source["snippet"])
            matched_terms = source.get("matched_terms")
            if matched_terms:
                st.caption(f"Matched terms: {matched_terms}")


def render_reference_panel(run: TriageRun) -> None:
    analysis = run.analysis

    with st.container(border=True):
        st.subheader(
            "Referenced runbooks",
            icon=":material/folder_copy:",
            help=HELP_TEXT["referenced_runbooks"],
        )
        if analysis.source_runbooks:
            for runbook in analysis.source_runbooks:
                st.badge(
                    runbook,
                    icon=":material/article:",
                    color="green",
                    help="A cited approved runbook used by the model response.",
                )
        else:
            st.caption("No runbooks were cited by the model response.")

    with st.container(border=True):
        st.subheader("Evidence", icon=":material/fact_check:", help=HELP_TEXT["evidence"])
        if analysis.evidence:
            for item in analysis.evidence:
                st.markdown(f"- {item}")
        else:
            st.caption("No evidence was returned by the model response.")

    if run.model_result and run.model_result.error:
        with st.container(border=True):
            st.subheader(
                "Provider diagnostic",
                icon=":material/error:",
                help=HELP_TEXT["provider_diagnostic"],
            )
            st.badge(
                run.model_result.error,
                icon=":material/warning:",
                color="red",
                help=HELP_TEXT["provider_diagnostic"],
            )
            if run.model_result.error_detail:
                st.caption(run.model_result.error_detail)


def render_result(run: TriageRun) -> None:
    with st.container(border=True):
        st.subheader("Triage decision", icon=":material/analytics:", help=HELP_TEXT["triage_decision"])
        render_status_badges(run)
        render_metric_row(run)

    left, right = st.columns([0.58, 0.42], gap="large")

    with left:
        with st.container(border=True):
            st.subheader("Recommendation", icon=":material/task_alt:", help=HELP_TEXT["recommendation"])
            st.markdown(run.analysis.recommendation)

        with st.container(border=True):
            st.subheader("Incident summary", icon=":material/summarize:", help=HELP_TEXT["summary"])
            st.markdown(run.analysis.summary)

        with st.container(border=True):
            st.subheader("Route reason", icon=":material/route:", help=HELP_TEXT["route_reason"])
            st.markdown(run.analysis.route_reason)

    with right:
        render_reference_panel(run)

    tab_sources, tab_raw, tab_prompt = st.tabs(
        [
            ":material/search: Retrieved evidence",
            ":material/data_object: Structured output",
            ":material/code: Prompt preview",
        ]
    )
    with tab_sources:
        render_retrieved_sources(run)
    with tab_raw:
        st.json(run.analysis.model_dump())
    with tab_prompt:
        st.code(run.prompt or "No prompt was built for this run.", language="text")


def render_empty_result(cases: list[dict[str, str]]) -> None:
    with st.container(border=True):
        st.subheader(
            "Awaiting triage",
            icon=":material/pending:",
            help="Run triage to populate this side with model-backed analysis and retrieved evidence.",
        )
        st.caption(
            "No active triage result is loaded for this session. The decision panel will populate after a run."
        )

    cols = st.columns(3)
    cols[0].metric("Runbooks", "5", help="Approved Markdown runbooks used by retrieval.", border=True)
    cols[1].metric(
        "Dev cases",
        split_count(cases, "Development"),
        help="Synthetic development cases for iteration and demos.",
        border=True,
    )
    cols[2].metric(
        "Held-out cases",
        split_count(cases, "Held-out"),
        help="Synthetic held-out cases for evaluation.",
        border=True,
    )


def render_sidebar(cases: list[dict[str, str]]) -> None:
    with st.sidebar:
        st.header("Operations console", icon=":material/dashboard:", help="Quick context for reviewers exploring the demo.")
        st.caption(APP_TAGLINE)
        st.badge("Synthetic data only", icon=":material/security:", color="gray", help=HELP_TEXT["synthetic_data"])
        st.badge("Human-in-the-loop", icon=":material/rate_review:", color="orange", help=HELP_TEXT["human_loop"])
        st.badge("Runbook grounded", icon=":material/fact_check:", color="green", help=HELP_TEXT["runbook_grounded"])

        st.subheader("System profile", icon=":material/monitoring:", help="Dataset and workflow coverage at a glance.")
        st.metric(
            "Incident records",
            len(cases),
            help="Total synthetic cases loaded into the app.",
            icon=":material/database:",
            border=True,
        )
        st.metric(
            "Held-out set",
            split_count(cases, "Held-out"),
            help="Cases reserved for evaluation runs.",
            icon=":material/rule:",
            border=True,
        )
        st.metric(
            "Category coverage",
            category_coverage(cases),
            help="Expected-label coverage across the five runbook categories.",
            icon=":material/hub:",
            border=True,
        )

        st.subheader("Evaluation", icon=":material/query_stats:", help=HELP_TEXT["evaluation_ready"])
        with st.expander("Evaluation command", icon=":material/terminal:", expanded=False):
            st.code("uv run python -m app.triage.evaluation", language="powershell")

        st.subheader("Builder", icon=":material/person:", help="Author and source links for reviewers.")
        st.markdown(f"**{OWNER_NAME}**")
        st.caption("AI workflow builder", help="Source links are included for technical review.")
        st.markdown(f"[GitHub]({GITHUB_PROFILE_URL})")
        st.markdown(f"[Repository]({REPO_URL})")


def render_app_header(cases: list[dict[str, str]]) -> None:
    logo_col, title_col = st.columns([0.09, 0.91], vertical_alignment="center")
    logo_col.image(str(LOGO_MARK_PATH), width=64)
    with title_col:
        st.title(APP_DISPLAY_NAME, icon=":material/analytics:")
        st.caption(
            "Operations-grade workflow for sourced recommendations, structured output, and review routing."
        )

    with st.container(horizontal=True, gap="small"):
        st.badge("Retrieval augmented", icon=":material/search:", color="blue", help=HELP_TEXT["retrieval_augmented"])
        st.badge("Structured output", icon=":material/data_object:", color="violet", help=HELP_TEXT["structured_output"])
        st.badge("Evaluation ready", icon=":material/query_stats:", color="green", help=HELP_TEXT["evaluation_ready"])

    status_cols = st.columns(4, gap="medium")
    status_cols[0].metric(
        "Runbooks",
        "5",
        help="Approved operational knowledge sources used for retrieval.",
        icon=":material/folder_copy:",
        border=True,
    )
    status_cols[1].metric(
        "Synthetic cases",
        len(cases),
        help="Development and held-out incidents available in the local dataset.",
        icon=":material/database:",
        border=True,
    )
    status_cols[2].metric(
        "Coverage",
        category_coverage(cases),
        help="Coverage across the five runbook categories.",
        icon=":material/hub:",
        border=True,
    )
    status_cols[3].metric(
        "Execution",
        "Local",
        help="Runs locally with an optional provider-backed model call configured by .env.",
        icon=":material/laptop_windows:",
        border=True,
    )


def render_footer() -> None:
    with st.container(border=True):
        left, right = st.columns([0.48, 0.52], gap="large", vertical_alignment="center")
        with left:
            st.caption("Project artifact", help=HELP_TEXT["project_artifact"])
            st.markdown(f"**{OWNER_NAME}** | [Email](mailto:{OWNER_EMAIL}) | [GitHub]({GITHUB_PROFILE_URL})")
        with right:
            st.caption(
                f"[Source repository]({REPO_URL}) | [Companion gateway]({COMPANION_REPO_URL})",
                text_alignment="right",
            )


st.set_page_config(
    page_title=APP_DISPLAY_NAME,
    page_icon=str(LOGO_MARK_PATH),
    layout="wide",
)

st.logo(
    str(LOGO_PATH),
    size="large",
    link=REPO_URL,
    icon_image=str(LOGO_MARK_PATH),
)

cases = load_incidents()
case_labels = [case_label(case) for case in cases]

render_sidebar(cases)
render_app_header(cases)

input_col, result_col = st.columns([0.38, 0.62], gap="large")

with input_col:
    with st.container(border=True):
        st.subheader(
            "Incident workspace",
            icon=":material/edit_note:",
            help="Choose or edit a synthetic incident before sending it through the triage workflow.",
        )

        with st.form("triage_form", border=False):
            selected_label = st.selectbox(
                "Sample incident",
                case_labels,
                help=HELP_TEXT["sample_incident"],
            )
            selected_case = cases[case_labels.index(selected_label)]
            incident_text = st.text_area(
                "Incident report",
                value=selected_case["description"],
                height=250,
                help=HELP_TEXT["incident_report"],
            )

            with st.expander("Expected label", icon=":material/visibility:", expanded=False):
                st.caption(HELP_TEXT["expected_label"])
                st.markdown(f"**Category:** `{selected_case['expected_category']}`")
                st.markdown(f"**Severity:** `{selected_case['expected_severity']}`")
                st.markdown(f"**Runbook:** `{selected_case['expected_runbook']}`")
                st.markdown(f"**Escalate:** `{selected_case['should_escalate']}`")

            submitted = st.form_submit_button(
                "Run triage",
                type="primary",
                icon=":material/play_arrow:",
                width="stretch",
                help=HELP_TEXT["run_triage"],
            )

    with st.container(border=True):
        st.subheader("Sample metadata", icon=":material/info:", help=HELP_TEXT["sample_metadata"])
        st.badge(
            selected_case["split"],
            icon=":material/dataset:",
            color="primary",
            help="Development cases are for iteration. Held-out cases are reserved for evaluation.",
        )
        st.markdown(f"**Incident:** `{selected_case['incident_id']}`")
        st.caption(selected_case["title"])

if submitted:
    with st.spinner("Retrieving runbooks and calling the model..."):
        st.session_state.triage_run = triage_incident_with_context(incident_text)
        st.session_state.triage_case = selected_label
    st.toast("Triage complete", icon=":material/check_circle:")

with result_col:
    if "triage_run" in st.session_state:
        render_result(st.session_state.triage_run)
    else:
        render_empty_result(cases)

render_footer()

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
LOGO_ICON_PATH = PROJECT_ROOT / "app" / "assets" / "triage_icon.svg"
AUTHOR_IMAGE_PATH = PROJECT_ROOT / "app" / "assets" / "author.jpg"
APP_DISPLAY_NAME = "RunbookOps AI"
APP_TAGLINE = "AI triage engine"
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
    "splash": "This first-use overview introduces the workflow before you enter the triage console.",
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


def incident_log_text(description: str) -> str:
    return (
        "[timestamp] ERROR: Incident signal received.\n"
        f"[timestamp] {description}\n"
        "[timestamp] Awaiting runbook retrieval and triage decision."
    )


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

    cols = st.columns(2, gap="medium")
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
    metric_bottom = st.columns(2, gap="medium")
    metric_bottom[0].metric(
        "Total latency",
        f"{run.total_latency_ms} ms",
        help=HELP_TEXT["total_latency"],
        icon=":material/timer:",
        border=True,
    )
    metric_bottom[1].metric(
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
        st.subheader("AI recommendations", icon=":material/psychology:", help=HELP_TEXT["triage_decision"])
        render_status_badges(run)
        render_metric_row(run)

        st.subheader("Recommendation", icon=":material/task_alt:", help=HELP_TEXT["recommendation"])
        st.markdown(run.analysis.recommendation)

        st.subheader("Route reason", icon=":material/route:", help=HELP_TEXT["route_reason"])
        st.markdown(run.analysis.route_reason)

    with st.container(border=True):
        st.subheader("Incident summary", icon=":material/summarize:", help=HELP_TEXT["summary"])
        st.markdown(run.analysis.summary)

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
        st.subheader("AI recommendations", icon=":material/psychology:")
        st.caption("Preview")
        st.metric("Confidence", "92% match", help="Static preview of the recommendation panel before a live run.", border=True)
        st.progress(0.92, text="RB-102: Schema migration failures")
        st.progress(0.81, text="RB-039: Data pipeline stagnation")

        with st.container(border=True):
            st.markdown("**Awaiting run...**")
            st.caption("The decision panel will populate with real-time analysis after the run.")

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
        st.header(APP_DISPLAY_NAME, icon=":material/library_books:", help="Quick context for reviewers exploring the demo.")
        st.caption(APP_TAGLINE)

        st.subheader("System overview", icon=":material/monitoring:", help="Dataset and workflow coverage at a glance.")
        overview_left, overview_right = st.columns(2)
        overview_left.metric(
            "Records",
            len(cases),
            help="Total synthetic cases loaded into the app.",
            icon=":material/database:",
            border=True,
        )
        overview_right.metric(
            "Held-out",
            split_count(cases, "Held-out"),
            help="Cases reserved for evaluation runs.",
            icon=":material/rule:",
            border=True,
        )
        overview_left.metric(
            "Cases",
            split_count(cases, "Development"),
            help="Development cases available for local iteration.",
            icon=":material/bug_report:",
            border=True,
        )
        overview_right.metric(
            "Coverage",
            category_coverage(cases),
            help="Expected-label coverage across the five runbook categories.",
            icon=":material/hub:",
            border=True,
        )

        st.subheader("Controls", icon=":material/tune:")
        st.toggle("Retrieval augmented", value=True, disabled=True, help=HELP_TEXT["retrieval_augmented"])
        st.toggle("Structured output", value=True, disabled=True, help=HELP_TEXT["structured_output"])
        st.toggle("Evaluation ready", value=True, disabled=True, help=HELP_TEXT["evaluation_ready"])

        st.subheader("Evaluation", icon=":material/query_stats:", help=HELP_TEXT["evaluation_ready"])
        with st.expander("Evaluation command", icon=":material/terminal:", expanded=False):
            st.code("uv run python -m app.triage.evaluation", language="powershell")

        st.subheader("Builder", icon=":material/person:", help="Author and source links for reviewers.")
        author_image, author_text = st.columns([0.28, 0.72], vertical_alignment="center")
        author_image.image(str(AUTHOR_IMAGE_PATH), width=58)
        author_text.markdown(f"**{OWNER_NAME}**")
        author_text.caption("AI workflow builder")
        st.markdown(f"[GitHub]({GITHUB_PROFILE_URL})")
        st.markdown(f"[Repository]({REPO_URL})")


def render_app_header(cases: list[dict[str, str]]) -> None:
    st.header(APP_DISPLAY_NAME, icon=":material/analytics:")
    st.caption(
        f"{APP_TAGLINE} | {len(cases)} synthetic records | {category_coverage(cases)} category coverage"
    )


def render_context_bar(cases: list[dict[str, str]], case_labels: list[str]) -> dict[str, str]:
    with st.container(border=True):
        top_left, top_right = st.columns([0.68, 0.32], gap="large", vertical_alignment="center")
        with top_left:
            selected_label = st.selectbox(
                "Sample incident",
                case_labels,
                help=HELP_TEXT["sample_incident"],
            )
            selected_case = cases[case_labels.index(selected_label)]
            st.caption("Sample incident")
            st.markdown(f"**{selected_case['split']}** {case_label(selected_case)}")
        with top_right:
            meta_left, meta_right = st.columns(2)
            meta_left.caption(f"Metadata: **{selected_case['incident_id']}**")
            meta_left.caption("Time: **5:00 AM PST**")
            meta_right.caption(f"ID: **{selected_case['incident_id']}**")
            meta_right.caption("Status: **Triage pending**")
    return selected_case


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


def render_splash_overlay(cases: list[dict[str, str]]) -> None:
    st.html(
        f"""
        <div id="runbookops-splash" role="dialog" aria-modal="true" aria-labelledby="runbookops-splash-title">
          <div class="runbookops-splash-backdrop"></div>
          <section class="runbookops-splash-panel">
            <button class="runbookops-splash-close" type="button" aria-label="Close splash screen">x</button>
            <div class="runbookops-splash-brand">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" class="runbookops-splash-mark" aria-hidden="true">
                <defs>
                  <linearGradient id="splashGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#00E5FF" />
                    <stop offset="100%" stop-color="#0072FF" />
                  </linearGradient>
                </defs>
                <rect width="100" height="100" rx="20" fill="#0B0F17"/>
                <path d="M 40 6 L 72 18 L 72 54 C 72 70 40 80 40 80 C 40 80 8 70 8 54 L 8 18 Z" fill="none" stroke="url(#splashGrad)" stroke-width="2.5" stroke-opacity="0.35" />
                <path d="M 40 26 C 30 22 20 24 18 26 L 18 58 C 20 56 30 54 40 58 Z" fill="none" stroke="url(#splashGrad)" stroke-width="3" stroke-linejoin="round" />
                <path d="M 40 26 C 50 22 60 24 62 26 L 62 58 C 60 56 50 54 40 58 Z" fill="none" stroke="url(#splashGrad)" stroke-width="3" stroke-linejoin="round" />
                <line x1="40" y1="16" x2="40" y2="68" stroke="#00E5FF" stroke-width="2.5" stroke-dasharray="4 2" />
                <circle cx="40" cy="42" r="5" fill="#00E5FF" />
                <circle cx="28" cy="36" r="2.5" fill="#00E5FF" />
                <circle cx="52" cy="36" r="2.5" fill="#00E5FF" />
              </svg>
              <div>
                <h1 id="runbookops-splash-title">RunbookOps AI</h1>
                <p>AI triage engine</p>
              </div>
            </div>
            <p class="runbookops-splash-copy">
              A runbook-grounded incident triage console for testing retrieval,
              structured model output, and review routing.
            </p>
            <div class="runbookops-splash-metrics" aria-label="Workflow overview">
              <div><span>{len(cases)}</span><strong>Incident records</strong></div>
              <div><span>{split_count(cases, "Held-out")}</span><strong>Held-out cases</strong></div>
              <div><span>{category_coverage(cases)}</span><strong>Coverage</strong></div>
            </div>
            <div class="runbookops-splash-start">
              <h2>Start in the console</h2>
              <p>Choose a sample incident, inspect retrieved runbook evidence, then run triage to review the model's structured decision.</p>
              <button class="runbookops-splash-enter" type="button">Enter console</button>
            </div>
          </section>
        </div>
        <style>
          #runbookops-splash {{
            position: fixed;
            inset: 0;
            z-index: 2147483647;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
            color: #E5E7EB;
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }}
          .runbookops-splash-backdrop {{
            position: absolute;
            inset: 0;
            background: rgba(3, 7, 18, 0.78);
            backdrop-filter: blur(10px);
          }}
          .runbookops-splash-panel {{
            position: relative;
            width: min(760px, 100%);
            border: 1px solid #293548;
            border-radius: 12px;
            background: linear-gradient(145deg, rgba(17, 24, 39, 0.98), rgba(8, 12, 18, 0.98));
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.55);
            padding: 28px;
          }}
          .runbookops-splash-close {{
            position: absolute;
            top: 14px;
            right: 14px;
            width: 34px;
            height: 34px;
            border: 1px solid #293548;
            border-radius: 8px;
            background: #0B0F17;
            color: #94A3B8;
            cursor: pointer;
          }}
          .runbookops-splash-brand {{
            display: flex;
            align-items: center;
            gap: 16px;
          }}
          .runbookops-splash-mark {{
            width: 72px;
            height: 72px;
            flex: 0 0 auto;
          }}
          .runbookops-splash-brand h1 {{
            margin: 0;
            color: #F8FAFC;
            font-size: 30px;
            line-height: 1.1;
          }}
          .runbookops-splash-brand p,
          .runbookops-splash-copy,
          .runbookops-splash-start p {{
            margin: 6px 0 0;
            color: #94A3B8;
          }}
          .runbookops-splash-copy {{
            margin-top: 22px;
            font-size: 15px;
            line-height: 1.55;
          }}
          .runbookops-splash-metrics {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin: 24px 0 16px;
          }}
          .runbookops-splash-metrics div {{
            border: 1px solid #293548;
            border-radius: 8px;
            background: #0B0F17;
            padding: 16px;
          }}
          .runbookops-splash-metrics span {{
            display: block;
            color: #F8FAFC;
            font-size: 30px;
            line-height: 1;
            margin-bottom: 8px;
          }}
          .runbookops-splash-metrics strong {{
            color: #CBD5E1;
            font-size: 13px;
            font-weight: 600;
          }}
          .runbookops-splash-start {{
            border: 1px solid #293548;
            border-radius: 8px;
            background: #080C12;
            padding: 18px;
          }}
          .runbookops-splash-start h2 {{
            margin: 0;
            color: #F8FAFC;
            font-size: 20px;
            line-height: 1.2;
          }}
          .runbookops-splash-enter {{
            width: 100%;
            margin-top: 18px;
            border: 0;
            border-radius: 8px;
            background: linear-gradient(90deg, #00E5FF, #0072FF);
            color: #03111F;
            cursor: pointer;
            font-weight: 700;
            padding: 12px 16px;
          }}
          @media (max-width: 720px) {{
            .runbookops-splash-panel {{
              padding: 22px;
            }}
            .runbookops-splash-metrics {{
              grid-template-columns: 1fr;
            }}
          }}
        </style>
        <script>
          (() => {{
            const key = "runbookopsSplashDismissed";
            const root = document.getElementById("runbookops-splash");
            if (!root) return;
            const close = () => {{
              try {{ window.localStorage.setItem(key, "true"); }} catch (error) {{}}
              root.remove();
            }};
            try {{
              if (window.localStorage.getItem(key) === "true") {{
                root.remove();
                return;
              }}
            }} catch (error) {{}}
            root.querySelector(".runbookops-splash-enter")?.addEventListener("click", close);
            root.querySelector(".runbookops-splash-close")?.addEventListener("click", close);
            root.querySelector(".runbookops-splash-backdrop")?.addEventListener("click", close);
            document.addEventListener("keydown", (event) => {{
              if (event.key === "Escape" && document.getElementById("runbookops-splash")) close();
            }});
          }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


st.set_page_config(
    page_title=APP_DISPLAY_NAME,
    page_icon=str(LOGO_ICON_PATH),
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
selected_case = render_context_bar(cases, case_labels)

input_col, result_col = st.columns([0.62, 0.38], gap="large")

with input_col, st.container(border=True):
    st.subheader("Incident report", icon=":material/edit_note:")

    with st.form("triage_form", border=False):
        incident_text = st.text_area(
            "Incident report (logs)",
            value=incident_log_text(selected_case["description"]),
            height=280,
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

if submitted:
    with st.spinner("Retrieving runbooks and calling the model..."):
        st.session_state.triage_run = triage_incident_with_context(incident_text)
        st.session_state.triage_case = case_label(selected_case)
    st.toast("Triage complete", icon=":material/check_circle:")

with result_col:
    if "triage_run" in st.session_state:
        render_result(st.session_state.triage_run)
    else:
        render_empty_result(cases)

render_footer()

render_splash_overlay(cases)

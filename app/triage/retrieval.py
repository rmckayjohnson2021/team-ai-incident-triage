import re
from pathlib import Path

RUNBOOK_DIR = Path(__file__).resolve().parents[2] / "data" / "runbooks"

STOPWORDS = {
    "a",
    "after",
    "all",
    "and",
    "are",
    "at",
    "be",
    "before",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "no",
    "not",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "was",
    "with",
}

CATEGORY_HINTS = {
    "ambiguous_outage.md": {
        "ambiguous",
        "blast",
        "cause",
        "multiple",
        "outage",
        "provider",
        "services",
        "unclear",
        "unknown",
    },
    "duplicate_records.md": {
        "duplicate",
        "duplicated",
        "duplicates",
        "key",
        "keys",
        "replay",
        "replayed",
        "resend",
        "upsert",
    },
    "failed_import.md": {
        "arrival",
        "corrupt",
        "download",
        "empty",
        "failed",
        "file",
        "import",
        "malformed",
        "parser",
        "timeout",
    },
    "schema_change.md": {
        "column",
        "columns",
        "field",
        "mapping",
        "missing",
        "renamed",
        "schema",
        "type",
        "validation",
    },
    "stale_dashboard.md": {
        "bi",
        "cache",
        "dashboard",
        "fresh",
        "refresh",
        "stale",
        "timestamp",
        "warehouse",
    },
}


def load_runbooks(runbook_dir: Path = RUNBOOK_DIR) -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in runbook_dir.glob("*.md")}


def tokenize(text: str) -> set[str]:
    normalized = text.lower().replace("_", " ").replace("-", " ")
    return {
        token
        for token in re.findall(r"[a-z0-9]+", normalized)
        if len(token) > 2 and token not in STOPWORDS
    }


def best_snippet(body: str, query_terms: set[str], hints: set[str]) -> tuple[str, str]:
    current_heading = "Runbook"
    best_heading = current_heading
    best_line = ""
    best_score = -1
    fallback_line = ""

    for raw_line in body.splitlines():
        line = raw_line.strip().lstrip("\ufeff")
        if not line:
            continue
        if line.startswith("#"):
            current_heading = line.strip("# ")
            continue

        fallback_line = line
        line_terms = tokenize(line)
        score = (len(query_terms & line_terms) * 3) + len(hints & line_terms)
        if current_heading.lower() in {"evidence to check", "recommended next steps", "symptoms"}:
            score += 1

        if score > best_score:
            best_score = score
            best_heading = current_heading
            best_line = line

    if not best_line:
        best_line = fallback_line or body[:240].replace("\n", " ")

    return best_heading, best_line[:360]


def retrieve_runbooks(incident_text: str, limit: int = 2) -> list[dict[str, str]]:
    query_terms = tokenize(incident_text)
    scored: list[tuple[int, str, dict[str, str]]] = []

    for name, body in load_runbooks().items():
        hints = CATEGORY_HINTS.get(name, set())
        body_terms = tokenize(body)
        filename_terms = tokenize(Path(name).stem)
        matched_terms = query_terms & (body_terms | filename_terms | hints)

        score = len(matched_terms)
        score += len(query_terms & hints) * 4
        score += len(query_terms & filename_terms) * 3
        score += len(query_terms & body_terms)

        if score:
            heading, snippet = best_snippet(body, query_terms, hints)
            scored.append(
                (
                    score,
                    name,
                    {
                        "name": name,
                        "score": str(score),
                        "heading": heading,
                        "snippet": snippet,
                        "matched_terms": ", ".join(sorted(matched_terms)),
                    },
                )
            )

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [item for _, _, item in scored[:limit]]

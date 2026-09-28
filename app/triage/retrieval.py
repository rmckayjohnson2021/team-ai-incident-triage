from pathlib import Path

RUNBOOK_DIR = Path(__file__).resolve().parents[2] / "data" / "runbooks"


def load_runbooks(runbook_dir: Path = RUNBOOK_DIR) -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in runbook_dir.glob("*.md")}


def retrieve_runbooks(incident_text: str, limit: int = 2) -> list[dict[str, str]]:
    query_terms = set(incident_text.lower().replace("-", " ").split())
    scored: list[tuple[int, str, str]] = []

    for name, body in load_runbooks().items():
        haystack = f"{name} {body}".lower().replace("-", " ")
        score = sum(1 for term in query_terms if term in haystack)
        if score:
            scored.append((score, name, body[:500]))

    scored.sort(reverse=True)
    return [{"name": name, "snippet": snippet} for _, name, snippet in scored[:limit]]

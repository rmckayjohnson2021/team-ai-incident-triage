from app.triage.retrieval import retrieve_runbooks


def test_retrieval_finds_schema_runbook():
    results = retrieve_runbooks("vendor file arrived with a new column")
    names = [item["name"] for item in results]
    assert "schema_change.md" in names

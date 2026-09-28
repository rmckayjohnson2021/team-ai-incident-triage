from app.triage.retrieval import retrieve_runbooks


def test_retrieval_finds_schema_runbook():
    results = retrieve_runbooks("vendor file arrived with a new column")
    names = [item["name"] for item in results]
    assert "schema_change.md" in names


def test_retrieval_returns_ranked_snippet_metadata():
    results = retrieve_runbooks("dashboard refresh failed and warehouse table is current", limit=1)

    assert results[0]["name"] == "stale_dashboard.md"
    assert int(results[0]["score"]) > 0
    assert results[0]["heading"]
    assert results[0]["snippet"]
    assert "dashboard" in results[0]["matched_terms"]

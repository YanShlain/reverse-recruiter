def test_saved_search_create_list_and_run(client):
    save_resp = client.post(
        "/api/v1/search/saved",
        json={"name": "Engineer remote", "filters": {"keywords": "engineer"}},
    )
    assert save_resp.status_code == 200
    saved = save_resp.json()
    assert saved["name"] == "Engineer remote"
    saved_id = saved["id"]
    assert saved["filters"]["keywords"] == "engineer"

    list_resp = client.get("/api/v1/search/saved")
    assert list_resp.status_code == 200
    ids = [s["id"] for s in list_resp.json()]
    assert saved_id in ids

    run_resp = client.post(f"/api/v1/search/saved/{saved_id}/run", params={"use_llm": False})
    assert run_resp.status_code == 200
    rows = run_resp.json()
    assert len(rows) >= 1
    assert rows[0]["match_score"] is not None


def test_run_saved_search_not_found(client):
    resp = client.post("/api/v1/search/saved/missing-id/run")
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"] == "not_found"

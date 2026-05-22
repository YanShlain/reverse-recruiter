def test_search_apply_pipeline_flow(client):
    search_resp = client.post(
        "/api/v1/search/",
        json={"keywords": "engineer", "use_llm": False},
    )
    assert search_resp.status_code == 200
    rows = search_resp.json()
    assert len(rows) >= 1
    assert rows[0]["match_score"] is not None

    job_ids = [r["job_id"] for r in rows[:2]]
    apply_resp = client.post("/api/v1/apply", json={"job_ids": job_ids})
    assert apply_resp.status_code == 200
    assert len(apply_resp.json()["jobs"]) == 2

    pipeline_resp = client.get("/api/v1/pipeline")
    assert pipeline_resp.status_code == 200
    pipeline = pipeline_resp.json()
    assert len(pipeline) >= 2

    confirm_resp = client.post(
        "/api/v1/pipeline/confirm",
        json={"job_ids": job_ids, "action": "submitted"},
    )
    assert confirm_resp.status_code == 200
    confirmed = confirm_resp.json()
    assert all(j["lifecycle_status"] == "submitted" for j in confirmed)


def test_search_settings(client):
    client.post("/api/v1/search/", json={"keywords": "engineer", "use_llm": True})
    settings_resp = client.get("/api/v1/search/settings")
    assert settings_resp.status_code == 200
    assert settings_resp.json()["use_llm_scoring"] is True


def test_session_ensure(client):
    resp = client.post("/api/v1/session/ensure")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

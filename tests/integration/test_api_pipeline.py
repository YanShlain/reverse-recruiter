from datetime import datetime, timezone


def test_get_pipeline_job(client, in_progress_job_id):
    resp = client.get(f"/api/v1/pipeline/{in_progress_job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == in_progress_job_id
    assert body["lifecycle_status"] == "in_progress"


def test_get_pipeline_job_not_found(client):
    resp = client.get("/api/v1/pipeline/nonexistent-job")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "not_found"


def test_patch_pipeline_job(client, in_progress_job_id):
    resp = client.patch(
        f"/api/v1/pipeline/{in_progress_job_id}",
        json={"progress_stage": "screening"},
    )
    assert resp.status_code == 200
    assert resp.json()["progress_stage"] == "screening"


def test_list_pipeline_by_lifecycle(client, search_job_ids):
    client.post("/api/v1/apply", json={"job_ids": search_job_ids})
    client.post(
        "/api/v1/pipeline/confirm",
        json={"job_ids": [search_job_ids[0]], "action": "submitted"},
    )
    resp = client.get("/api/v1/pipeline", params={"lifecycle": "submitted"})
    assert resp.status_code == 200
    submitted = resp.json()
    assert any(j["job_id"] == search_job_ids[0] for j in submitted)
    assert all(j["lifecycle_status"] == "submitted" for j in submitted)


def test_confirm_skipped(client, search_job_ids):
    job_id = search_job_ids[1]
    client.post("/api/v1/apply", json={"job_ids": [job_id]})
    resp = client.post(
        "/api/v1/pipeline/confirm",
        json={"job_ids": [job_id], "action": "skipped"},
    )
    assert resp.status_code == 200
    assert resp.json()[0]["lifecycle_status"] == "skipped"


def test_pipeline_interviews_crud(client, in_progress_job_id):
    interview_at = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc).isoformat()
    create_resp = client.post(
        f"/api/v1/pipeline/{in_progress_job_id}/interviews",
        json={
            "datetime": interview_at,
            "with_whom": "Alex Recruiter",
            "interview_type": "video",
            "notes": "Round 1",
        },
    )
    assert create_resp.status_code == 200
    interviews = create_resp.json()["interviews"]
    assert len(interviews) == 1
    event_id = interviews[0]["id"]

    patch_resp = client.patch(
        f"/api/v1/pipeline/{in_progress_job_id}/interviews/{event_id}",
        json={"notes": "Round 1 rescheduled"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["interviews"][0]["notes"] == "Round 1 rescheduled"

    delete_resp = client.delete(
        f"/api/v1/pipeline/{in_progress_job_id}/interviews/{event_id}",
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["interviews"] == []


def test_apply_unknown_job_returns_404(client):
    resp = client.post("/api/v1/apply", json={"job_ids": ["unknown-job-id"]})
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "not_found"

import os

import pytest

os.environ["MOCK_MCP"] = "true"
os.environ.setdefault("LOG_LEVEL", "warning")


@pytest.fixture(autouse=True)
def _isolated_data(tmp_path):
    from backend.api.dependencies import reset_dependencies
    from backend.config import settings

    settings.data_dir = tmp_path
    os.environ["DATA_DIR"] = str(tmp_path)
    reset_dependencies()
    yield
    reset_dependencies()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def search_job_ids(client):
    resp = client.post(
        "/api/v1/search/",
        json={"keywords": "engineer", "use_llm": False},
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert rows
    return [r["job_id"] for r in rows[:2]]


@pytest.fixture
def in_progress_job_id(client, search_job_ids):
    job_id = search_job_ids[0]
    resp = client.post("/api/v1/apply", json={"job_ids": [job_id]})
    assert resp.status_code == 200
    return job_id

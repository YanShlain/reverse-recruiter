import os
import tempfile

import pytest

_test_data_dir = tempfile.mkdtemp(prefix="reverse_recruiter_test_")
os.environ.setdefault("MOCK_MCP", "true")
os.environ["DATA_DIR"] = _test_data_dir
os.environ.setdefault("LOG_LEVEL", "warning")


@pytest.fixture(autouse=True)
def _reset_dependency_caches():
    from reverse_recruiter.api.dependencies import reset_dependencies

    reset_dependencies()
    yield
    reset_dependencies()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from reverse_recruiter.main import app

    with TestClient(app) as test_client:
        yield test_client

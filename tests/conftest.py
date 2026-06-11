import os

import pytest
from fastapi.testclient import TestClient


os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["SESSION_SECRET"] = "test-session-secret"
os.environ["MINIMAX_API_KEY"] = ""


@pytest.fixture()
def client():
    from huarun_app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

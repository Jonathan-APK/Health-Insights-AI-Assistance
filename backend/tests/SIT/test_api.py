from fastapi.testclient import TestClient

import os

os.environ["BACKEND_HEALTH_ONLY_APP"] = "1"

from main import create_app

client = TestClient(create_app(include_chat_routes=False))


def test_health_check_status_code():
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_health_check_payload():
    response = client.get("/v1/health")
    assert response.json() == {"status": "ok", "service": "Health Insights AI"}


def test_health_check_content_type():
    response = client.get("/v1/health")
    assert response.headers["content-type"].startswith("application/json")
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/v1/health")
    assert response.status_code == 200

def test_health_response():
    response = client.get("/v1/health")
    assert response.json()["status"] == "ok"
from fastapi.testclient import TestClient

from intentbid.app.main import app


def test_readiness():
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

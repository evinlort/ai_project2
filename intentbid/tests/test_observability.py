import re


def test_metrics_endpoint_exposes_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "http_requests_total" in body


def test_correlation_id_header_echoed(client):
    response = client.get("/health", headers={"X-Correlation-Id": "req-123"})
    assert response.status_code == 200
    assert response.headers["X-Correlation-Id"] == "req-123"


def test_correlation_id_generated_when_missing(client):
    response = client.get("/health")
    assert response.status_code == 200
    correlation_id = response.headers["X-Correlation-Id"]
    assert re.match(r"^[a-f0-9]{32}$", correlation_id)

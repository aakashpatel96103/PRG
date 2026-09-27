from unittest.mock import patch


def test_liveness_probe(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_readiness_probe_healthy(client):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_readiness_probe_database_failure(client):
    with patch("app.routers.health.check_db_connection", return_value=False):
        resp = client.get("/health/ready")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "not_ready"
        assert data["database"] == "disconnected"

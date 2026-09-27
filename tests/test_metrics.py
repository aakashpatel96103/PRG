def test_prometheus_metrics_endpoint(client):
    # Perform a request to generate metrics
    client.get("/health")

    # Fetch Prometheus metrics
    resp = client.get("/metrics")
    assert resp.status_code == 200
    content = resp.text

    # Validate Prometheus format markers
    assert "http_request_duration_seconds" in content or "http_requests_total" in content

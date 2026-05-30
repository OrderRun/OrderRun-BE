def test_health_uses_v1_api_response(client):
    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {"status": "UP"},
        "message": "Success",
    }

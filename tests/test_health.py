def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_home_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Py-Yt" in response.text


def test_database_readiness_endpoint(client):
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "available"}

 
def test_security_policy_allows_signed_video_media_sources(client):
    response = client.get("/health")
    assert response.status_code == 200
    policy = response.headers.get("content-security-policy", "")
    assert "media-src 'self' https: blob:" in policy
    assert "script-src 'self'" in policy

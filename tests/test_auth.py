def test_register_login_and_current_user(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "creator@example.com",
            "display_name": "Creator One",
            "password": "A-very-strong-test-password-1",
        },
    )
    assert registration.status_code == 201
    assert registration.json()["email"] == "creator@example.com"
    assert client.cookies.get("pyyt_session")
    assert client.cookies.get("pyyt_csrf")

    current = client.get("/api/v1/auth/me")
    assert current.status_code == 200
    assert current.json()["display_name"] == "Creator One"

    csrf = client.cookies.get("pyyt_csrf")
    logout = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    assert logout.status_code == 204

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@example.com", "password": "A-very-strong-test-password-1"},
    )
    assert login.status_code == 200
    assert login.json()["email"] == "creator@example.com"

def test_duplicate_registration_is_rejected(client):
    payload = {
        "email": "duplicate@example.com",
        "display_name": "Creator Two",
        "password": "A-very-strong-test-password-2",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    duplicate = client.post("/api/v1/auth/register", json=payload)
    assert duplicate.status_code == 409

def test_csrf_is_required_for_authenticated_mutations(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "csrf@example.com",
            "display_name": "CSRF User",
            "password": "A-very-strong-test-password-3",
        },
    )
    response = client.post("/api/v1/playlists", json={"title": "Private list"})
    assert response.status_code == 403

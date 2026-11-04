def register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "settings-user@example.com",
            "display_name": "Settings User",
            "password": "A-very-strong-test-password-10",
        },
    )
    assert response.status_code == 201
    return client.cookies.get("pyyt_csrf")


def test_profile_update_changes_user_and_channel_name(client):
    csrf = register_user(client)
    response = client.patch(
        "/api/v1/auth/me",
        json={
            "display_name": "Updated Creator",
            "bio": "I publish educational videos.",
            "avatar_url": "https://cdn.example.com/avatar.png",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Creator"
    assert data["bio"] == "I publish educational videos."
    assert data["avatar_url"] == "https://cdn.example.com/avatar.png"

    channel = client.get("/api/v1/channels/me")
    assert channel.status_code == 200
    assert channel.json()["name"] == "Updated Creator"


def test_profile_rejects_non_http_avatar_url(client):
    csrf = register_user(client)
    response = client.patch(
        "/api/v1/auth/me",
        json={
            "display_name": "Settings User",
            "bio": "",
            "avatar_url": "javascript:alert(1)",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 422


def test_password_change_requires_current_password_and_rotates_credentials(client):
    csrf = register_user(client)
    wrong = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "not-the-current-password",
            "new_password": "A-new-very-strong-password-11",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert wrong.status_code == 400

    changed = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "A-very-strong-test-password-10",
            "new_password": "A-new-very-strong-password-11",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert changed.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "settings-user@example.com", "password": "A-very-strong-test-password-10"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "settings-user@example.com", "password": "A-new-very-strong-password-11"},
    )
    assert new_login.status_code == 200

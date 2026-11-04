from db.models import Channel
from db.session import SessionLocal


def test_profile_update_changes_user_and_channel_name(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile@example.com",
            "display_name": "Original Name",
            "password": "A-very-strong-test-password-11",
        },
    )
    assert registration.status_code == 201
    csrf = client.cookies.get("pyyt_csrf")

    updated = client.patch(
        "/api/v1/auth/me",
        json={
            "display_name": "Updated Creator",
            "bio": "I publish coding tutorials.",
            "avatar_url": "https://example.com/avatar.png",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Updated Creator"
    assert updated.json()["bio"] == "I publish coding tutorials."
    assert updated.json()["avatar_url"] == "https://example.com/avatar.png"

    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == updated.json()["id"]).one()
        assert channel.name == "Updated Creator"

    current = client.get("/api/v1/auth/me")
    assert current.status_code == 200
    assert current.json()["bio"] == "I publish coding tutorials."


def test_password_change_requires_current_password_and_new_password_works(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "password-change@example.com",
            "display_name": "Password User",
            "password": "A-very-strong-test-password-12",
        },
    )
    assert registration.status_code == 201
    csrf = client.cookies.get("pyyt_csrf")

    wrong_current = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "incorrect-current-password",
            "new_password": "Another-strong-password-13",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert wrong_current.status_code == 400

    changed = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "A-very-strong-test-password-12",
            "new_password": "Another-strong-password-13",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert changed.status_code == 204

    csrf = client.cookies.get("pyyt_csrf")
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "password-change@example.com",
            "password": "Another-strong-password-13",
        },
    )
    assert login.status_code == 200

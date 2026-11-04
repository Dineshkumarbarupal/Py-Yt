from db.models import Channel, ContentReport, Video
from db.session import SessionLocal


def register(client, email, name):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": name,
            "password": "A-very-strong-test-password-19",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_video_report_duplicate_and_admin_action(client):
    owner = register(client, "reported-owner@example.com", "Reported Owner")
    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == owner["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Reported video",
            description="",
            category="General",
            source_type="upload",
            storage_key=f"moderation/{owner['id']}/video.mp4",
            mime_type="video/mp4",
            file_size_bytes=256,
            visibility="public",
            status="published",
        )
        db.add(video)
        db.commit()
        video_id = video.id

    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")})
    reporter = register(client, "reporter@example.com", "Reporter")
    csrf = client.cookies.get("pyyt_csrf")
    report = client.post(
        "/api/v1/reports",
        json={
            "target_type": "video",
            "target_id": video_id,
            "reason": "spam",
            "details": "This video repeats misleading links.",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert report.status_code == 201
    assert report.json()["status"] == "open"

    duplicate = client.post(
        "/api/v1/reports",
        json={"target_type": "video", "target_id": video_id, "reason": "spam"},
        headers={"X-CSRF-Token": csrf},
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["status"] == "already_reported"

    forbidden = client.get("/api/v1/admin/reports")
    assert forbidden.status_code == 403

    with SessionLocal() as db:
        admin = db.query(type(db.get(type(db.query(ContentReport).first()), None))) if False else None
        from db.models import User
        admin_user = db.query(User).filter(User.email == reporter["email"]).one()
        admin_user.role = "admin"
        db.commit()

    queue = client.get("/api/v1/admin/reports")
    assert queue.status_code == 200
    assert len(queue.json()["items"]) == 1
    report_id = queue.json()["items"][0]["id"]

    action = client.patch(
        f"/api/v1/admin/reports/{report_id}",
        json={"status": "actioned", "resolution_note": "Removed under platform policy."},
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    assert action.status_code == 200
    assert action.json()["status"] == "actioned"

    with SessionLocal() as db:
        video = db.get(Video, video_id)
        assert video.status == "removed"
        assert video.visibility == "private"
        saved_report = db.get(ContentReport, report_id)
        assert saved_report.reviewer_id is not None

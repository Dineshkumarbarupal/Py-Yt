from db.models import Notification, User
from db.session import SessionLocal


def register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "notifications@example.com",
            "display_name": "Notification User",
            "password": "A-very-strong-test-password-14",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_notification_list_and_read_state(client):
    user = register_user(client)
    with SessionLocal() as db:
        item = Notification(
            recipient_id=user["id"],
            notification_type="new_video",
            entity_type="video",
            entity_id="video-123",
            message="A creator published a new video.",
            is_read=False,
        )
        db.add(item)
        db.commit()
        notification_id = item.id

    listing = client.get("/api/v1/notifications")
    assert listing.status_code == 200
    assert listing.json()["unread_count"] == 1
    assert listing.json()["items"][0]["id"] == notification_id
    assert listing.json()["items"][0]["url"] == "/watch/video-123"

    csrf = client.cookies.get("pyyt_csrf")
    marked = client.post(
        f"/api/v1/notifications/{notification_id}/read",
        headers={"X-CSRF-Token": csrf},
    )
    assert marked.status_code == 204

    listing = client.get("/api/v1/notifications")
    assert listing.status_code == 200
    assert listing.json()["unread_count"] == 0
    assert listing.json()["items"][0]["is_read"] is True


def test_mark_all_notifications_read(client):
    user = register_user(client)
    with SessionLocal() as db:
        db.add_all([
            Notification(
                recipient_id=user["id"],
                notification_type="new_subscriber",
                entity_type="channel",
                entity_id="channel-123",
                message="A user subscribed to your channel.",
                is_read=False,
            ),
            Notification(
                recipient_id=user["id"],
                notification_type="new_comment",
                entity_type="video",
                entity_id="video-456",
                message="A user commented on your video.",
                is_read=False,
            ),
        ])
        db.commit()

    csrf = client.cookies.get("pyyt_csrf")
    response = client.post("/api/v1/notifications/read-all", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 204
    listing = client.get("/api/v1/notifications")
    assert listing.json()["unread_count"] == 0


def test_comment_creates_creator_notification(client):
    creator = register_user(client)
    from db.models import Channel, Video
    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == creator["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Creator video",
            description="",
            category="General",
            source_type="upload",
            storage_key=f"notifications/{creator['id']}/video.mp4",
            mime_type="video/mp4",
            file_size_bytes=128,
            visibility="public",
            status="published",
        )
        db.add(video)
        db.commit()
        video_id = video.id

    csrf = client.cookies.get("pyyt_csrf")
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    commenter_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "commenter@example.com",
            "display_name": "Commenter",
            "password": "A-very-strong-test-password-15",
        },
    )
    assert commenter_response.status_code == 201
    comment = client.post(
        "/api/v1/comments",
        json={"video_id": video_id, "body": "Great tutorial!"},
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    assert comment.status_code == 201

    client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": creator["email"], "password": "A-very-strong-test-password-14"},
    )
    assert login.status_code == 200
    notifications = client.get("/api/v1/notifications")
    assert notifications.status_code == 200
    assert notifications.json()["unread_count"] == 1
    assert notifications.json()["items"][0]["type"] == "new_comment"

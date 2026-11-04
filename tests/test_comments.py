from db.models import Channel, Video
from db.session import SessionLocal


def register(client, email, name, password):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": name, "password": password},
    )
    assert response.status_code == 201
    return response.json()


def test_comment_thread_and_reply_notifications(client):
    owner = register(
        client,
        "thread-owner@example.com",
        "Thread Owner",
        "A-very-strong-test-password-16",
    )
    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == owner["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Threaded video",
            description="",
            category="Learning",
            source_type="upload",
            storage_key=f"threads/{owner['id']}/video.mp4",
            mime_type="video/mp4",
            file_size_bytes=512,
            visibility="public",
            status="published",
        )
        db.add(video)
        db.commit()
        video_id = video.id

    client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    register(
        client,
        "thread-viewer@example.com",
        "Thread Viewer",
        "A-very-strong-test-password-17",
    )
    csrf = client.cookies.get("pyyt_csrf")
    root = client.post(
        "/api/v1/comments",
        json={"video_id": video_id, "body": "First comment"},
        headers={"X-CSRF-Token": csrf},
    )
    assert root.status_code == 201

    reply = client.post(
        "/api/v1/comments",
        json={
            "video_id": video_id,
            "body": "A reply",
            "parent_comment_id": root.json()["id"],
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert reply.status_code == 201

    comments = client.get(f"/api/v1/comments/video/{video_id}")
    assert comments.status_code == 200
    replies = [item for item in comments.json()["items"] if item["parent_comment_id"] == root.json()["id"]]
    assert len(replies) == 1
    assert replies[0]["body"] == "A reply"

    client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": owner["email"], "password": "A-very-strong-test-password-16"},
    )
    assert login.status_code == 200
    notifications = client.get("/api/v1/notifications")
    assert notifications.status_code == 200
    assert any(item["type"] == "new_comment" for item in notifications.json()["items"])

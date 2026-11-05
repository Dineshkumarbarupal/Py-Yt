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


def test_comment_owner_can_edit_and_delete_but_other_users_cannot(client):
    owner = register(
        client,
        "comment-owner@example.com",
        "Comment Owner",
        "A-very-strong-test-password-20",
    )
    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == owner["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Comment ownership video",
            description="",
            category="Learning",
            source_type="upload",
            storage_key=f"comment-owner/{owner['id']}/video.mp4",
            mime_type="video/mp4",
            file_size_bytes=256,
            visibility="public",
            status="published",
        )
        db.add(video)
        db.commit()
        video_id = video.id

    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")})
    commenter = register(
        client,
        "comment-author@example.com",
        "Comment Author",
        "A-very-strong-test-password-21",
    )
    created = client.post(
        "/api/v1/comments",
        json={"video_id": video_id, "body": "Original comment"},
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    assert created.status_code == 201
    comment_id = created.json()["id"]

    listing = client.get(f"/api/v1/comments/video/{video_id}")
    assert listing.status_code == 200
    assert listing.json()["items"][0]["can_manage"] is True

    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")})
    owner_login = client.post(
        "/api/v1/auth/login",
        json={"email": owner["email"], "password": "A-very-strong-test-password-20"},
    )
    assert owner_login.status_code == 200
    forbidden_edit = client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"body": "Attempted unauthorized edit"},
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    assert forbidden_edit.status_code == 404
    forbidden_delete = client.delete(
        f"/api/v1/comments/{comment_id}",
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    assert forbidden_delete.status_code == 404
    listing = client.get(f"/api/v1/comments/video/{video_id}")
    assert listing.json()["items"][0]["can_manage"] is False

    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")})
    author_login = client.post(
        "/api/v1/auth/login",
        json={"email": commenter["email"], "password": "A-very-strong-test-password-21"},
    )
    assert author_login.status_code == 200

    edited = client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"body": "Edited comment"},
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    assert edited.status_code == 200
    assert edited.json()["body"] == "Edited comment"

    deleted = client.delete(
        f"/api/v1/comments/{comment_id}",
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    assert deleted.status_code == 204
    listing = client.get(f"/api/v1/comments/video/{video_id}")
    assert listing.status_code == 200
    assert listing.json()["items"] == []

def test_comment_sort_newest_and_oldest(client):
    from datetime import datetime
    from db.models import Comment

    owner = register(
        client,
        "comment-sort-owner@example.com",
        "Comment Sort Owner",
        "A-very-strong-test-password-22",
    )
    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == owner["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Comment sorting video",
            description="",
            category="Learning",
            source_type="upload",
            storage_key=f"comment-sort/{owner['id']}/video.mp4",
            mime_type="video/mp4",
            file_size_bytes=128,
            visibility="public",
            status="published",
        )
        db.add(video)
        db.flush()
        older = Comment(
            user_id=owner["id"],
            video_id=video.id,
            body="Older comment",
            created_at=datetime(2025, 1, 1, 10, 0, 0),
        )
        newer = Comment(
            user_id=owner["id"],
            video_id=video.id,
            body="Newer comment",
            created_at=datetime(2025, 1, 2, 10, 0, 0),
        )
        db.add_all([older, newer])
        db.commit()
        video_id = video.id

    newest = client.get(f"/api/v1/comments/video/{video_id}?sort=newest")
    assert newest.status_code == 200
    assert [item["body"] for item in newest.json()["items"]] == ["Newer comment", "Older comment"]

    oldest = client.get(f"/api/v1/comments/video/{video_id}?sort=oldest")
    assert oldest.status_code == 200
    assert [item["body"] for item in oldest.json()["items"]] == ["Older comment", "Newer comment"]

    invalid = client.get(f"/api/v1/comments/video/{video_id}?sort=top")
    assert invalid.status_code == 422

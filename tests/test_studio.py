from db.models import Channel, Comment, Video
from db.session import SessionLocal


def test_creator_studio_dashboard_and_comment_moderation(client, monkeypatch):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "studio-owner@example.com",
            "display_name": "Studio Owner",
            "password": "A-very-strong-test-password-5",
        },
    )
    assert registration.status_code == 201
    owner = registration.json()
    csrf = client.cookies.get("pyyt_csrf")

    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == owner["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Studio test video",
            description="A video for Studio tests",
            category="Learning",
            source_type="upload",
            storage_key=f"test/{owner['id']}/studio.mp4",
            mime_type="video/mp4",
            file_size_bytes=256,
            visibility="public",
            status="published",
            view_count=7,
        )
        db.add(video)
        db.flush()
        comment = Comment(
            user_id=owner["id"],
            video_id=video.id,
            body="A test comment",
            status="visible",
        )
        db.add(comment)
        db.commit()
        video_id = video.id
        comment_id = comment.id

    overview = client.get("/api/v1/studio/overview")
    assert overview.status_code == 200
    assert overview.json()["published_videos"] == 1
    assert overview.json()["total_views"] == 7
    assert overview.json()["visible_comments"] == 1

    content = client.get("/api/v1/studio/videos")
    assert content.status_code == 200
    assert content.json()["items"][0]["id"] == video_id

    analytics = client.get("/api/v1/studio/analytics")
    assert analytics.status_code == 200
    assert analytics.json()["top_videos"][0]["id"] == video_id

    comments = client.get("/api/v1/studio/comments")
    assert comments.status_code == 200
    assert comments.json()["items"][0]["id"] == comment_id

    hidden = client.patch(
        f"/api/v1/studio/comments/{comment_id}",
        json={"status": "hidden"},
        headers={"X-CSRF-Token": csrf},
    )
    assert hidden.status_code == 200
    assert hidden.json()["status"] == "hidden"

    import api.v1.endpoints.videos as videos_module
    monkeypatch.setattr(videos_module, "delete_object", lambda object_key: None)

    updated = client.patch(
        f"/api/v1/videos/{video_id}",
        json={"title": "Updated Studio test", "category": "Technology", "video_format": "short", "visibility": "unlisted"},
        headers={"X-CSRF-Token": csrf},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated Studio test"
    assert updated.json()["visibility"] == "unlisted"
    assert updated.json()["video_format"] == "short"

    deleted = client.delete(
        f"/api/v1/videos/{video_id}",
        headers={"X-CSRF-Token": csrf},
    )
    assert deleted.status_code == 204

    unavailable = client.get(f"/api/v1/videos/{video_id}")
    assert unavailable.status_code == 404

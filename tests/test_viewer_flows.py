from db.models import Channel, Video
from db.session import SessionLocal


def register(client, email, name):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": name,
            "password": "A-very-strong-test-password-9",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_public_video(owner, video_format="standard"):
    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == owner["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Python tutorial",
            description="Learn Python",
            category="Learning",
            video_format=video_format,
            source_type="upload",
            storage_key=f"test/{owner['id']}/video.mp4",
            mime_type="video/mp4",
            file_size_bytes=120,
            visibility="public",
            status="published",
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        return video.id, channel.id


def test_watch_later_and_liked_library(client):
    owner = register(client, "viewer-owner@example.com", "Video Owner")
    video_id, _ = create_public_video(owner)

    viewer_client = client
    saved = viewer_client.post(f"/api/v1/library/watch-later/{video_id}", headers={
        "X-CSRF-Token": viewer_client.cookies.get("pyyt_csrf")
    })
    assert saved.status_code == 201
    assert saved.json()["status"] == "saved"

    later = viewer_client.get("/api/v1/library/watch-later")
    assert later.status_code == 200
    assert [item["id"] for item in later.json()["items"]] == [video_id]

    liked = viewer_client.put(
        f"/api/v1/engagement/videos/{video_id}/reaction",
        json={"reaction": "like"},
        headers={"X-CSRF-Token": viewer_client.cookies.get("pyyt_csrf")},
    )
    assert liked.status_code == 200
    summary = viewer_client.get(f"/api/v1/engagement/videos/{video_id}/reaction")
    assert summary.status_code == 200
    assert summary.json()["likes"] == 1
    assert summary.json()["dislikes"] == 0
    assert summary.json()["current_reaction"] == "like"

    disliked = viewer_client.put(
        f"/api/v1/engagement/videos/{video_id}/reaction",
        json={"reaction": "dislike"},
        headers={"X-CSRF-Token": viewer_client.cookies.get("pyyt_csrf")},
    )
    assert disliked.status_code == 200
    summary = viewer_client.get(f"/api/v1/engagement/videos/{video_id}/reaction")
    assert summary.json()["likes"] == 0
    assert summary.json()["dislikes"] == 1
    assert summary.json()["current_reaction"] == "dislike"

    viewer_client.delete(
        f"/api/v1/engagement/videos/{video_id}/reaction",
        headers={"X-CSRF-Token": viewer_client.cookies.get("pyyt_csrf")},
    )
    summary = viewer_client.get(f"/api/v1/engagement/videos/{video_id}/reaction")
    assert summary.json()["current_reaction"] is None
    liked_again = viewer_client.put(
        f"/api/v1/engagement/videos/{video_id}/reaction",
        json={"reaction": "like"},
        headers={"X-CSRF-Token": viewer_client.cookies.get("pyyt_csrf")},
    )
    assert liked_again.status_code == 200

    liked_list = viewer_client.get("/api/v1/library/liked")
    assert liked_list.status_code == 200
    assert [item["id"] for item in liked_list.json()["items"]] == [video_id]

    removed = viewer_client.delete(
        f"/api/v1/library/watch-later/{video_id}",
        headers={"X-CSRF-Token": viewer_client.cookies.get("pyyt_csrf")},
    )
    assert removed.status_code == 204


def test_playlist_create_and_visibility(client):
    owner = register(client, "playlist-owner@example.com", "Playlist Owner")
    video_id, _ = create_public_video(owner)
    csrf = client.cookies.get("pyyt_csrf")

    created = client.post(
        "/api/v1/playlists",
        json={"title": "My Learning List", "visibility": "public"},
        headers={"X-CSRF-Token": csrf},
    )
    assert created.status_code == 201
    playlist_id = created.json()["id"]

    added = client.post(
        f"/api/v1/playlists/{playlist_id}/items",
        json={"video_id": video_id},
        headers={"X-CSRF-Token": csrf},
    )
    assert added.status_code == 201

    detail = client.get(f"/api/v1/playlists/{playlist_id}")
    assert detail.status_code == 200
    assert detail.json()["items"][0]["video_id"] == video_id
    assert detail.json()["is_owner"] is True

    updated = client.patch(
        f"/api/v1/playlists/{playlist_id}",
        json={"title": "Updated Learning List", "description": "A curated study list."},
        headers={"X-CSRF-Token": csrf},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated Learning List"

    removed = client.delete(
        f"/api/v1/playlists/{playlist_id}/items/{video_id}",
        headers={"X-CSRF-Token": csrf},
    )
    assert removed.status_code == 204

    empty_detail = client.get(f"/api/v1/playlists/{playlist_id}")
    assert empty_detail.status_code == 200
    assert empty_detail.json()["items"] == []

    deleted = client.delete(
        f"/api/v1/playlists/{playlist_id}",
        headers={"X-CSRF-Token": csrf},
    )
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/playlists/{playlist_id}").status_code == 404


def test_subscription_lifecycle(client):
    first = register(client, "subscriber@example.com", "Subscriber")
    csrf = client.cookies.get("pyyt_csrf")
    second_client = client
    second_client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})

    second = register(second_client, "creator@example.com", "Creator Two")
    video_id, channel_id = create_public_video(second)

    # Sign back in as the subscriber.
    second_client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": second_client.cookies.get("pyyt_csrf")})
    login = second_client.post(
        "/api/v1/auth/login",
        json={"email": first["email"], "password": "A-very-strong-test-password-9"},
    )
    assert login.status_code == 200

    csrf = second_client.cookies.get("pyyt_csrf")
    subscribed = second_client.post(
        f"/api/v1/subscriptions/{channel_id}",
        headers={"X-CSRF-Token": csrf},
    )
    assert subscribed.status_code == 201
    listing = second_client.get("/api/v1/subscriptions")
    assert listing.status_code == 200
    assert listing.json()["items"][0]["channel_id"] == channel_id

    feed = second_client.get("/api/v1/subscriptions/feed")
    assert feed.status_code == 200
    assert [item["id"] for item in feed.json()["items"]] == [video_id]

    second_client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": second_client.cookies.get("pyyt_csrf")},
    )
    creator_login = second_client.post(
        "/api/v1/auth/login",
        json={"email": second["email"], "password": "A-very-strong-test-password-9"},
    )
    assert creator_login.status_code == 200
    creator_notifications = second_client.get("/api/v1/notifications")
    assert creator_notifications.status_code == 200
    assert creator_notifications.json()["unread_count"] == 1
    assert creator_notifications.json()["items"][0]["type"] == "new_subscriber"


def test_shorts_discovery_returns_only_short_public_videos(client):
    owner = register(client, "shorts-owner@example.com", "Shorts Owner")
    _standard_id, _ = create_public_video(owner, "standard")
    short_id, _ = create_public_video(owner, "short")

    response = client.get("/api/v1/discovery/shorts")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [short_id]
    assert response.json()["items"][0]["video_format"] == "short"

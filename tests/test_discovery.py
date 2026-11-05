def test_discovery_feed_and_search_are_empty_but_valid(client):
    feed = client.get("/api/v1/discovery/feed")
    assert feed.status_code == 200
    assert feed.json()["items"] == []

    search = client.get("/api/v1/discovery/search", params={"q": "python"})
    assert search.status_code == 200
    assert search.json()["query"] == "python"
    assert search.json()["items"] == []


def test_recently_uploaded_feed_includes_all_public_categories(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "recent-feed@example.com",
            "display_name": "Recent Feed Creator",
            "password": "A-very-strong-test-password-32",
        },
    )
    assert registration.status_code == 201

    from db.models import Channel, Video
    from db.session import SessionLocal

    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == registration.json()["id"]).one()
        python_video = Video(
            channel_id=channel.id,
            title="Python basics",
            category="Learning",
            source_type="upload",
            storage_key="recent-feed/python.mp4",
            mime_type="video/mp4",
            file_size_bytes=1024,
            visibility="public",
            status="published",
        )
        music_video = Video(
            channel_id=channel.id,
            title="Music practice",
            category="Music",
            source_type="upload",
            storage_key="recent-feed/music.mp4",
            mime_type="video/mp4",
            file_size_bytes=1024,
            visibility="public",
            status="published",
        )
        db.add_all([python_video, music_video])
        db.commit()
        expected_ids = {python_video.id, music_video.id}

    feed = client.get("/api/v1/discovery/feed", params={"category": "Recently uploaded"})
    assert feed.status_code == 200
    assert {item["id"] for item in feed.json()["items"]} == expected_ids

    search = client.get(
        "/api/v1/discovery/search",
        params={"q": "practice", "category": "Recently uploaded"},
    )
    assert search.status_code == 200
    assert [item["title"] for item in search.json()["items"]] == ["Music practice"]

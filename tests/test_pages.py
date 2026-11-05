def test_creator_studio_pages_render(client):
    for path in ["/studio", "/studio/upload", "/studio/content", "/studio/analytics", "/studio/comments", "/settings", "/notifications", "/shorts", "/admin/moderation"]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert "Py-Yt" in response.text, path


def test_viewer_library_pages_render(client):
    for path in ["/subscriptions", "/playlists", "/watch-later", "/liked", "/history", "/settings"]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert "Py-Yt" in response.text, path


def test_public_channel_page_and_own_channel_redirect(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "page-owner@example.com",
            "display_name": "Page Owner",
            "password": "A-very-strong-test-password-6",
        },
    )
    assert registration.status_code == 201
    response = client.get("/channel")
    assert response.status_code == 200
    assert "Page Owner" in response.text
    handle = client.get("/api/v1/channels/me").json()["handle"]
    public_page = client.get(f"/@{handle}")
    assert public_page.status_code == 200
    assert "Page Owner" in public_page.text


def test_watch_page_exposes_player_controls_and_comment_threads(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "watch-page@example.com",
            "display_name": "Watch Page Owner",
            "password": "A-very-strong-test-password-18",
        },
    )
    assert registration.status_code == 201
    from db.models import Channel, Video
    from db.session import SessionLocal
    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == registration.json()["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Player controls test",
            description="",
            category="Learning",
            source_type="upload",
            storage_key=f"watch-page/{registration.json()['id']}/video.mp4",
            mime_type="video/mp4",
            file_size_bytes=1024,
            visibility="public",
            status="published",
        )
        db.add(video)
        db.commit()
        video_id = video.id

    response = client.get(f"/watch/{video_id}")
    assert response.status_code == 200
    assert 'id="player-speed"' in response.text
    assert 'id="theater-toggle"' in response.text
    assert 'id="mini-player-toggle"' in response.text
    assert 'id="pip-toggle"' in response.text
    assert 'id="dislike-button"' in response.text
    assert 'id="share-button"' in response.text
    assert 'id="autoplay-toggle"' in response.text
    assert 'id="video-chapters"' in response.text
    assert 'id="video-chapter-list"' in response.text
    assert 'id="up-next-list"' in response.text
    assert 'id="queue-open"' in response.text
    assert 'id="queue-dialog"' in response.text


def test_studio_content_filter_controls_render(client):
    response = client.get("/studio/content")
    assert response.status_code == 200
    assert 'id="studio-search"' in response.text
    assert 'id="studio-status-filter"' in response.text
    assert 'id="studio-visibility-filter"' in response.text
    assert 'id="studio-format-filter"' in response.text
    assert 'id="studio-load-more"' in response.text


def test_upload_page_includes_optional_custom_thumbnail_picker(client):
    response = client.get("/studio/upload")
    assert response.status_code == 200
    assert 'id="thumbnail-file"' in response.text
    assert "image/jpeg,image/png,image/webp" in response.text

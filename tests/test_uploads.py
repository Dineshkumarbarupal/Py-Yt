def test_upload_verify_publish_and_playback(client, monkeypatch):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "upload-owner@example.com",
            "display_name": "Upload Owner",
            "password": "A-very-strong-test-password-7",
        },
    )
    assert registration.status_code == 201
    csrf = client.cookies.get("pyyt_csrf")

    import api.v1.endpoints.uploads as uploads_module
    import api.v1.endpoints.videos as videos_module

    monkeypatch.setattr(uploads_module.settings, "media_public_base_url", "https://media.example.test")
    monkeypatch.setattr(uploads_module.settings, "media_thumbnail_bucket", "pyyt-thumbnails")
    monkeypatch.setattr(
        uploads_module,
        "create_upload_url",
        lambda object_key, content_type, bucket_name=None: "https://storage.example.test/presigned-upload",
    )
    def inspect_video_object(object_key):
        return {"ContentLength": 2048, "ContentType": "video/mp4"}

    monkeypatch.setattr(uploads_module, "inspect_uploaded_object", inspect_video_object)
    monkeypatch.setattr(
        uploads_module,
        "inspect_uploaded_image",
        lambda object_key, bucket_name=None: {
            "ContentLength": 4096,
            "ContentType": "image/webp",
            "Signature": b"RIFFxxxxWEBPVP8 ",
        },
    )
    monkeypatch.setattr(
        videos_module,
        "create_playback_url",
        lambda object_key, expires_in=600: "https://storage.example.test/signed-playback",
    )

    presigned = client.post(
        "/api/v1/uploads/presign",
        json={
            "title": "Uploaded test video",
            "description": "Integration test",
            "category": "Learning",
            "video_format": "short",
            "content_type": "video/mp4",
            "file_size_bytes": 2048,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert presigned.status_code == 201
    assert presigned.json()["method"] == "PUT"
    assert presigned.json()["video_format"] == "short"
    video_id = presigned.json()["video_id"]

    complete = client.post(
        f"/api/v1/uploads/{video_id}/complete",
        headers={"X-CSRF-Token": csrf},
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "ready"

    thumbnail_presign = client.post(
        f"/api/v1/uploads/{video_id}/thumbnail/presign",
        json={"content_type": "image/webp", "file_size_bytes": 4096},
        headers={"X-CSRF-Token": csrf},
    )
    assert thumbnail_presign.status_code == 201
    assert thumbnail_presign.json()["headers"]["Content-Type"] == "image/webp"

    thumbnail_complete = client.post(
        f"/api/v1/uploads/{video_id}/thumbnail/complete",
        headers={"X-CSRF-Token": csrf},
    )
    assert thumbnail_complete.status_code == 200
    assert thumbnail_complete.json()["thumbnail_url"].startswith(
        "https://media.example.test/thumbnails/"
    )

    published = client.post(
        f"/api/v1/videos/{video_id}/publish",
        json={"visibility": "public"},
        headers={"X-CSRF-Token": csrf},
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    playback = client.get(f"/api/v1/videos/{video_id}/playback")
    assert playback.status_code == 200
    assert playback.json()["playback_url"] == "https://storage.example.test/signed-playback"


def test_upload_rejects_unsupported_content_type(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "upload-type@example.com",
            "display_name": "Upload Type",
            "password": "A-very-strong-test-password-8",
        },
    )
    csrf = client.cookies.get("pyyt_csrf")
    invalid_thumbnail = client.post(
        f"/api/v1/uploads/invalid-video/thumbnail/presign",
        json={"content_type": "image/svg+xml", "file_size_bytes": 100},
        headers={"X-CSRF-Token": csrf},
    )
    assert invalid_thumbnail.status_code == 415
    oversized_thumbnail = client.post(
        "/api/v1/uploads/invalid-video/thumbnail/presign",
        json={"content_type": "image/jpeg", "file_size_bytes": 6 * 1024 * 1024},
        headers={"X-CSRF-Token": csrf},
    )
    assert oversized_thumbnail.status_code == 413

    response = client.post(
        "/api/v1/uploads/presign",
        json={
            "title": "Bad file",
            "content_type": "application/octet-stream",
            "file_size_bytes": 100,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 415


def test_thumbnail_complete_rejects_invalid_image_signature_and_cleans_object(client, monkeypatch):
    from db.models import Channel, Video
    from db.session import SessionLocal
    import api.v1.endpoints.uploads as uploads_module

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid-thumbnail@example.com",
            "display_name": "Thumbnail Owner",
            "password": "A-very-strong-test-password-21",
        },
    )
    assert registration.status_code == 201
    owner_id = registration.json()["id"]
    csrf = client.cookies.get("pyyt_csrf")

    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == owner_id).one()
        video = Video(
            channel_id=channel.id,
            title="Thumbnail validation test",
            description="",
            category="General",
            source_type="upload",
            visibility="private",
            status="ready",
        )
        db.add(video)
        db.commit()
        video_id = video.id

    monkeypatch.setattr(uploads_module.settings, "media_public_base_url", "https://media.example.test")
    monkeypatch.setattr(
        uploads_module,
        "inspect_uploaded_image",
        lambda object_key: {
            "ContentLength": 256,
            "ContentType": "image/png",
            "Signature": b"this is not a PNG file",
        },
    )
    deleted = []
    monkeypatch.setattr(uploads_module, "delete_object", lambda object_key, bucket_name=None: deleted.append((object_key, bucket_name)))

    response = client.post(
        f"/api/v1/uploads/{video_id}/thumbnail/complete",
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 422
    assert deleted == [(f"thumbnails/{channel.id}/{video_id}/cover", "pyyt-thumbnails")]

    with SessionLocal() as db:
        saved_video = db.get(Video, video_id)
        assert saved_video.thumbnail_storage_key is None
        assert saved_video.thumbnail_url is None

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

    monkeypatch.setattr(
        uploads_module,
        "create_upload_url",
        lambda object_key, content_type: "https://storage.example.test/presigned-upload",
    )
    monkeypatch.setattr(
        uploads_module,
        "inspect_uploaded_object",
        lambda object_key: {"ContentLength": 2048, "ContentType": "video/mp4"},
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

from db.models import Channel, Video, VideoChapter
from db.session import SessionLocal


def register_user(client, email, name):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": name,
            "password": "A-very-strong-test-password-24",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_video(owner, duration_seconds=600):
    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == owner["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Chapter timeline test",
            description="A video used to test chapter markers.",
            category="Learning",
            source_type="upload",
            storage_key=f"chapter-tests/{owner['id']}/video.mp4",
            mime_type="video/mp4",
            file_size_bytes=2048,
            duration_seconds=duration_seconds,
            visibility="public",
            status="published",
        )
        db.add(video)
        db.commit()
        return video.id


def test_owner_can_replace_public_chapters_and_viewers_can_read(client):
    owner = register_user(client, "chapter-owner@example.com", "Chapter Owner")
    video_id = create_video(owner)
    csrf = client.cookies.get("pyyt_csrf")

    created = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={
            "items": [
                {"start_seconds": 0, "title": "Introduction"},
                {"start_seconds": 90, "title": "Main topic"},
                {"start_seconds": 480, "title": "Summary"},
            ]
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert created.status_code == 200
    assert [item["start_seconds"] for item in created.json()["items"]] == [0, 90, 480]

    listed = client.get(f"/api/v1/videos/{video_id}/chapters")
    assert listed.status_code == 200
    assert [item["title"] for item in listed.json()["items"]] == [
        "Introduction",
        "Main topic",
        "Summary",
    ]

    with SessionLocal() as db:
        assert db.query(VideoChapter).filter(VideoChapter.video_id == video_id).count() == 3

    cleared = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={"items": []},
        headers={"X-CSRF-Token": csrf},
    )
    assert cleared.status_code == 200
    assert cleared.json()["items"] == []


def test_chapter_validation_and_owner_permissions(client):
    owner = register_user(client, "chapter-validation@example.com", "Chapter Validator")
    video_id = create_video(owner)
    csrf = client.cookies.get("pyyt_csrf")

    too_few = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={
            "items": [
                {"start_seconds": 0, "title": "Intro"},
                {"start_seconds": 30, "title": "Ending"},
            ]
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert too_few.status_code == 422

    short_interval = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={
            "items": [
                {"start_seconds": 0, "title": "Intro"},
                {"start_seconds": 9, "title": "Next"},
                {"start_seconds": 30, "title": "Ending"},
            ]
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert short_interval.status_code == 422

    invalid_first = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={"items": [{"start_seconds": 12, "title": "Not the beginning"}]},
        headers={"X-CSRF-Token": csrf},
    )
    assert invalid_first.status_code == 422

    descending = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={
            "items": [
                {"start_seconds": 0, "title": "Intro"},
                {"start_seconds": 120, "title": "Later"},
                {"start_seconds": 60, "title": "Earlier"},
            ]
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert descending.status_code == 422

    duplicate_time = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={
            "items": [
                {"start_seconds": 0, "title": "Intro"},
                {"start_seconds": 0, "title": "Duplicate"},
            ]
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert duplicate_time.status_code == 422

    outside_duration = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={"items": [{"start_seconds": 0, "title": "Intro"}, {"start_seconds": 120, "title": "Middle"}, {"start_seconds": 600, "title": "Past the end"}]},
        headers={"X-CSRF-Token": csrf},
    )
    assert outside_duration.status_code == 422

    short_last_chapter = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={
            "items": [
                {"start_seconds": 0, "title": "Intro"},
                {"start_seconds": 120, "title": "Middle"},
                {"start_seconds": 595, "title": "Ending"},
            ]
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert short_last_chapter.status_code == 422

    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")})
    register_user(client, "chapter-viewer@example.com", "Chapter Viewer")
    viewer_csrf = client.cookies.get("pyyt_csrf")
    forbidden = client.put(
        f"/api/v1/videos/{video_id}/chapters",
        json={"items": [{"start_seconds": 0, "title": "Viewer edit"}]},
        headers={"X-CSRF-Token": viewer_csrf},
    )
    assert forbidden.status_code == 404
    public_list = client.get(f"/api/v1/videos/{video_id}/chapters")
    assert public_list.status_code == 200

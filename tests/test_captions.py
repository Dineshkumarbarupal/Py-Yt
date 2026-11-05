from db.models import Channel, Video, VideoCaption
from db.session import SessionLocal


ENGLISH_VTT = """WEBVTT

00:00:00.000 --> 00:00:02.500
Welcome to Py-Yt.

00:00:03.000 --> 00:00:05.000
This is a caption track.
"""

SPANISH_VTT = """WEBVTT

00:00:00.000 --> 00:00:02.500
Bienvenido a Py-Yt.
"""


def register_user(client, email, name):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": name,
            "password": "A-very-strong-test-password-23",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_public_video(owner):
    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == owner["id"]).one()
        video = Video(
            channel_id=channel.id,
            title="Caption test video",
            description="",
            category="Learning",
            source_type="upload",
            visibility="public",
            status="published",
        )
        db.add(video)
        db.commit()
        video_id = video.id
    return video_id


def test_multilingual_captions_default_language_delivery_and_owner_controls(client):
    owner = register_user(client, "caption-owner@example.com", "Caption Owner")
    video_id = create_public_video(owner)
    csrf = client.cookies.get("pyyt_csrf")

    english = client.put(
        f"/api/v1/videos/{video_id}/captions",
        json={
            "language": "en",
            "label": "English",
            "vtt_content": ENGLISH_VTT,
            "is_default": True,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert english.status_code == 200
    english_id = english.json()["id"]
    assert english.json()["is_default"] is True

    spanish = client.put(
        f"/api/v1/videos/{video_id}/captions",
        json={
            "language": "es",
            "label": "Español",
            "vtt_content": SPANISH_VTT,
            "is_default": True,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert spanish.status_code == 200
    spanish_id = spanish.json()["id"]
    assert spanish.json()["is_default"] is True

    tracks = client.get(f"/api/v1/videos/{video_id}/captions")
    assert tracks.status_code == 200
    assert len(tracks.json()["items"]) == 2
    default_tracks = [item for item in tracks.json()["items"] if item["is_default"]]
    assert [item["language"] for item in default_tracks] == ["es"]

    english_vtt = client.get(f"/api/v1/videos/{video_id}/captions/{english_id}/vtt")
    assert english_vtt.status_code == 200
    assert english_vtt.headers["content-type"].startswith("text/vtt")
    assert english_vtt.text.startswith("WEBVTT")

    invalid = client.put(
        f"/api/v1/videos/{video_id}/captions",
        json={
            "language": "fr",
            "label": "Français",
            "vtt_content": "This is not a WebVTT file.",
            "is_default": False,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert invalid.status_code == 422

    removed = client.delete(
        f"/api/v1/videos/{video_id}/captions/{english_id}",
        headers={"X-CSRF-Token": csrf},
    )
    assert removed.status_code == 204

    client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": client.cookies.get("pyyt_csrf")},
    )
    public_tracks = client.get(f"/api/v1/videos/{video_id}/captions")
    assert public_tracks.status_code == 200
    assert [item["id"] for item in public_tracks.json()["items"]] == [spanish_id]
    public_vtt = client.get(public_tracks.json()["items"][0]["vtt_url"])
    assert public_vtt.status_code == 200
    assert "Bienvenido a Py-Yt." in public_vtt.text

    register_user(client, "caption-viewer@example.com", "Caption Viewer")
    viewer_csrf = client.cookies.get("pyyt_csrf")
    forbidden = client.put(
        f"/api/v1/videos/{video_id}/captions",
        json={
            "language": "de",
            "label": "Deutsch",
            "vtt_content": SPANISH_VTT,
            "is_default": False,
        },
        headers={"X-CSRF-Token": viewer_csrf},
    )
    assert forbidden.status_code == 404

    with SessionLocal() as db:
        assert db.query(VideoCaption).filter(VideoCaption.video_id == video_id).count() == 1

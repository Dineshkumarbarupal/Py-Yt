from db.models import Channel, Video
from db.session import SessionLocal


def test_search_suggestions_include_public_titles_and_channels_only(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "suggestions@example.com",
            "display_name": "Python School",
            "password": "A-very-strong-test-password-20",
        },
    )
    assert registration.status_code == 201

    with SessionLocal() as db:
        channel = db.query(Channel).filter(Channel.owner_id == registration.json()["id"]).one()
        db.add_all([
            Video(
                channel_id=channel.id,
                title="Python automation basics",
                description="A public tutorial",
                category="Technology",
                source_type="upload",
                storage_key=f"suggestions/{registration.json()['id']}/public.mp4",
                mime_type="video/mp4",
                file_size_bytes=256,
                visibility="public",
                status="published",
            ),
            Video(
                channel_id=channel.id,
                title="Python private draft",
                description="Not for public discovery",
                category="Technology",
                source_type="upload",
                storage_key=f"suggestions/{registration.json()['id']}/private.mp4",
                mime_type="video/mp4",
                file_size_bytes=256,
                visibility="private",
                status="published",
            ),
        ])
        db.commit()

    response = client.get("/api/v1/discovery/suggest", params={"q": "Python"})
    assert response.status_code == 200
    items = response.json()["items"]
    labels = {item["label"] for item in items}
    assert "Python automation basics" in labels
    assert "Python School" in labels
    assert "Python private draft" not in labels
    assert all(item["kind"] in {"video", "channel"} for item in items)


def test_search_suggestions_require_at_least_two_characters(client):
    response = client.get("/api/v1/discovery/suggest", params={"q": "p"})
    assert response.status_code == 422

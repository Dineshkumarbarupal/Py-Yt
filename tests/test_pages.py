def test_creator_studio_pages_render(client):
    for path in ["/studio", "/studio/upload", "/studio/content", "/studio/analytics", "/studio/comments", "/settings"]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert "Py-Yt" in response.text, path


def test_viewer_library_pages_render(client):
    for path in ["/subscriptions", "/playlists", "/watch-later", "/liked", "/history"]:
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

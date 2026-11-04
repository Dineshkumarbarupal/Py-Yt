def test_discovery_feed_and_search_are_empty_but_valid(client):
    feed = client.get("/api/v1/discovery/feed")
    assert feed.status_code == 200
    assert feed.json()["items"] == []

    search = client.get("/api/v1/discovery/search", params={"q": "python"})
    assert search.status_code == 200
    assert search.json()["query"] == "python"
    assert search.json()["items"] == []

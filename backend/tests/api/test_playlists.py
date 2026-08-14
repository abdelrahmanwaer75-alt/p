from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _account(prefix: str):
    email = f"{prefix}-{uuid4()}@example.com"
    password = "CorrectHorseBattery12!"
    assert client.post("/api/v1/auth/register", json={"email": email, "password": password}).status_code == 201
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _library_item(headers, title: str):
    response = client.post("/api/v1/library", headers=headers, json={"title": title, "source_url": "https://vimeo.com/123", "media_path": None})
    assert response.status_code == 201
    return response.json()["id"]


def test_playlist_crud_items_and_reorder():
    headers = _account("playlist")
    first = _library_item(headers, "First")
    second = _library_item(headers, "Second")
    created = client.post("/api/v1/playlists", headers=headers, json={"name": "Watch later", "description": "Queue"})
    assert created.status_code == 201
    playlist_id = created.json()["id"]
    assert client.post(f"/api/v1/playlists/{playlist_id}/items", headers=headers, json={"library_item_id": first}).status_code == 200
    updated = client.post(f"/api/v1/playlists/{playlist_id}/items", headers=headers, json={"library_item_id": second}).json()
    assert [item["title"] for item in updated["items"]] == ["First", "Second"]
    ids = [item["id"] for item in updated["items"]]
    reordered = client.post(f"/api/v1/playlists/{playlist_id}/reorder", headers=headers, json={"item_ids": list(reversed(ids))})
    assert reordered.status_code == 200
    assert [item["title"] for item in reordered.json()["items"]] == ["Second", "First"]
    item_id = reordered.json()["items"][0]["id"]
    assert client.delete(f"/api/v1/playlists/{playlist_id}/items/{item_id}", headers=headers).status_code == 200
    assert client.patch(f"/api/v1/playlists/{playlist_id}", headers=headers, json={"name": "Renamed"}).json()["name"] == "Renamed"
    assert client.delete(f"/api/v1/playlists/{playlist_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/playlists", headers=headers).json() == []


def test_playlist_authorization_and_feature_gate():
    owner = _account("playlist-owner")
    other = _account("playlist-other")
    library_id = _library_item(owner, "Private")
    playlist_id = client.post("/api/v1/playlists", headers=owner, json={"name": "Private"}).json()["id"]
    assert client.get(f"/api/v1/playlists/{playlist_id}", headers=other).status_code == 404
    assert client.post(f"/api/v1/playlists/{playlist_id}/items", headers=other, json={"library_item_id": library_id}).status_code == 404
    assert client.patch(f"/api/v1/playlists/{playlist_id}", headers=other, json={"name": "Stolen"}).status_code == 404
    assert client.delete(f"/api/v1/playlists/{playlist_id}", headers=other).status_code == 404
    assert client.post(f"/api/v1/playlists/{playlist_id}/download", headers=owner).status_code == 501

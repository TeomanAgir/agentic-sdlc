import pytest
from fastapi.testclient import TestClient

from app.main import app, reset_state

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_state():
    reset_state()
    yield


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_get_note():
    resp = client.post("/notes", json={"title": "ilk not", "body": "içerik"})
    assert resp.status_code == 201
    note = resp.json()
    assert note["id"] == 1
    assert note["title"] == "ilk not"

    resp = client.get("/notes/1")
    assert resp.status_code == 200
    assert resp.json() == note


def test_list_notes():
    client.post("/notes", json={"title": "a"})
    client.post("/notes", json={"title": "b"})
    resp = client.get("/notes")
    assert resp.status_code == 200
    assert [n["title"] for n in resp.json()] == ["a", "b"]


def test_list_notes_filters_by_title_case_insensitive():
    client.post("/notes", json={"title": "Ilk Not"})
    client.post("/notes", json={"title": "ikinci not"})
    client.post("/notes", json={"title": "baska bir sey"})

    resp = client.get("/notes", params={"q": "NOT"})
    assert resp.status_code == 200
    assert [n["title"] for n in resp.json()] == ["Ilk Not", "ikinci not"]


def test_list_notes_with_no_match_returns_empty_list():
    client.post("/notes", json={"title": "a"})
    resp = client.get("/notes", params={"q": "zzz"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_missing_note_returns_404():
    resp = client.get("/notes/99")
    assert resp.status_code == 404


def test_delete_note():
    client.post("/notes", json={"title": "silinecek"})
    resp = client.delete("/notes/1")
    assert resp.status_code == 204
    assert client.get("/notes/1").status_code == 404


def test_update_note():
    client.post("/notes", json={"title": "eski", "body": "eski gövde"})
    resp = client.put("/notes/1", json={"title": "yeni", "body": "yeni gövde"})
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "title": "yeni", "body": "yeni gövde"}
    assert client.get("/notes/1").json()["title"] == "yeni"


def test_update_missing_note_returns_404():
    resp = client.put("/notes/99", json={"title": "x"})
    assert resp.status_code == 404


def test_delete_missing_note_returns_404():
    resp = client.delete("/notes/99")
    assert resp.status_code == 404


def test_patch_note_updates_only_title():
    client.post("/notes", json={"title": "eski", "body": "eski gövde"})
    resp = client.patch("/notes/1", json={"title": "yeni"})
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "title": "yeni", "body": "eski gövde"}


def test_patch_note_updates_only_body():
    client.post("/notes", json={"title": "eski", "body": "eski gövde"})
    resp = client.patch("/notes/1", json={"body": "yeni gövde"})
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "title": "eski", "body": "yeni gövde"}


def test_patch_note_updates_both_fields():
    client.post("/notes", json={"title": "eski", "body": "eski gövde"})
    resp = client.patch("/notes/1", json={"title": "yeni", "body": "yeni gövde"})
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "title": "yeni", "body": "yeni gövde"}


def test_patch_note_with_empty_body_returns_422():
    client.post("/notes", json={"title": "eski", "body": "eski gövde"})
    resp = client.patch("/notes/1", json={})
    assert resp.status_code == 422
    assert client.get("/notes/1").json() == {
        "id": 1,
        "title": "eski",
        "body": "eski gövde",
    }


def test_patch_note_with_null_field_returns_422():
    client.post("/notes", json={"title": "eski", "body": "eski gövde"})
    resp = client.patch("/notes/1", json={"title": None})
    assert resp.status_code == 422
    assert client.get("/notes/1").json() == {
        "id": 1,
        "title": "eski",
        "body": "eski gövde",
    }


def test_patch_missing_note_returns_404():
    resp = client.patch("/notes/99", json={"title": "x"})
    assert resp.status_code == 404

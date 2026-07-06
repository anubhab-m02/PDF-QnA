import pytest

from tests.test_quiz import _upload_and_wait_ready


@pytest.mark.asyncio
async def test_generate_flashcard_deck(client, auth_headers):
    document_id = await _upload_and_wait_ready(client, auth_headers)

    resp = await client.post(
        f"/api/documents/{document_id}/flashcards",
        headers=auth_headers,
        json={"topic": "biology", "num_cards": 3},
    )
    assert resp.status_code == 201
    deck = resp.json()
    assert deck["document_id"] == document_id
    assert len(deck["flashcards"]) == 3
    for card in deck["flashcards"]:
        assert card["term"]
        assert card["definition"]


@pytest.mark.asyncio
async def test_flashcards_for_missing_document_404(client, auth_headers):
    resp = await client.post("/api/documents/9999/flashcards", headers=auth_headers, json={})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_and_get_flashcard_deck(client, auth_headers):
    document_id = await _upload_and_wait_ready(client, auth_headers)
    resp = await client.post(f"/api/documents/{document_id}/flashcards", headers=auth_headers, json={})
    deck_id = resp.json()["id"]

    resp = await client.get(f"/api/flashcard-decks?document_id={document_id}", headers=auth_headers)
    assert any(d["id"] == deck_id for d in resp.json())

    resp = await client.get(f"/api/flashcard-decks/{deck_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["flashcards"]) == 3

    resp = await client.get(f"/api/flashcard-decks/{deck_id + 999}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_flashcards_require_auth(client):
    resp = await client.post("/api/documents/1/flashcards", json={})
    assert resp.status_code == 401

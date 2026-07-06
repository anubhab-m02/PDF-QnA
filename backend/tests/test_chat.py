import pytest


@pytest.mark.asyncio
async def test_create_session_and_send_message_streams_tokens(client, auth_headers):
    resp = await client.post("/api/chat/sessions", headers=auth_headers, json={"title": "General"})
    assert resp.status_code == 201
    session_id = resp.json()["id"]
    assert resp.json()["document_id"] is None

    resp = await client.post(
        f"/api/chat/sessions/{session_id}/messages",
        headers=auth_headers,
        json={"content": "What is photosynthesis?"},
    )
    assert resp.status_code == 200
    body = resp.text
    assert "event: token" in body
    assert "fake" in body
    assert "event: done" in body

    resp = await client.get(f"/api/chat/sessions/{session_id}/messages", headers=auth_headers)
    messages = resp.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is photosynthesis?"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "fake streamed response"


@pytest.mark.asyncio
async def test_session_scoped_to_document_requires_ownership(client, auth_headers):
    resp = await client.post("/api/chat/sessions", headers=auth_headers, json={"document_id": 9999})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_sessions_and_messages_require_auth(client):
    resp = await client.get("/api/chat/sessions")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_message_to_missing_session_404(client, auth_headers):
    resp = await client.post(
        "/api/chat/sessions/9999/messages", headers=auth_headers, json={"content": "hello"}
    )
    assert resp.status_code == 404

import pytest

from tests.test_quiz import _upload_and_wait_ready


@pytest.mark.asyncio
async def test_generate_summary(client, auth_headers):
    document_id = await _upload_and_wait_ready(client, auth_headers)

    resp = await client.post(f"/api/documents/{document_id}/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["document_id"] == document_id
    assert body["summary"] == "fake response"


@pytest.mark.asyncio
async def test_summary_for_missing_document_404(client, auth_headers):
    resp = await client.post("/api/documents/9999/summary", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_summary_requires_auth(client):
    resp = await client.post("/api/documents/1/summary")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_profile_stats_empty_for_new_user(client, auth_headers):
    resp = await client.get("/api/profile/stats", headers=auth_headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["document_count"] == 0
    assert stats["quiz_attempt_count"] == 0
    assert stats["average_quiz_score_pct"] is None


@pytest.mark.asyncio
async def test_profile_stats_reflect_activity(client, auth_headers):
    document_id = await _upload_and_wait_ready(client, auth_headers)

    resp = await client.post(
        f"/api/documents/{document_id}/quizzes", headers=auth_headers, json={"num_questions": 2}
    )
    quiz = resp.json()
    answers = [q["answer_index"] for q in quiz["questions"]]
    await client.post(
        f"/api/quizzes/{quiz['id']}/attempts", headers=auth_headers, json={"answers": answers}
    )

    await client.post(f"/api/documents/{document_id}/flashcards", headers=auth_headers, json={})

    session_resp = await client.post("/api/chat/sessions", headers=auth_headers, json={})
    session_id = session_resp.json()["id"]
    await client.post(
        f"/api/chat/sessions/{session_id}/messages", headers=auth_headers, json={"content": "hi"}
    )

    resp = await client.get("/api/profile/stats", headers=auth_headers)
    stats = resp.json()
    assert stats["document_count"] == 1
    assert stats["ready_document_count"] == 1
    assert stats["quiz_count"] == 1
    assert stats["quiz_attempt_count"] == 1
    assert stats["average_quiz_score_pct"] == 100.0
    assert stats["flashcard_deck_count"] == 1
    assert stats["chat_session_count"] == 1
    assert stats["message_count"] == 2

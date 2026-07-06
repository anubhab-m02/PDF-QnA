import asyncio

import pytest

from tests.pdf_fixture import build_minimal_pdf


async def _upload_and_wait_ready(client, auth_headers, text="Quiz content about biology") -> int:
    resp = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("quiz.pdf", build_minimal_pdf(text), "application/pdf")},
    )
    document_id = resp.json()["id"]
    for _ in range(20):
        resp = await client.get(f"/api/documents/{document_id}", headers=auth_headers)
        if resp.json()["status"] != "processing":
            break
        await asyncio.sleep(0.05)
    assert resp.json()["status"] == "ready"
    return document_id


@pytest.mark.asyncio
async def test_generate_quiz_and_submit_attempt(client, auth_headers):
    document_id = await _upload_and_wait_ready(client, auth_headers)

    resp = await client.post(
        f"/api/documents/{document_id}/quizzes",
        headers=auth_headers,
        json={"topic": "biology", "num_questions": 3},
    )
    assert resp.status_code == 201
    quiz = resp.json()
    assert quiz["document_id"] == document_id
    assert len(quiz["questions"]) == 3
    for q in quiz["questions"]:
        assert len(q["options"]) == 4
        assert 0 <= q["answer_index"] <= 3

    quiz_id = quiz["id"]
    correct_answers = [q["answer_index"] for q in quiz["questions"]]

    resp = await client.post(
        f"/api/quizzes/{quiz_id}/attempts", headers=auth_headers, json={"answers": correct_answers}
    )
    assert resp.status_code == 201
    attempt = resp.json()
    assert attempt["score"] == 3
    assert attempt["total"] == 3


@pytest.mark.asyncio
async def test_submit_attempt_with_wrong_answers_scores_zero(client, auth_headers):
    document_id = await _upload_and_wait_ready(client, auth_headers)
    resp = await client.post(
        f"/api/documents/{document_id}/quizzes", headers=auth_headers, json={"num_questions": 3}
    )
    quiz = resp.json()
    wrong_answers = [(q["answer_index"] + 1) % 4 for q in quiz["questions"]]

    resp = await client.post(
        f"/api/quizzes/{quiz['id']}/attempts", headers=auth_headers, json={"answers": wrong_answers}
    )
    attempt = resp.json()
    assert attempt["score"] == 0
    assert attempt["total"] == 3


@pytest.mark.asyncio
async def test_quiz_for_missing_document_404(client, auth_headers):
    resp = await client.post("/api/documents/9999/quizzes", headers=auth_headers, json={})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_and_get_quiz(client, auth_headers):
    document_id = await _upload_and_wait_ready(client, auth_headers)
    resp = await client.post(f"/api/documents/{document_id}/quizzes", headers=auth_headers, json={})
    quiz_id = resp.json()["id"]

    resp = await client.get(f"/api/quizzes?document_id={document_id}", headers=auth_headers)
    assert any(q["id"] == quiz_id for q in resp.json())

    resp = await client.get(f"/api/quizzes/{quiz_id}", headers=auth_headers)
    assert resp.status_code == 200

    resp = await client.get(f"/api/quizzes/{quiz_id + 999}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_quiz_requires_auth(client):
    resp = await client.post("/api/documents/1/quizzes", json={})
    assert resp.status_code == 401

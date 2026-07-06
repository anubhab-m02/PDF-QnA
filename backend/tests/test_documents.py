import asyncio

import pytest

from tests.pdf_fixture import build_minimal_pdf


@pytest.mark.asyncio
async def test_upload_document_ingests_and_becomes_ready(client, auth_headers):
    pdf_bytes = build_minimal_pdf("Hello World")

    resp = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 201
    document = resp.json()
    assert document["status"] == "processing"

    for _ in range(20):
        resp = await client.get(f"/api/documents/{document['id']}", headers=auth_headers)
        if resp.json()["status"] != "processing":
            break
        await asyncio.sleep(0.05)

    final = resp.json()
    assert final["status"] == "ready"
    assert final["chunk_count"] >= 1
    assert final["page_count"] == 1


@pytest.mark.asyncio
async def test_upload_rejects_non_pdf(client, auth_headers):
    resp = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_requires_auth(client):
    resp = await client.post(
        "/api/documents",
        files={"file": ("test.pdf", build_minimal_pdf(), "application/pdf")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_upload_rejected(client, auth_headers):
    pdf_bytes = build_minimal_pdf("Same content")
    resp1 = await client.post(
        "/api/documents", headers=auth_headers, files={"file": ("a.pdf", pdf_bytes, "application/pdf")}
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/api/documents", headers=auth_headers, files={"file": ("b.pdf", pdf_bytes, "application/pdf")}
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_list_and_delete_document(client, auth_headers):
    pdf_bytes = build_minimal_pdf("Deletable")
    resp = await client.post(
        "/api/documents", headers=auth_headers, files={"file": ("c.pdf", pdf_bytes, "application/pdf")}
    )
    document_id = resp.json()["id"]

    resp = await client.get("/api/documents", headers=auth_headers)
    assert any(d["id"] == document_id for d in resp.json())

    resp = await client.delete(f"/api/documents/{document_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/api/documents/{document_id}", headers=auth_headers)
    assert resp.status_code == 404

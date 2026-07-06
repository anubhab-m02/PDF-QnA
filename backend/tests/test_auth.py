import pytest


@pytest.mark.asyncio
async def test_register_login_me(client):
    resp = await client.post("/api/auth/register", json={"username": "alice", "password": "hunter2pass"})
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    resp = await client.post("/api/auth/login", json={"username": "alice", "password": "hunter2pass"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


@pytest.mark.asyncio
async def test_duplicate_username_rejected(client):
    await client.post("/api/auth/register", json={"username": "bob", "password": "hunter2pass"})
    resp = await client.post("/api/auth/register", json={"username": "bob", "password": "otherpassword"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_wrong_password_rejected(client):
    await client.post("/api/auth/register", json={"username": "carol", "password": "hunter2pass"})
    resp = await client.post("/api/auth/login", json={"username": "carol", "password": "wrongpassword"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401

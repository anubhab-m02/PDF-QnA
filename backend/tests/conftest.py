import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.db.session import get_db, get_session_factory
from app.main import create_app
from app.services.gemini import get_gemini_service
from app.services.vector_store import get_vector_store
from tests.fakes import FakeGeminiService, FakeVectorStore


@pytest.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_gemini_service] = lambda: FakeGeminiService()
    app.dependency_overrides[get_vector_store] = lambda: FakeVectorStore()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await engine.dispose()


@pytest.fixture
async def auth_headers(client):
    resp = await client.post("/api/auth/register", json={"username": "docuser", "password": "docuserpass"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, Document, User


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_user_document_relationship(db_session: AsyncSession):
    user = User(username="alice", password_hash="hashed")
    db_session.add(user)
    await db_session.flush()

    doc = Document(
        user_id=user.id,
        filename="paper.pdf",
        title="Paper",
        sha256="abc123",
    )
    db_session.add(doc)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.username == "alice"))
    fetched = result.scalar_one()
    assert fetched.id == user.id

    result = await db_session.execute(select(Document).where(Document.user_id == user.id))
    fetched_doc = result.scalar_one()
    assert fetched_doc.status == "processing"

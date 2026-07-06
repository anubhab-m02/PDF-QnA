from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.flashcards import router as flashcards_router
from app.api.quiz import router as quiz_router
from app.api.study import router as study_router
from app.core.config import DATA_DIR, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "uploads").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "chroma").mkdir(parents=True, exist_ok=True)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="PDF-QnA API", version="2.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(documents_router)
    app.include_router(chat_router)
    app.include_router(quiz_router)
    app.include_router(flashcards_router)
    app.include_router(study_router)

    return app


app = create_app()

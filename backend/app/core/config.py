from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    google_api_key: str = ""
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    database_url: str = f"sqlite+aiosqlite:///{DATA_DIR / 'app.db'}"
    chroma_dir: str = str(DATA_DIR / "chroma")
    uploads_dir: str = str(DATA_DIR / "uploads")

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dims: int = 768


@lru_cache
def get_settings() -> Settings:
    return Settings()

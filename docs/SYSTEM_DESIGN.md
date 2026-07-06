# System Design — PDF-QnA v2

**Status:** Approved · **Date:** 2026-07-06 · **Author:** anubhab-m02
**Scope:** Full rewrite of the Streamlit PDF-QnA prototype into a local-first FastAPI + Next.js application.

---

## 1. Requirements

### 1.1 Functional
| # | Requirement | Priority |
|---|-------------|----------|
| F1 | User registration/login with local accounts | P0 |
| F2 | Upload PDF documents; extract, chunk, embed, and index their text | P0 |
| F3 | Streaming RAG chat scoped to a document, with source citations | P0 |
| F4 | Persistent chat sessions and message history | P0 |
| F5 | Quiz generation (5 MCQs) from a document, with attempts and scoring history | P1 |
| F6 | Flashcard deck generation from a document | P1 |
| F7 | One-shot document summarization | P1 |
| F8 | Profile stats (documents, quizzes taken, average score) | P1 |
| F9 | Read-aloud via browser SpeechSynthesis (no backend) | P2 |
| F10 | Translation of answers/summaries via Gemini | P2 (backlog) |

**Cut from v1:** email sharing (SMTP spam/abuse surface, credential liability), server-side gTTS audio (replaced by F9), matplotlib complexity charts (low value), TF-IDF key concepts (backlog).

### 1.2 Non-functional
- **Deployment:** single Mac, local-only. No Docker, no cloud infra. Two processes: `uvicorn` (:8000) and `next dev`/`next start` (:3000).
- **Scale:** one user class (the owner), a few concurrent sessions at most. Design for tens of documents, thousands of chunks — not millions.
- **Latency targets:** first streamed token < 3 s; 50-page PDF ingested < 60 s; quiz generation < 15 s.
- **Reliability:** LLM/API failures must degrade gracefully (typed errors, retry affordance in UI) — never a stack trace to the client.
- **Security:** no secrets in git; no pickle deserialization; hashed passwords (bcrypt); JWT-scoped resources (every query filtered by `user_id`).

### 1.3 Constraints
- Solo developer; incremental one-feature commits.
- Gemini API is the only external dependency (`gemini-2.5-flash` for generation, `gemini-embedding-001` for embeddings).
- Legacy Streamlit app stays runnable in `src/` until parity, then moves to `legacy/streamlit/`.

---

## 2. High-Level Architecture

```
┌────────────────────┐         ┌─────────────────────────────────┐
│  Next.js 15 (:3000)│  CORS   │        FastAPI (:8000)          │
│  App Router, TS,   ├────────▶│  /api/*  (JWT Bearer auth)      │
│  Tailwind, shadcn  │  fetch  │                                 │
│                    │◀────────┤  SSE stream for chat            │
└────────────────────┘         └───────┬──────────┬──────────────┘
                                       │          │
                          ┌────────────▼───┐  ┌───▼────────────────┐
                          │ SQLite (WAL)   │  │ ChromaDB           │
                          │ data/app.db    │  │ PersistentClient   │
                          │ users, docs,   │  │ data/chroma/       │
                          │ chats, quizzes │  │ chunk vectors +    │
                          └────────────────┘  │ metadata filters   │
                                              └───┬────────────────┘
                                       ┌──────────▼──────────┐
                                       │  Gemini API         │
                                       │  gemini-2.5-flash   │
                                       │  gemini-embedding-  │
                                       │  001 (768 dims)     │
                                       └─────────────────────┘
```

**Key decisions (trade-offs in §7):**
- Browser calls FastAPI **directly with CORS** (`localhost:3000` and `127.0.0.1:3000` both allowed). SSE is never proxied through Next.js rewrites (they buffer).
- **ChromaDB embedded** (`PersistentClient`) as the vector store: pure-local single-directory persistence, SQLite-backed (no pickle), first-class metadata `where` filters for `{user_id, document_id}` scoping.
- **SQLite in WAL mode** via async SQLAlchemy (`aiosqlite`): fine for a single-machine, low-concurrency app; migrations via Alembic.
- **Ingestion via FastAPI `BackgroundTasks`** with a status field the frontend polls. No job queue — unnecessary at this scale.

---

## 3. Data Model

```
User 1──* Document 1──* (chunks live in Chroma, not SQL)
User 1──* ChatSession 1──* Message
User 1──* Quiz 1──* QuizAttempt
User 1──* FlashcardDeck 1──* Flashcard
Document 1──* ChatSession / Quiz / FlashcardDeck (nullable for chat)
```

| Table | Columns |
|-------|---------|
| `users` | id PK, username TEXT UNIQUE NOT NULL, password_hash TEXT, created_at |
| `documents` | id PK, user_id FK, filename, title, page_count, chunk_count, sha256, status ENUM(processing/ready/failed), error TEXT NULL, created_at |
| `chat_sessions` | id PK, user_id FK, document_id FK NULL, title, created_at |
| `messages` | id PK, session_id FK, role ENUM(user/assistant), content TEXT, sources_json TEXT NULL, created_at |
| `quizzes` | id PK, user_id FK, document_id FK, topic, questions_json TEXT, created_at |
| `quiz_attempts` | id PK, quiz_id FK, user_id FK, answers_json TEXT, score INT, total INT, created_at |
| `flashcard_decks` | id PK, user_id FK, document_id FK, title, created_at |
| `flashcards` | id PK, deck_id FK, term TEXT, definition TEXT, position INT |

**Chunks are not in SQL.** Each chunk lives in Chroma with its embedding and metadata `{user_id, document_id, page, chunk_index}`; document deletion issues a Chroma `delete(where={"document_id": ...})` plus SQL cascade.

`sha256` on documents enables upload dedupe (re-upload of identical file returns the existing document).

---

## 4. API Design

All routes under `/api`, JSON in/out, `Authorization: Bearer <JWT>` except auth endpoints. Errors use a consistent envelope: `{"detail": str, "code": str}` (e.g. `code="document_not_ready"`); internal exceptions are logged server-side and mapped to safe messages.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/register` | Create account → `{token, user}` |
| POST | `/api/auth/login` | Verify credentials → `{token, user}` |
| GET | `/api/auth/me` | Current user from token |
| POST | `/api/documents` | Multipart PDF upload → 202 `{id, status: "processing"}`; ingestion in background |
| GET | `/api/documents` | List user's documents with status |
| GET | `/api/documents/{id}` | Detail (poll target during processing) |
| DELETE | `/api/documents/{id}` | Delete SQL rows + Chroma vectors + stored file |
| POST | `/api/documents/{id}/summary` | Generate summary (non-streaming) |
| POST | `/api/chat/sessions` | Create session `{document_id?, title?}` |
| GET | `/api/chat/sessions` | List sessions |
| GET | `/api/chat/sessions/{id}/messages` | Message history |
| POST | `/api/chat/sessions/{id}/messages` | Send user message → **SSE stream** of assistant tokens, final event carries sources + persisted message id |
| POST | `/api/documents/{id}/quizzes` | Generate quiz (structured output) |
| GET | `/api/quizzes` / `/api/quizzes/{id}` | List/detail (answers withheld until attempted) |
| POST | `/api/quizzes/{id}/attempts` | Submit answers → scored result + explanations |
| POST | `/api/documents/{id}/flashcards` | Generate deck (structured output) |
| GET | `/api/flashcard-decks` / `/{id}` | List/detail |
| GET | `/api/profile/stats` | Aggregate counts + recent quiz scores |

**SSE protocol** (via `sse-starlette`): events `token` (text delta), `sources` (JSON array of `{document_id, page, snippet}`), `done` (message id), `error` (safe message). Client uses `fetch` + ReadableStream parsing because `EventSource` cannot send Authorization headers.

---

## 5. Core Pipelines

### 5.1 Ingestion (background task)
```
upload → save to data/uploads/{sha256}.pdf → status=processing
  → pypdf extract per page
  → recursive character chunking (~1000 chars, 150 overlap), page metadata kept
  → gemini-embedding-001, output_dimensionality=768, batched ≤100 per call
  → chroma.add(ids, embeddings, documents, metadatas)
  → status=ready (page_count, chunk_count)   |   on any failure: status=failed + safe error
```
Chroma's sync client is called via `run_in_threadpool` to avoid blocking the event loop. The chunker is hand-rolled (~40 lines) — no LangChain dependency in v2.

### 5.2 RAG chat
```
user message → embed query → chroma.query(k=6, where={user_id, document_id})
  → prompt = system rules + numbered context blocks [page refs] + recent turns + question
  → client.aio.models.generate_content_stream(gemini-2.5-flash)
  → stream tokens over SSE → persist user + assistant messages with sources_json
```
Prompt rules instruct the model to answer only from context and cite block numbers; retrieved page metadata becomes the citation payload.

### 5.3 Structured generation (quiz / flashcards)
Pydantic schemas are passed as `response_schema` with `response_mime_type="application/json"`:
```python
class QuizQuestion(BaseModel):
    question: str
    options: list[str]          # exactly 4
    answer_index: int           # 0-3
    explanation: str
```
This eliminates the v1 failure class of string-parsing LLM output. Responses are validated with Pydantic before persisting; a single retry with the validation error appended covers rare malformed outputs.

### 5.4 Auth
- Register/login → bcrypt (`bcrypt` package directly, cost 12) → PyJWT HS256 access token, 7-day expiry, `sub=user_id`. No refresh tokens (local app).
- FastAPI dependency `get_current_user` decodes the token and loads the user; every repository query filters by `user_id`.
- v1 credentials are **not migrated**: the old `users.db` was tracked in git (compromised by definition); users re-register.

---

## 6. Error Handling, Observability, Reliability

- **Exception hierarchy:** `AppError(code, status, safe_message)` subclasses (`NotFoundError`, `NotReadyError`, `LLMError`, `AuthError`) → one FastAPI exception handler renders the envelope. Unknown exceptions → 500 `{"detail": "Internal error", "code": "internal"}` + full traceback to logs only.
- **Logging:** stdlib `logging` to stderr + `logs/app.log` (RotatingFileHandler, 5 MB × 3). Request logging via uvicorn access logs. No in-memory StringIO logger (v1's unbounded-growth bug).
- **LLM resilience:** timeouts on all Gemini calls (30 s generation, 60 s embedding batch); one retry on transient 5xx/timeout; structured-output validation retry as above.
- **Data safety:** SQLite WAL; multi-step writes in transactions; Chroma and SQL deletes ordered so an interrupted delete leaves recoverable state (SQL row survives until vectors are gone).
- **No silent data expiry:** v1's 24-hour index auto-delete is removed. Documents persist until the user deletes them.

---

## 7. Trade-offs & Revisit Triggers

| Decision | Alternative | Why this way | Revisit when |
|----------|-------------|--------------|--------------|
| SQLite + aiosqlite | Postgres | Zero-ops local install; WAL handles this concurrency | Multi-user hosting |
| Chroma embedded | LanceDB, sqlite-vec, FAISS | No pickle, metadata filters, no server; FAISS rejected (pickle RCE, no filters) | >1M chunks or multi-process access |
| BackgroundTasks | Celery/RQ + broker | No broker to run locally; ingestion is minutes at worst | Long jobs, retries-with-backoff needs |
| JWT in localStorage | httpOnly cookie sessions | Simplest with a separate SPA origin; XSS risk accepted at localhost | Public deployment |
| Direct CORS calls | Next.js API proxy | Proxy buffers SSE and doubles hops | Deploying behind one origin |
| Fresh user table | Migrate pbkdf2 hashes | Old DB was in git → treat as breached; solo app, re-registering is free | Never (verifiable via `hashlib.pbkdf2_hmac` if ever needed) |
| No rate limiting | slowapi middleware | Localhost-only, single user | Any network exposure |

---

## 8. Directory Layout (backend)

```
backend/
├── app/
│   ├── main.py                # app factory, CORS, exception handlers, lifespan
│   ├── core/config.py         # pydantic-settings ← backend/.env
│   ├── core/security.py       # bcrypt hash/verify, JWT encode/decode, get_current_user
│   ├── db/session.py          # async engine sqlite+aiosqlite:///../data/app.db
│   ├── db/models.py           # SQLAlchemy 2.0 mapped classes (§3)
│   ├── schemas/               # pydantic request/response models per domain
│   ├── api/                   # routers: auth, documents, chat, quiz, flashcards, study
│   └── services/              # gemini, chunking, ingestion, vector_store, rag, quiz, flashcards, summary
├── alembic/                   # migrations (sync sqlite:/// URL)
├── tests/                     # pytest + httpx ASGITransport + FakeGemini override
├── requirements.txt           # pinned
└── .env                       # GOOGLE_API_KEY, JWT_SECRET (gitignored)
```

## 9. Testing Strategy

- **Unit/integration:** pytest + `httpx.AsyncClient(transport=ASGITransport(app))`. `conftest.py` provides a tmp SQLite DB, tmp Chroma dir, and a `FakeGemini` dependency override (deterministic embeddings, canned stream chunks, canned structured JSON) — tests never touch the network.
- **Frontend gates:** `tsc --noEmit` and `npm run build`.
- **Smoke:** `scripts/smoke.sh` — health → register → login → upload fixture PDF → poll ready → chat → quiz → attempt. Required before declaring v1 parity.

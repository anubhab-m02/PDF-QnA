# PRD — PDF-QnA v2

**Date:** 2026-07-06 · **Owner:** anubhab-m02 · **Status:** Approved
**Companion docs:** [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) (architecture), [DESIGN_HANDOFF.md](DESIGN_HANDOFF.md) (UI spec)

---

## 1. Problem Statement

The v1 Streamlit app proves the concept — study PDFs through RAG chat, quizzes, and flashcards — but it is a prototype: quiz/flashcard generation silently fails on LLM formatting drift, the index self-deletes after 24 hours, credentials leaked into git, and the single-page Streamlit UI reruns the whole app on every interaction. The cost of staying on v1 is unreliable study sessions (lost quizzes, vanished documents) and a codebase too fragile to extend.

v2 rebuilds the product on a real client/server architecture so every feature is reliable, fast, and extensible — while staying a zero-ops local app.

## 2. Goals

1. **Reliability of generation:** 0 parse failures across quiz/flashcard generation (structured output), measured over any 20 consecutive generations.
2. **Persistent knowledge base:** documents and their indexes persist until explicitly deleted (v1 deleted them after 24 h).
3. **Responsive study loop:** first streamed chat token < 3 s; 50-page PDF ready < 60 s; quiz generated < 15 s.
4. **Security baseline:** no secrets or user data in git; no pickle deserialization; per-user resource scoping enforced on every endpoint.
5. **Full v1-parity for core study features** (chat, quiz, flashcards, summary, history) on the new stack, verified by the smoke script.

## 3. Non-Goals

- **Multi-tenant / hosted deployment** — this is a single-owner local tool; Postgres, rate limiting, and managed vector DBs are deferred until hosting is a real need.
- **Docker/containerization** — explicitly rejected by the owner; two local processes are the deployment model.
- **Mobile app or mobile-optimized UI** — desktop-first; the `md` collapse is a courtesy only.
- **Email/document sharing** — v1's SMTP sharing is cut: spam/abuse surface, credential liability, near-zero value for a solo user.
- **Server-side audio (gTTS)** — replaced by the browser's built-in SpeechSynthesis at zero backend cost.
- **Non-PDF formats (epub, docx, web pages)** — architectural insurance only: keep extraction behind one function so formats can be added later.

## 4. Persona

**The Solo Learner (the owner).** Studies technical/academic PDFs in focused sessions on a Mac. Wants to drop a paper in, interrogate it conversationally with page-level citations, then self-test with quizzes and flashcards. Values: nothing lost between sessions, no infra babysitting, honest errors when something fails.

## 5. User Stories

**P0**
- As a learner, I want to create a local account and log in so that my documents and history are mine and persist across sessions.
- As a learner, I want to upload a PDF and see its processing status so that I know when it's ready to study.
- As a learner, I want to ask questions about a document and watch the answer stream in with page citations so that I can verify claims against the source.
- As a learner, I want my chat sessions saved per document so that I can resume where I left off.
- As a learner, I want a clear error (not a crash or silence) when a PDF fails to process or the model errs, so that I can retry deliberately.

**P1**
- As a learner, I want a 5-question MCQ quiz generated from my document so that I can test my understanding.
- As a learner, I want my quiz attempts scored and stored with explanations so that I can track improvement over time.
- As a learner, I want flashcard decks generated from a document so that I can revise key terms quickly.
- As a learner, I want a one-click summary of a document so that I can triage what to read deeply.
- As a learner, I want a profile page with my stats and history so that I can see my progress at a glance.

**P2**
- As a learner, I want answers read aloud in the browser so that I can listen while multitasking.
- As a learner, I want translations of answers/summaries so that I can study in another language.

## 6. Requirements

### P0 — Must-Have
| # | Requirement | Acceptance criteria |
|---|-------------|---------------------|
| R1 | Local auth (register/login/me), bcrypt + JWT | Given a registered user, when they log in with correct credentials, then they receive a token that authorizes all `/api/*` calls; wrong password → 401 envelope; duplicate username → 409. Usernames unique at the DB level. |
| R2 | PDF upload + background ingestion with status | Upload returns 202 with `status=processing`; polling reflects `ready` (with page/chunk counts) or `failed` (with safe error); identical re-upload (sha256) returns existing document; non-PDF or >50 MB rejected with 422. |
| R3 | Streaming RAG chat with citations | Given a `ready` document, when the user sends a message, then tokens stream via SSE and the completed answer lists page-level sources; retrieval is filtered to that user+document; both messages persist. |
| R4 | Chat session persistence | Sessions list/create/resume; history loads on open; deleting a document cascades its sessions. |
| R5 | Typed error envelope everywhere | All errors return `{detail, code}`; no stack traces or raw exception text ever reach the client (negative test in suite). |

### P1 — Nice-to-Have (built in v2, after P0)
| # | Requirement | Acceptance criteria |
|---|-------------|---------------------|
| R6 | Quiz generation via structured output | 5 questions, exactly 4 options each, valid `answer_index`, explanation present — schema-validated before persisting; one retry on validation failure; 20 consecutive generations produce 0 unparseable quizzes. |
| R7 | Quiz attempts & scoring | Submitting answers returns score + per-question correctness + explanations; attempt stored; history lists attempts with scores. |
| R8 | Flashcard decks | Deck of 8–12 term/definition pairs, schema-validated; stored and listable per document. |
| R9 | Document summary | Returns a summary for any `ready` document; length capped; safe error if model fails. |
| R10 | Profile stats | Counts (documents, quizzes, decks) and average/recent quiz scores from real queries. |

### P2 — Future Considerations
- Browser TTS (SpeechSynthesis) on chat answers — frontend-only, no API.
- Gemini-powered translation endpoint (drops v1's deep_translator).
- Key-concept extraction; non-PDF sources; export (Anki/CSV).

## 7. Success Metrics

**Leading (evaluate at parity + 1 week):**
- Smoke script (`scripts/smoke.sh`) passes end-to-end: health → register → login → upload → ready → chat → quiz → attempt.
- 0 quiz/flashcard parse failures in 20 consecutive generations.
- Latency targets met on a 50-page PDF (ingest < 60 s, first token < 3 s, quiz < 15 s).
- `pytest` suite green; `npm run build` + `tsc --noEmit` clean.

**Lagging (evaluate at parity + 1 month):**
- v1 fully retired to `legacy/` with no feature the owner misses (parity checklist in §6 all checked).
- 0 incidents of lost documents/sessions (v1's index expiry class of bugs).
- Repo hygiene holds: no secrets, no DBs, no artifacts committed since v2 start.

## 8. Timeline & Phasing

No hard deadline; milestones map to the build order, each ending in a working, committed state (one-line commits per working feature).

| Milestone | Contents | Exit criterion |
|-----------|----------|----------------|
| M0 Hygiene | users.db untracked, .gitignore fixed, deps pinned, LICENSE, CLAUDE.md | clean `git status`, docs merged |
| M1 Docs | SYSTEM_DESIGN, DESIGN_HANDOFF, PRD_V2 | this document set committed |
| M2 Backend core | scaffold, models+migrations, auth (R1) | pytest green, curl auth flow |
| M3 Knowledge base | upload/ingestion (R2) | fixture PDF reaches `ready` |
| M4 Chat | RAG SSE chat + sessions (R3, R4) | `curl -N` streams; history persists |
| M5 Study tools | quiz (R6, R7), flashcards (R8), summary (R9), stats (R10) | curl round-trips |
| M6 Frontend | scaffold, auth UI, library, chat, quiz, flashcards, profile | browser flows work |
| M7 Parity & polish | error/empty states, browser TTS, README, smoke.sh, `src/` → `legacy/` | smoke green; parity checklist done |

**Dependencies:** rotated Google API key in `backend/.env` before M3 (ingestion needs embeddings); Node 22 LTS recommended before M6.

## 9. Open Questions

- **(Owner, non-blocking)** Should quiz history from v1's `users.db` be viewable read-only anywhere, or fully abandoned? Current decision: abandoned (file kept locally as archive).
- **(Owner, non-blocking)** Accent color preference — spec says indigo; trivially swappable via tokens.
- **(Engineering, non-blocking)** Whether to add `slowapi` rate limiting behind a config flag now vs. when the app is ever exposed beyond localhost. Current decision: defer.

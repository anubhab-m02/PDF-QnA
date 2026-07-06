# Design Handoff — PDF-QnA v2 Frontend

**Stack:** Next.js 15 (App Router) · TypeScript · Tailwind CSS · shadcn/ui · lucide-react icons
**Date:** 2026-07-06 · Companion docs: [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md), [PRD_V2.md](PRD_V2.md)

---

## 1. Overview

A focused study workspace: the user uploads PDFs into a **Library**, then works with one document at a time in **Chat**, **Quiz**, or **Flashcards** views, with a **Profile** page for history and stats. Desktop-first (it runs locally on a Mac); one collapse breakpoint for narrow windows. Calm, content-forward aesthetic: neutral surfaces, a single accent color, generous whitespace, no decorative gradients.

## 2. App Shell & Layout

```
┌──────┬──────────────────────────────────────┐
│ Side │  Top bar (page title · theme toggle) │
│ bar  ├──────────────────────────────────────┤
│ 240px│  Main pane                           │
│      │  max-w-4xl centered, px-6 py-8       │
│ nav  │                                      │
│ ...  │                                      │
│ user │                                      │
└──────┴──────────────────────────────────────┘
```

- **Sidebar** (`w-60`, `border-r`, `bg-sidebar`): logo/wordmark top; nav items Library, Profile; below a "Current document" section listing per-document tools (Chat, Quiz, Flashcards) enabled only when a document is selected; user block pinned bottom (username, logout).
- **Nav item states:** default `text-muted-foreground`; hover `bg-accent text-foreground`; active `bg-accent text-foreground font-medium` with a 2px accent-colored left indicator.
- **Auth pages** ((auth) route group): no shell — centered `Card` `max-w-sm` on `bg-muted/40`.
- **Grid:** main pane single column; Library uses a responsive card grid `grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4`.

## 3. Design Tokens

Use shadcn CSS variables everywhere — never raw hex in components. Dark mode via `class` strategy, toggle in top bar, persisted in `localStorage`.

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--background` | zinc-50 | zinc-950 | app background |
| `--foreground` | zinc-900 | zinc-50 | body text |
| `--card` | white | zinc-900 | cards, panels |
| `--primary` | indigo-600 | indigo-400 | CTAs, active states, links |
| `--primary-foreground` | white | zinc-950 | text on primary |
| `--muted` / `--muted-foreground` | zinc-100 / zinc-500 | zinc-800 / zinc-400 | secondary surfaces/text |
| `--destructive` | red-600 | red-400 | delete, errors |
| `--border` / `--ring` | zinc-200 / indigo-600 | zinc-800 / indigo-400 | borders, focus rings |
| `--radius` | 0.5rem | — | all corners |

**Typography:** Geist Sans (via `next/font`), mono for citations/code. Scale: page title `text-2xl font-semibold`; section `text-lg font-medium`; body `text-sm` (Tailwind default `leading-6`); captions `text-xs text-muted-foreground`.
**Spacing:** Tailwind scale; sections separated by `space-y-6`; card internals `p-4`/`p-6`.
**Semantic status colors:** processing `amber-500`, ready `emerald-500`, failed `red-500` (Badge variants).

## 4. Component Inventory

| Component | Source | Props / notes |
|-----------|--------|---------------|
| Button, Input, Label, Card, Dialog, Tabs, Badge, Skeleton, Progress, Separator, DropdownMenu, Sheet, Tooltip | shadcn/ui | stock variants |
| Toast | `sonner` | bottom-right; errors persist until dismissed, successes auto-dismiss 4 s |
| `UploadDropzone` | custom | drag-over `border-primary bg-primary/5`; accepts `.pdf` only, max 50 MB; click = file picker |
| `DocumentCard` | custom | title (truncate 2 lines), page/chunk counts, `StatusBadge`, kebab menu (Delete → confirm Dialog) |
| `StatusBadge` | custom | processing (amber, pulsing dot) / ready (emerald) / failed (red, tooltip shows safe error) |
| `ChatBubble` | custom | user: `bg-primary text-primary-foreground` right-aligned `max-w-[75%]`; assistant: `bg-card border` left-aligned, markdown rendered |
| `SourceChip` | custom | pill `text-xs bg-muted font-mono` "p. 12"; click opens Dialog with the snippet |
| `StreamingCursor` | custom | 2px pulsing block appended to streaming assistant text |
| `QuizQuestionCard` | custom | question + 4 option rows (radio-style buttons); reveal state colors correct emerald / chosen-wrong red + explanation block |
| `FlipCard` | custom | term face / definition face; 3D flip on click/Enter/Space |
| `ScoreRing` | custom | SVG circular progress for quiz results (≥80% emerald, ≥50% amber, else red) |

## 5. Screens: states & interactions

### 5.1 Login / Register
- Fields: username, password (register adds confirm). Submit: loading spinner in Button, all inputs disabled.
- Error: envelope `detail` shown in a destructive `Alert` above the form (e.g. "Username already taken"); field borders `border-destructive`.
- Success: store token, redirect to `/library`. Links cross-reference the two pages.

### 5.2 Library
- **Empty:** centered illustration-free empty state — `FileText` icon `text-muted-foreground`, "No documents yet", "Upload a PDF to start learning", dropzone directly below.
- **Uploading:** optimistic `DocumentCard` with `Progress` (upload) → `StatusBadge processing`; grid polls `GET /api/documents` every 2.5 s while any card is processing, stops when none.
- **Ready:** card click → `/documents/{id}/chat`. Hover: `shadow-md` lift, 150 ms ease-out.
- **Failed:** red badge, tooltip with safe error, kebab → Delete or Retry (re-upload).
- **Delete:** confirmation Dialog ("Deletes the document, its chats, quizzes and flashcards. This cannot be undone."), destructive Button, toast on success.

### 5.3 Chat
- Header: document title + session switcher (DropdownMenu, "New session").
- Message list `overflow-y-auto`, newest pinned to bottom; auto-scroll only if user is already at bottom.
- **Empty session:** 3 suggested-question chips (static prompts like "Summarize the key ideas") — click sends.
- **Streaming:** tokens append to an assistant `ChatBubble` with `StreamingCursor`; input and Send disabled; Stop button replaces Send (aborts fetch).
- **Done:** `SourceChip` row under the bubble from the `sources` SSE event.
- **Error mid-stream:** partial text kept, inline destructive caption "Response interrupted — Retry" (button re-sends).
- Input: textarea autogrows to 6 rows; Enter sends, Shift+Enter newline; 4000-char limit with counter after 3500.

### 5.4 Quiz
- **Start:** "Generate quiz" Button; loading state = 5 stacked Skeleton cards (generation ≤ 15 s).
- **Taking:** one `QuizQuestionCard` at a time, `Progress` bar "Question 2 of 5"; option select highlights (`border-primary bg-primary/5`); Next disabled until a choice; last question → Submit.
- **Results:** `ScoreRing` + per-question review (correct/wrong coloring + explanations). Actions: "New quiz", "Back to document".
- **History:** table below start screen — date, score badge (same thresholds as ScoreRing), row click opens past attempt review.

### 5.5 Flashcards
- **Empty:** "Generate flashcards" CTA; loading = 1 Skeleton card.
- **Study:** centered `FlipCard` (min-h 260px), "3 / 10" counter, Prev/Next; flip 300 ms ease-in-out `rotateY`; keyboard ← → navigate, Space/Enter flips.
- Deck list (if >1 deck): simple list with created date.

### 5.6 Profile
- Stat cards row: Documents, Quizzes taken, Average score, Flashcard decks.
- Recent quiz scores as compact list with score badges; chat sessions list with relative timestamps ("2 h ago").
- Logout: secondary Button, confirmation not required (re-login is cheap).

## 6. Responsive Behavior

| Breakpoint | Changes |
|------------|---------|
| ≥ 1024px | Default layout, fixed 240px sidebar |
| 768–1024px | Main pane padding `px-4`; library grid naturally reflows |
| < 768px (`md` collapse) | Sidebar becomes a `Sheet` (hamburger in top bar); chat bubbles `max-w-[90%]`; this is a courtesy, not a mobile product (PRD non-goal) |

## 7. Motion

| Element | Trigger | Animation | Duration / easing |
|---------|---------|-----------|-------------------|
| Card hover | pointer | shadow + translateY(-1px) | 150 ms ease-out |
| FlipCard | click/key | rotateY 180° | 300 ms ease-in-out |
| StatusBadge dot | processing | opacity pulse | 1.2 s loop |
| Streaming cursor | while streaming | opacity pulse | 800 ms loop |
| Dialog/Sheet | open | shadcn defaults (fade+zoom / slide) | stock |
| Quiz answer reveal | submit | background color transition | 200 ms ease |

Respect `prefers-reduced-motion`: disable flip rotation (crossfade instead) and pulses.

## 8. Edge Cases

- **Long titles/filenames:** truncate with `line-clamp-2` (cards) / `truncate` (headers); full value in Tooltip.
- **Large chat history:** render latest 100 messages, "Load earlier" button prepends.
- **Slow LLM:** if no first token in 10 s, show "Still thinking…" caption; fetch timeout at 60 s → error state.
- **Token expiry (7 d):** any 401 → clear token, redirect to login with toast "Session expired".
- **Backend down:** typed fetch wrapper surfaces a global toast "Can't reach the server — is the backend running?" (this is a local app; say so plainly).
- **International/long strings:** all containers `min-w-0` + wrap; no fixed-width text boxes.

## 9. Accessibility (WCAG 2.1 AA)

- **Focus:** visible `ring-2 ring-ring ring-offset-2` on all interactive elements; focus order follows visual order; Dialog/Sheet trap focus and restore on close.
- **Chat streaming:** message list `aria-live="polite"`; announce completion, not every token (wrap streaming text, announce final).
- **Quiz:** options are a `radiogroup` with arrow-key navigation; result announces score via `aria-live`.
- **FlipCard:** `role="button"`, `aria-pressed` for flipped state, `aria-label="Flashcard: {term}. Press Enter to reveal definition"`.
- **StatusBadge:** text + color (never color alone); processing badge `aria-busy`.
- **Forms:** `Label` bound to every Input; errors linked via `aria-describedby`.
- **Contrast:** token pairs above meet AA (4.5:1 body, 3:1 large text) in both themes; verify with the theme toggle during review.
- **Keyboard completeness:** every flow (upload via picker, chat, quiz, flashcards, delete) operable without a pointer.

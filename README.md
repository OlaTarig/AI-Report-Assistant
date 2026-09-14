# AI Report Assistant

Private AI-powered report writing app for an agricultural quality-inspection
business. React/TypeScript frontend, FastAPI backend, PostgreSQL, Gemini
for AI (via a swappable provider abstraction).

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop (for Postgres)
- A Gemini API key: https://aistudio.google.com/apikey

## Setup

### 1. Postgres

```bash
docker compose up -d
```

**If you already have Postgres installed natively on your machine**, it's
likely also listening on port 5432, which will conflict with this
container. If so, edit `docker-compose.yml`'s `ports:` line to something
like `"5433:5432"`, and match that port in `backend/.env`'s
`DATABASE_URL` (see below).

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: paste your GEMINI_API_KEY, and fix DATABASE_URL's port if
# you changed it above
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs to confirm the server is running.

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000.

## Project layout

```
backend/app/
  main.py                        FastAPI entrypoint, registers all routers
  config.py                      Settings loaded from .env
  database.py                    Async SQLAlchemy engine/session
  models/                        Conversation, Message, UploadedFile, Report, ReportVersion
  schemas/                       Pydantic request/response + AI structured-output schemas
  api/
    conversations.py              CRUD for conversations
    messages.py                   Send a message -> AI structured call -> persist + patch report
    files.py                      Upload/list files
    reports.py                    Get current report, export to Word
    chat.py                       Phase-1 debug endpoint (stateless, no persistence)
  services/
    ai/                           AIProvider abstraction, GeminiProvider, prompts, schema conversion
    documents/                    Per-file-type extraction (pdf/docx/excel/image)
    files/                        Storage (sanitized filenames) + type dispatch
    reports/                      Patch-merge logic + docx export
  migrations/                    Alembic (async-engine setup)

frontend/src/
  App.tsx                        Top-level state and wiring
  components/                    ConversationList, ChatPanel, FileUpload
  api/                           Typed clients per resource
  types/                         Shared TS types mirroring backend schemas
```

## How report editing works

Every message sends the AI the current report content (as JSON) plus the
conversation history, and asks it to return BOTH a conversational reply
and a *patch* (only the sections that changed, not the whole report) in
one structured call. The backend merges that patch into the report's
current content and saves a new version — this is what lets "make the
intro shorter" only touch the intro instead of regenerating everything.

## Known limitations (accepted for this scope)

- **All files re-sent every message**: every uploaded file's extracted
  text is included in every AI call for that conversation, not just
  files relevant to the current message. Fine at low file counts; would
  get expensive with many/large files in one conversation.
- **Stop button doesn't cancel server-side work**: clicking Stop aborts
  the browser's wait, but the Gemini call keeps running on the backend
  and its result is still saved — it just won't appear until you reopen
  the conversation.
- **No real authentication**: single shared app, not per-user secured.
  `user_id` columns exist but are unused, ready for future auth.
- **PDF heading detection is a heuristic** (font-size relative to page
  median), not exact — unusual PDF formatting (e.g. bold instead of
  larger text for headings) may not be detected correctly.
- **Report versioning has no UI**: every edit creates a new
  `report_versions` row (so history is retained in the database), but
  there's no restore/compare screen yet.

## Troubleshooting

- **"password authentication failed" from Alembic/Postgres**: almost
  always a native Postgres install competing for port 5432 — see the
  Postgres setup note above.
- **CORS errors in the browser**: confirm the backend is running on
  port 8000 — Vite's dev server proxies `/api` there.
- **AI request fails with a schema/validation error**: check
  `backend/app/services/ai/schema_utils.py` is present and imported in
  `gemini_provider.py` — Gemini's structured output needs the
  Pydantic schema flattened (no `$ref`/`$defs`) before it's sent.

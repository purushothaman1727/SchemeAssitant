# Scheme Assistant: Government Scheme Assistance Chatbot (RAG)

An **independent** tool that helps people in India find government schemes (Central and Tamil Nadu) that
may fit their circumstances. It collects only the details a scheme's rules need, checks them with a
deterministic eligibility engine, retrieves official source text with RAG, and explains the result in
**English or Tamil** through a grounded chatbot.

> **This is not an official government service.** It does not submit applications, has no access to any
> government database, and its results are preliminary. Always confirm with the official source linked on
> each scheme.

## How it works

```
 profile ─► validation ─► eligibility engine (rules, no LLM) ─► ranked scheme cards
                                   │
                                   ▼
 question ─► retrieval (ChromaDB, multilingual embeddings) ─► grounded LLM answer + citations
                                   │
                                   ▼
                    guards: cited sources only, no invented numbers,
                    no "I submitted…" claims, otherwise fall back to verified records
```

- **The engine decides, the LLM explains.** Eligibility status comes only from verified rules in
  `data/schemes.json`. The model can never change it.
- **Honest about gaps.** Rules from unofficial sources are stored but flagged `verified: false`; they can
  never produce "does not match". Unverifiable schemes are reported as "information unverified".
- **Grounded answers.** Every factual reply cites a scheme record `[S#]` or a document passage `[E#]`.
  Answers with unknown citations, numbers absent from the sources, or false action claims are replaced by a
  deterministic answer built from the records.

## Features

- Multi-step profile form with conditional disability questions and a parent/guardian path
- 20 scheme records (15 Central, 5 Tamil Nadu), each with source URLs, check date and verification flags
- Four statuses: *potentially eligible*, *more information required*, *does not match known criteria*,
  *information unverified*, each with reasons and the missing facts
- Recommendation ranking (eligibility, relevance, state, evidence, completeness; no benefit amounts)
- RAG over official PDFs and pages: extraction, sentence-aware chunking, de-duplication, versioning,
  injection-flagging, neighbour-context retrieval
- English and Tamil UI and chat (query translated for retrieval, answer in the chosen language)
- Admin API and UI: JWT login, ingestion jobs, source status, scheme/rule editing with validation
- Privacy by default: answers stay in the browser tab, chat history stored only on opt-in with deletion
  and a retention purge job
- Accessible, responsive UI with a self-hosted font stack

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, React Hook Form |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Database | SQLite (local) / PostgreSQL 16 (Docker Compose) |
| Retrieval | ChromaDB, `fastembed` (ONNX, no PyTorch) with `paraphrase-multilingual-MiniLM-L12-v2`, PyMuPDF, BeautifulSoup |
| LLM | Groq by default (OpenAI-compatible); also any OpenAI-compatible API or Ollama |
| Quality | pytest, Vitest |

## Project layout

```
backend/app/
  api/            routes: health, schemes, profile, recommendations, chat, admin
  eligibility/    deterministic rules engine (no network, no LLM)
  rag/            extract, chunk, embed, store, ingest, retrieve
  services/       recommendation ranking, grounded chat, LLM client, retention, seed
  models/ schemas/ core/ scripts/
backend/alembic/  database migrations
frontend/src/     pages, components, i18n (English/Tamil), services
data/             schemes.json, sample_profiles.json, documents/ (manifest + official PDFs),
                  VERIFICATION_REPORT.md
tests/            backend test suite
docker-compose.yml, .env.example
requirements.txt (runtime), requirements-dev.txt (adds pytest)
```

## Quick start (local, SQLite)

Prerequisites: Python 3.12, Node 20+.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # Linux/macOS: .venv/bin/pip
cp .env.example .env                                 # then edit (see Configuration)

export PYTHONPATH=backend
python -m app.scripts.ingest                         # seeds schemes, downloads the embedding model (~200 MB), ingests sources
python -m app.scripts.create_admin                   # optional: prompts for an admin password (12+ chars)

# terminal 1: API (http://localhost:8000, docs at /docs)
python -m uvicorn app.main:app --port 8000

# terminal 2: web app (http://127.0.0.1:5173, proxies /api to :8000)
cd frontend && npm install && npm run dev
```

Without an LLM key the chat still works: it returns deterministic answers built from the verified records
and retrieved passages, and says the AI assistant is unavailable.

> For a local SQLite run, delete or comment out `DATABASE_URL` in `.env`. The PostgreSQL URL in
> `.env.example` is meant for Docker Compose.

### Docker Compose (PostgreSQL)

```bash
cp .env.example .env     # set POSTGRES_PASSWORD, JWT_SECRET, LLM_API_KEY; APP_ENV=production
docker compose up --build                  # app at http://localhost:8080
docker compose run --rm backend python -m app.scripts.ingest
docker compose run --rm -e ADMIN_PASSWORD='...' backend python -m app.scripts.create_admin
```

The Compose file validates, but the images were **not built or run** during development (no Docker
daemon available). Treat the first build as untested. The migration was verified on SQLite only.

## Configuration

See `.env.example`. Key settings:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `groq` (default), `openai_compatible`, `ollama`, `none` |
| `LLM_API_KEY`, `LLM_MODEL` | Groq key and model (default `openai/gpt-oss-120b`; list yours with `GET https://api.groq.com/openai/v1/models`) |
| `EMBEDDING_BACKEND` | `fastembed` (default) or `hashing` (offline fallback used by the tests; do not mix it with an index built by `fastembed`) |
| `DATABASE_URL` | SQLite by default; PostgreSQL URL for Compose |
| `JWT_SECRET` | required in production; the app refuses the dev default |
| `*_RETENTION_DAYS`, `RATE_LIMIT_*` | privacy retention and rate limits |

Never commit `.env`; it is git-ignored.

## API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | none | liveness + DB check |
| GET | `/api/schemes` | none | list/search/filter, paginated |
| GET | `/api/schemes/{id}` | none | scheme with rules (verified flags) and sources |
| POST | `/api/profile/validate` | none | validate/normalise a profile (stores nothing) |
| POST | `/api/recommendations` | none | eligibility + ranking (stores nothing) |
| POST | `/api/chat` | none | grounded Q&A, English/Tamil (rate limited) |
| DELETE | `/api/chat/sessions/{id}` | session id | erase a saved conversation |
| POST | `/api/admin/login` | none | bearer token (5/min limit) |
| POST | `/api/admin/ingest` | admin | start ingestion |
| GET | `/api/admin/sources`, `/api/admin/ingestion-jobs` | admin | source and job status |
| POST/PATCH | `/api/admin/schemes[/{id}]` | admin | create/update schemes, rules, sources |

Interactive docs: `http://localhost:8000/docs`.

## Adding or updating a scheme

1. Read the **official** source (scheme page, guideline PDF, circular). Do not rely on aggregators.
2. Add the entry to `data/schemes.json` (or `POST /api/admin/schemes`). Mark a rule `verified: true` only
   if you read the value in an official document. The API rejects verified rules on an unverified scheme.
3. Add sources to `data/documents/manifest.json`, then `python -m app.scripts.ingest --scheme <id>`.
4. Add a boundary test in `tests/test_eligibility.py` and, if useful, a profile in
   `data/sample_profiles.json`.

`python -m app.scripts.seed` reloads `data/schemes.json` and overwrites database edits for those ids, so
treat the file as the source of truth.

## Data verification

The scheme data was checked against official pages and documents on **13 October 2026**. Result:
**7 verified, 9 partially verified, 4 unverified.** Several official sites could not be reached from the
verification environment, and those schemes are marked rather than guessed. Details, source limitations and
the replacements made to the original list are in [`data/VERIFICATION_REPORT.md`](data/VERIFICATION_REPORT.md).

Rules and scheme amounts can change; re-verify before relying on them.

## Testing

```bash
pip install -r requirements-dev.txt                 # runtime deps + pytest
export PYTHONPATH=backend && python -m pytest -q     # backend: 240 passed, 1 xpassed
cd frontend && npm test                              # frontend: 14 tests
```

Covered: all 20 records, eligibility boundaries and composite categories, children/adults/undisclosed
disability, unverified rules, state restrictions, retrieval and attribution, hallucination guards, API
validation, admin auth and rate limiting, ingestion failures, persistence, retention.

The dependency files were verified by installing `requirements-dev.txt` into a brand-new virtual
environment and running the full backend suite there.

The `xpassed` test documents a known limit: numeric rules inside PDF tables are not reliably retrievable
with the real embedding model, so they come from the verified structured data instead.

## Privacy

- Profiles live in the browser tab's session storage and are sent to the API only to compute results.
- Chat history is stored only if the user opts in, expires after `CHAT_RETENTION_DAYS`, and can be deleted.
- No names, phone numbers, Aadhaar/UDID numbers, passwords or document images are collected.
- Only profile fields relevant to the schemes under discussion are sent to the LLM provider.
- Retrieved document text is treated as untrusted data.

This is engineering guidance, not legal advice. Review the DPDP Act 2023 obligations (notice, consent
records, grievance contact, cross-border transfer to the LLM provider) before any public launch.

## Known limitations

- 4 schemes are unverified and 9 partially verified.
- `accepting_applications` is unknown for every scheme except UDID.
- Tamil UI strings and canned replies are drafts and need native-speaker review; official Tamil scheme
  names (`name_ta`) are not yet filled in.
- The retrieval index must be rebuilt (`ingest`) if `EMBEDDING_MODEL` changes; there is no re-index command.
- Browser testing was limited to Edge; no formal accessibility audit has been done.
- Docker images and PostgreSQL were not run in development.

## License

No license has been chosen yet. Until one is added, all rights are reserved by the author.

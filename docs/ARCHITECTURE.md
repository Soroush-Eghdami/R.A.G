# Architecture — Local RAG v2

## System overview

```
┌─────────────────────┐      HTTP/SSE (text/event-stream)      ┌──────────────────────────────┐
│   React + Vite UI   │  <====================================>   Django REST backend        │
│   http://:5173      │                                        │   http://:8000               │
│                     │                                        │                              │
│  • Knowledge bases  │                                        │  llm app:  /api/health/     │
│  • Document upload  │                                        │         /api/models/        │
│  • Chat + citations │                                        │         /api/settings/      │
│  • Dark/light theme │                                        │  kb app:   /api/kb/         │
│                     │                                        │         /api/documents/     │
└─────────────────────┘                                        │  chat app: /api/conversations│
                                                               │         /api/messages/       │
                                                               └──────────────────────────────┘
                                                                       │
                                                                  Ollama HTTP API
                                                                       │
                                                                       ▼
                                                          ┌─────────────────────┐
                                                          │      Ollama         │
                                                          │  chat + embeddings  │
                                                          │  qwen3.5:9b         │
                                                          │  nomic-embed-text   │
                                                          │  embeddinggemma     │
                                                          │  all-minilm         │
                                                          └─────────────────────┘
```

The frontend talks only to Django. Django talks to Ollama. Nothing calls Ollama
directly from the browser. No data ever leaves the machine.

## Backend apps

### `llm` — system surface
- `GET /api/health/` — backend + Ollama reachability, version, base URL
- `GET /api/models/` — installed models split into `chat` / `embedding`, plus
  `cloud_hidden` count (`:cloud` models are hidden by default)
- `GET/PATCH /api/settings/` — app defaults: default chat model, default
  embedding model, top_k, temperature, num_ctx. `ollama_base_url` is exposed
  read-only (deployment config, not app config).

### `kb` — knowledge bases and ingestion
- `GET/POST /api/knowledge-bases/` — list, create, filter
- `GET/PATCH/DELETE /api/knowledge-bases/{id}/` — detail; embedding model is
  locked after a document is indexed
- `POST /api/documents/` — upload; sha256 dedupe (returns 202), queued for
  background ingestion
- `GET /api/documents/?knowledge_base=<id>` — list documents with status
- `DELETE /api/documents/{id}/` — remove file + vectors
- `POST /api/kb/{id}/search/` — retrieval-only endpoint (no model call),
  useful for tuning

### `chat` — conversations and answers
- `GET/POST /api/conversations/` — list/create; title set from first question
- `GET/PATCH/DELETE /api/conversations/{id}/` — detail; `chat_model` can be
  switched per conversation (PATCH)
- `POST /api/conversations/{id}/messages/` — ask; SSE stream:
  `sources` → `token`* → `done` (or `error`); non-streaming JSON fallback with
  `stream: false`

### `rag/` — framework-free RAG engine
The `rag/` package imports no Django. Django apps call into it.

- `loaders/` — txt, md, docx, pdf (PyMuPDF, one block per page)
- `chunking.py` — fixed-size chunks: 900 chars, 120 overlap (configurable)
- `embedder.py` — OllamaEmbedder; prefix table for nomic-style models
- `vectorstore.py` — Chroma (cosine), one collection per KB
- `retriever.py` — top-k + max_distance guard (0.65 loose)
- `prompts.py` — SYSTEM_PROMPT: answer only from context, say "I don't know"
  when missing, cite inline like [1], no source list at the end
- `pipeline.py` — `answer_stream()`: rewrite follow-ups → retrieve → budget
  context → stream model output as SSE events (`sources`, `token`,
  `thinking`, `done`, `error`)

## Data flow

### 1. Upload → ingest
1. File is hashed (sha256) for dedupe; duplicate returns 409
2. Document row created with status `pending`, saved to `media/`
3. Ingestion is queued on a single `ThreadPoolExecutor(max_workers=1)`;
   SQLite WAL + `busy_timeout=20000` avoids writer contention
4. Worker loads, chunks, embeds, stores in Chroma; document marked `ready` or
   `failed` with a friendly error message

### 2. Ask → answer
1. Question is embedded; top-k chunks retrieved from Chroma (cosine distance)
2. Context budget: `num_ctx − reserve_output_tokens`; system prompt + question
   fixed cost; history gets 25% of remaining budget; chunks fill the rest
3. If the question looks like a follow-up (short, pronoun-heavy, or follow-up
   prefix) and history exists, it is rewritten into a standalone query using
   the same `num_ctx` as the answer (avoids a double model reload: 21s → ~6s)
4. `SYSTEM_PROMPT` + numbered context + recent history + question are sent to
   Ollama; answer streams back as SSE events
5. Assistant message is saved with `sources` attached so the UI can cite

## Ports and networking

| Service | Port | Bind |
|---------|------|------|
| Django backend | 8000 | `127.0.0.1` |
| Vite frontend (dev) | 5173 | `127.0.0.1` |
| Ollama | 21434 | `127.0.0.1` (host, fixed) |

Ollama port 21434 is permanent — Windows dynamic TCP exclusion ranges forced
this port, and the Ollama tray app ignores `OLLAMA_HOST`, so autostart was
replaced by a scheduled task (`"Ollama 21434"`) plus a helper script.

## Docker

`docker compose up --build` starts backend and frontend containers. Ollama stays
on the host; containers reach it at `host.docker.internal:21434` via
`OLLAMA_BASE_URL`.

## Configuration (`.env`, `django-environ`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | *(required)* | Django secret key |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:21434` | Ollama endpoint |
| `OLLAMA_CONNECT_TIMEOUT` | `5` | Seconds |
| `OLLAMA_REQUEST_TIMEOUT` | `600` | Seconds |
| `DEFAULT_TOP_K` | `4` | Chunks per answer |
| `DEFAULT_TEMPERATURE` | `0.2` | Model temperature |
| `DEFAULT_NUM_CTX` | `8192` | Context window (tokens) |
| `DEFAULT_THINK` | `false` | Enable thinking mode by default |
| `REWRITE_FOLLOWUPS` | `true` | Rewrite follow-up questions |
| `MODEL_CACHE_TTL` | `30` | Model list cache (seconds) |
| `SHOW_CLOUD_MODELS` | `false` | Hide `:cloud` models |
| `STARTUP_RECOVERY` | `true` | Recover stuck docs on first request |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max file upload size |

## Known risks and mitigations

| Risk | Mitigation |
|------|------------|
| Embedding model mismatch | Model locked per KB; explicit re-index via new KB |
| Default context too small | Always send `num_ctx`; budget chunks to fit |
| Missing embedding prefixes | Prefix table in `embedder.py` |
| `runserver` auto-reload kills ingestion | Lazy singleton Chroma client; recover stuck docs on first request; `--noreload` |
| Long streaming requests | SSE headers, `X-Accel-Buffering: no`, 600s Ollama timeout |
| Chroma + SQLite drift | Delete both in one service function; `reconcile` management command |
| Scanned PDFs (no text) | `EmptyDocument` → document marked `failed` with clear message |
| Huge uploads | Max upload size; stream to disk; page-by-page processing |
| Thinking models leak `think` text | `thinking` events filtered from UI unless toggle enabled |
| Ollama not running | Typed errors → 503 + friendly UI banner |
| Exposing beyond localhost | Bind `127.0.0.1`; document it; auth only if opened up |

## Testing

- Backend: `pytest` — 126 tests, mocked Ollama, fast and deterministic
- Frontend: `vitest` — SSE parser tests, 8 cases

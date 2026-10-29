# Architecture

## Overview

```
+----------------+      HTTP/SSE       +---------------------------+
|   React UI     | <==================> |   Django REST backend     |
|  (Vite 5173)   |                      |   (Django 8000)           |
+----------------+                      +---------------------------+
                                                  |
                                                  | Ollama HTTP API
                                                  | (host:21434)
                                                  v
                                          +---------------+
                                          |   Ollama      |
                                          | qwen3.5:9b    |
                                          | nomic-embed   |
                                          +---------------+
```

The frontend talks only to Django. Django talks to Ollama. Nothing calls Ollama
directly from the browser.

## Backend apps

- **`llm`** — Ollama health (`/api/health/`), model discovery (`/api/models/`),
  app settings (`GET/PATCH /api/settings/`).
- **`kb`** — Knowledge bases, document upload, background ingestion,
  retrieval/search.
- **`chat`** — Conversations, messages, SSE answer stream.
- **`rag/`** — Framework-free RAG engine: loaders, chunking, embedder, vector
  store, retriever, prompts, pipeline. Django apps call into it; it imports no
  Django.

## Data flow

1. **Upload** — file is hashed (sha256) for dedupe, stored on disk, ingestion is
   queued on a single-threaded pool.
2. **Ingest** — PDF/Docx/TXT/Markdown is loaded, split into 900-char chunks with
   120-char overlap, embedded with Ollama, stored in Chroma (cosine distance).
3. **Ask** — question is embedded, top-k chunks retrieved from Chroma, system
   prompt + context + history + question are sent to Ollama, answer streams back
   as SSE events (`sources` → `token`* → `done`).
4. **Follow-ups** — short or pronoun-heavy questions are rewritten into a
   standalone query before retrieval (heuristic gate, reuses `num_ctx` to avoid
   model reload).

## Configuration

All runtime config comes from `.env` via `django-environ`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:21434` | Ollama endpoint |
| `OLLAMA_CONNECT_TIMEOUT` | `5` | Connect timeout (seconds) |
| `OLLAMA_REQUEST_TIMEOUT` | `600` | Request timeout (seconds) |
| `DEFAULT_TOP_K` | `4` | Chunks per answer |
| `DEFAULT_TEMPERATURE` | `0.2` | Model temperature |
| `DEFAULT_NUM_CTX` | `8192` | Context window |
| `DEFAULT_THINK` | `false` | Enable thinking mode by default |
| `REWRITE_FOLLOWUPS` | `true` | Rewrite follow-up questions |
| `MODEL_CACHE_TTL` | `30` | Model list cache (seconds) |
| `SHOW_CLOUD_MODELS` | `false` | Hide `:cloud` models |
| `STARTUP_RECOVERY` | `true` | Recover stuck docs on first request |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max file upload size |
| `SECRET_KEY` | *(required)* | Django secret key |

## Ports

- `8000` — Django backend
- `5173` — Vite frontend (dev only)
- `21434` — Ollama on the host (fixed; Windows dynamic TCP exclusion ranges)

## Docker

`docker compose up --build` starts backend + frontend. Ollama stays on the host;
containers reach it at `host.docker.internal:21434`.

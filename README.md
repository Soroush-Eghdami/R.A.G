# Local RAG (v2)

Your documents. Your models. Your machine.

A private, local-only retrieval-augmented generation app: Django REST backend,
React + Vite frontend, Ollama for inference. No accounts. No cloud. Nothing
leaves your box.

```
┌─────────────┐     HTTP/SSE      ┌─────────────────────────┐
│   React UI  │  <================>   Django REST backend   │
│  (port 5173)│                   │   (port 8000)           │
└─────────────┘                   └─────────────────────────┘
                                                │
                                           Ollama HTTP API
                                                │
                                                ▼
                                         ┌───────────┐
                                         | Ollama    |
                                         | any chat  |
                                         | any embed |
                                         └───────────┘
```

## What it does

- **Upload** PDFs, Word docs, Markdown, or plain text to a knowledge base.
  Files are hashed (sha256) so you never upload the same document twice.
- **Ask** questions about your documents. Answers cite the exact passages they
  used, inline like [1], [2].
- **Stream** answers token-by-token as they're generated, with a source drawer
  that shows file, page, and a match score for each citation.
- **Switch** chat models per conversation from the model dropdown — anything
  installed in Ollama shows up automatically.
- **Follow-up questions** are rewritten into standalone queries before
  retrieval, so "explain that more simply" still finds the right chunks.
- **Dark/light theme** toggle, persisted to your browser.
- **Settings** for default top-k, temperature, and context window.

## Stack

| Layer | Tech |
|-------|------|
| Backend | Django 5.2 + Django REST Framework |
| RAG engine | Framework-free `rag/` package (no Django imports) |
| LLM / Embeddings | Ollama — you pick the chat and embedding models |
| Vector store | Chroma (cosine similarity) |
| Frontend | React 19 + Vite + TanStack Query + Tailwind CSS |
| Database | SQLite (WAL mode) |

## Quick start

**Terminal 1 — backend**

```powershell
# from the repo root
.\venv\Scripts\Activate.ps1        # or: source venv/bin/activate
Copy-Item .env.example .env        # then set SECRET_KEY
pip install -r backend\requirements-dev.txt

python backend\manage.py migrate
python run.py                      # Django on http://127.0.0.1:8000
```

**Terminal 2 — frontend**

```powershell
cd frontend
npm install
npm run dev                        # Vite on http://127.0.0.1:5173
```

Open http://127.0.0.1:5173. Vite proxies `/api` to Django, so no CORS setup
is needed.

**Docker** — Ollama stays on your host (port 21434); backend and frontend run
in containers:

```powershell
docker compose up --build
```

Backend: http://localhost:8000 · Frontend: http://localhost:5173

## First steps in the UI

1. **Create a knowledge base** — give it a name and pick an embedding model
   from your installed Ollama models. The model is locked after indexing, so
   pick carefully.
2. **Upload documents** — drag in PDFs, Word files, Markdown, or text. They're
   indexed in the background; watch the status badges go from "Queued" to
   "Processing" to "Ready."
3. **Start a chat** — pick your knowledge base and a chat model, then ask
   anything. Answers cite the sources they used; click a citation to open the
   source drawer.
4. **Change models mid-chat** — use the model dropdown in the header. The
   switch applies to that conversation only.
5. **Tune defaults** — visit Settings to set the default chat model, embedding
   model, chunks per answer, temperature, and context window.

## Requirements

- Python 3.13
- Node.js 22+
- [Ollama](https://ollama.com) running locally on `127.0.0.1:21434` with at
  least one chat model and one embedding model of your choice:

```powershell
# examples — install whichever models you want to use:
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

## Testing

```powershell
# Backend
cd backend
..\venv\Scripts\python.exe -m pytest -q

# Frontend
cd frontend
npm run test
```

## API

Live docs at http://127.0.0.1:8000/api/docs/ (Swagger UI) and the raw schema
at http://127.0.0.1:8000/api/schema/.

Key endpoints:

| Endpoint | What it does |
|----------|--------------|
| `GET /api/health/` | Backend + Ollama status |
| `GET /api/models/` | Installed chat and embedding models |
| `GET/PATCH /api/settings/` | App defaults (top-k, temperature, context) |
| `GET/POST /api/knowledge-bases/` | List and create knowledge bases |
| `POST /api/documents/` | Upload a file to a knowledge base |
| `POST /api/conversations/{id}/messages/` | Ask a question (SSE stream) |

## Config

Runtime config comes from `.env` via `django-environ`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:21434` | Ollama endpoint |
| `DEFAULT_TOP_K` | `4` | Chunks per answer |
| `DEFAULT_TEMPERATURE` | `0.2` | Model temperature |
| `DEFAULT_NUM_CTX` | `8192` | Context window |
| `REWRITE_FOLLOWUPS` | `true` | Rewrite follow-up questions |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max file upload size |

`SECRET_KEY` is required — set it in `.env` before running.

## Deep dive

For the technical architecture — data flow, ports, risks and mitigations —
see `docs/ARCHITECTURE.md`.

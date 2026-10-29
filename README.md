# Local RAG (v2)

A private, local-only retrieval-augmented generation app. Django REST backend,
React + Vite frontend, Ollama for models. No accounts, no cloud, nothing leaves
your machine.

## What it does

- Upload PDFs, Word docs, Markdown or text files to a knowledge base
- Ask questions about your documents; answers cite the exact passages they used
- Stream answers token-by-token with citations and sources
- Switch chat models per conversation; follow-up questions are rewritten into
  standalone queries so pronoun-heavy questions still retrieve the right chunks
- Dark/light theme, settings for defaults (top-k, temperature, context window)

## Stack

| Layer | Tech |
|-------|------|
| Backend | Django 5.2 + Django REST Framework |
| RAG engine | Framework-free `rag/` package (chunking, embeddings, Chroma vector store) |
| LLM | Ollama (chat + embedding models) |
| Frontend | React 19 + Vite + TanStack Query + Tailwind CSS |
| Database | SQLite (WAL mode) |

## Requirements

- Python 3.13
- Node.js 22+
- [Ollama](https://ollama.com) running locally on `127.0.0.1:21434` with at least
  one chat model and one embedding model:

```powershell
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

## Quick start

**Terminal 1 — backend:**

```powershell
# from the repository root
.\venv\Scripts\Activate.ps1      # or source venv/bin/activate on Linux/macOS
Copy-Item .env.example .env       # then set SECRET_KEY
pip install -r backend\requirements-dev.txt

python backend\manage.py migrate
python run.py                     # Django on http://127.0.0.1:8000
```

**Terminal 2 — frontend:**

```powershell
cd frontend
npm install
npm run dev                       # Vite on http://127.0.0.1:5173
```

Open http://127.0.0.1:5173. The dev server proxies `/api` to Django, so no CORS
setup is needed.

## Using Docker

Ollama stays on your host (port 21434). Backend and frontend run in containers:

```powershell
docker compose up --build
```

Backend: http://localhost:8000 — Frontend: http://localhost:5173

## Project layout

```
backend/        Django apps: chat, kb, llm + the framework-free rag/ package
frontend/       React + Vite + TanStack Query app
scripts/        dev.ps1 / ui.ps1 / test.ps1 helper scripts
docs/           Architecture and operations notes
```

## API

Interactive docs at http://127.0.0.1:8000/api/docs/ (Swagger UI) and the raw
OpenAPI schema at http://127.0.0.1:8000/api/schema/.

Key endpoints:

- `GET /api/health/` — backend + Ollama status
- `GET /api/models/` — installed chat and embedding models
- `GET/PATCH /api/settings/` — app defaults (top-k, temperature, context window)
- `GET/POST /api/knowledge-bases/` — list and create knowledge bases
- `POST /api/documents/` — upload a file to a knowledge base
- `POST /api/conversations/{id}/messages/` — ask a question (SSE stream)

## Testing

```powershell
# Backend
cd backend
..\venv\Scripts\python.exe -m pytest -q

# Frontend
cd frontend
npm run test
```

## Phases

This is v2, built in phases:

- **Phase 0–4:** Backend skeleton, RAG engine, ask/stream API
- **Phase 5:** Follow-up rewriting, auto-titles, per-conversation models
- **Phase 6:** Frontend for knowledge bases and settings
- **Phase 7:** Streaming chat UI with citations, dark/light mode
- **Phase 8:** Hardening and tests (this release)
- **Phase 9:** Packaging, Docker, README, v2.0.0 tag

# Local RAG (v2)

A local, document-agnostic retrieval-augmented generation app: Django REST
backend, React frontend, Ollama for models. No accounts, no cloud, no data
leaving the machine.

> Status: **Phase 6 complete** — backend, RAG engine and the browser UI for
> knowledge bases and settings. Chat UI lands next.

## Requirements

- Python 3.13
- Node.js 22+ (frontend, from Phase 6)
- [Ollama](https://ollama.com) running locally with at least one chat model and
  one embedding model, e.g.:

```bash
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

## Quick start

```powershell
# from the repository root
.\venv\Scripts\Activate.ps1
Copy-Item .env.example .env      # then set SECRET_KEY
pip install -r backend\requirements-dev.txt

python backend\manage.py migrate
python backend\manage.py createsuperuser
python run.py
```

Backend: http://127.0.0.1:8000 - Admin: http://127.0.0.1:8000/admin/ -
API docs: http://127.0.0.1:8000/api/docs/

Frontend (second terminal):

```powershell
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173 - it proxies `/api` to Django, so no CORS setup
is needed in development.

Windows shortcuts:

```powershell
.\scripts\dev.ps1
.\scripts\ui.ps1
.\scripts\test.ps1
```

## Layout

```
backend/            Django project (config) + apps kb, chat, llm
backend/rag/        Framework-free RAG engine (no Django imports)
backend/tests/      pytest suite
frontend/           React + Vite app (chat UI lands in Phase 7)
data/               SQLite, uploads, Chroma (gitignored)
scripts/            Windows dev helpers
```

## Security

This app has **no authentication** and is meant to be bound to `127.0.0.1`
only. Do not expose it to a network. Ollama cloud models are hidden by default
because they send data off the machine; set `SHOW_CLOUD_MODELS=true` to list
them anyway.

## Tests

```powershell
.\scripts\test.ps1
```

## Configuration

All deployment settings live in `.env` (see `.env.example`). User-tunable
values (top-k, temperature, context window, default models) will live in the
database and be editable from the UI.

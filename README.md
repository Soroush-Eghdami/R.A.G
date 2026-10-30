# Local RAG

Your documents, your models, your machine. A local-first retrieval-augmented
generation app with a Django API, React UI, Chroma vector store, and llama.cpp
for both chat and embeddings.

## What it does

- Index PDF, Word, Markdown, and plain-text files in separate knowledge bases.
- Answer questions with streamed responses and clickable source citations.
- Rewrite follow-up questions before retrieval.
- Choose the configured chat/embedding model aliases and tune RAG defaults.
- Keep documents, chats, embeddings, and inference on your machine.

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2 + Django REST Framework |
| RAG engine | Framework-free Python package |
| Chat + embeddings | llama.cpp OpenAI-compatible servers |
| Models | Qwen3.5 9B Q4_K_M; Nomic Embed Text v1.5 Q4_K_M |
| Vector store | Chroma, cosine similarity |
| Frontend | React + Vite + TanStack Query + Tailwind CSS |
| Metadata | SQLite |

## Requirements

- Python 3.13
- Node.js 22+
- A Vulkan-enabled `llama-server` build
- The GGUF files below, or equivalent files with the configured model aliases:

```text
C:\Users\sorou\.lmstudio\models\lmstudio-community\
  Qwen3.5-9B-GGUF\Qwen3.5-9B-Q4_K_M.gguf
  nomic-embed-text-v1.5-GGUF\nomic-embed-text-v1.5.Q4_K_M.gguf
```

The launch script uses the detected Vulkan device `Vulkan0` and attempts to
offload 99 layers. For this integrated GPU, model weights, context cache, and
other applications share system memory; lower `-GpuLayers` or `-ContextSize`
if memory pressure causes slowdowns or allocation errors.

## Start the model servers

Copy the environment template and set a Django secret. If your GGUF files live
somewhere else, pass the directory with `-ModelDirectory` when starting either
server:

```powershell
Copy-Item .env.example .env
```

In two PowerShell terminals from the repository root, start the chat and
embedding servers:

```powershell
.\scripts\start-llama.ps1 -Mode chat
.\scripts\start-llama.ps1 -Mode embedding
```

The chat server loads Qwen3.5 9B on `127.0.0.1:8082`. The embedding server loads
Nomic Embed Text v1.5 on `127.0.0.1:8083` with mean pooling and the model's
`search_document:` / `search_query:` prefixes. Keep both terminals running.
If `llama-server` is not on PATH, pass its executable path with `-Server`.

## Run the application

Backend:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements-dev.txt
python backend\manage.py migrate
python run.py --backend-only
```

Frontend, in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. For the one-command dev launcher, run `python run.py`
without `--backend-only` after installing frontend dependencies.

### Docker

Docker Compose runs the UI and backend, while the two llama.cpp servers stay on
the host. Start both model servers with `-HostAddress 0.0.0.0` so containers can
reach them through `host.docker.internal`, then run:

```powershell
docker compose up --build
```

Binding the model servers to `0.0.0.0` can expose them to your local network.
Only use that option on a trusted network and apply appropriate firewall rules.
The default script binding is loopback-only.

## First use

1. Create a knowledge base, selecting the configured Nomic embedding model.
2. Upload documents and wait for each status to become **Ready**.
3. Start a chat and ask questions; click citations to inspect their passages.
4. Tune context size, temperature, and retrieval count in **Settings**.

**Existing indexes:** embeddings made with an older Ollama model are not
compatible with Nomic Embed Text v1.5. Create a new knowledge base and re-upload
the original documents before querying with this configuration. Keep your
existing data directory until you have verified the new index.

## Configuration

Runtime settings come from `.env`:

| Variable | Default | Purpose |
|---|---|---|
| `LLAMA_CPP_CHAT_BASE_URL` | `http://127.0.0.1:8082` | Chat server |
| `LLAMA_CPP_EMBEDDING_BASE_URL` | `http://127.0.0.1:8083` | Embedding server |
| `LLAMA_CPP_CHAT_MODEL` | `Qwen3.5-9B` | Chat server alias (`--alias`) |
| `LLAMA_CPP_EMBEDDING_MODEL` | `nomic-embed-text-v1.5` | Embedding alias (`--alias`) |
| `LLAMA_CPP_CONNECT_TIMEOUT` | `5` | Connect timeout in seconds |
| `LLAMA_CPP_REQUEST_TIMEOUT` | `600` | Model request timeout in seconds |
| `LLAMA_CPP_CONTEXT_SIZE` | `8192` | Server context limit; the app prevents larger prompt budgets |
| `DEFAULT_TOP_K` | `4` | Retrieved passages |
| `DEFAULT_TEMPERATURE` | `0.2` | Generation temperature |
| `DEFAULT_NUM_CTX` | `8192` | Prompt budget; must not exceed `LLAMA_CPP_CONTEXT_SIZE` |
| `MAX_UPLOAD_SIZE_MB` | `50` | Upload limit |

`SECRET_KEY` is required; replace the example value before use.

## API and tests

API docs: http://127.0.0.1:8000/api/docs/ · schema:
http://127.0.0.1:8000/api/schema/.

```powershell
# Backend
cd backend
..\venv\Scripts\python.exe -m pytest -q

# Frontend
cd ..\frontend
npm run test
npm run build
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for runtime details and data
flow.

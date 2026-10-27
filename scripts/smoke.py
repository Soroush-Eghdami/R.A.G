"""Run the whole RAG flow from the terminal.

    python scripts/smoke.py sample.pdf --question "What is this about?"

Uses .env for OLLAMA_BASE_URL / DATA_DIR unless flags override them.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from rag.embedder import OllamaEmbedder  # noqa: E402
from rag.ollama_client import OllamaClient, OllamaError  # noqa: E402
from rag.pipeline import KnowledgeBaseConfig, answer_stream, ingest_document  # noqa: E402
from rag.vectorstore import VectorStore  # noqa: E402


def load_env() -> None:
    """Read .env without adding a dependency."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest a file and ask a question.")
    parser.add_argument("file", type=Path, help="Document to ingest")
    parser.add_argument("-q", "--question", required=True, help="Question to ask")
    parser.add_argument("--kb", default="smoke", help="Knowledge base id")
    parser.add_argument("--chat-model", default=os.environ.get("DEFAULT_CHAT_MODEL", "qwen3.5:9b"))
    parser.add_argument(
        "--embed-model",
        default=os.environ.get("DEFAULT_EMBED_MODEL", "nomic-embed-text:latest"),
    )
    parser.add_argument("--data-dir", default=None, help="Chroma directory")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--max-distance", type=float, default=0.65)
    parser.add_argument("--num-ctx", type=int, default=8192)
    parser.add_argument("--think", action="store_true", help="Let the model reason first")
    parser.add_argument("--keep", action="store_true", help="Keep vectors after the run")
    parser.add_argument("--no-ingest", action="store_true", help="Ask against existing vectors")
    return parser.parse_args()


def main() -> int:
    load_env()
    args = parse_args()

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    data_dir = Path(args.data_dir or os.environ.get("DATA_DIR", "data"))
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    chroma_dir = data_dir / "chroma"

    client = OllamaClient(base_url)
    embedder = OllamaEmbedder(client, args.embed_model)
    store = VectorStore(chroma_dir)
    kb = KnowledgeBaseConfig(
        id=args.kb,
        embedding_model=args.embed_model,
        top_k=args.top_k,
        max_distance=args.max_distance,
    )

    print(f"Ollama: {base_url}")
    print(f"Vectors: {chroma_dir}")

    try:
        if not args.no_ingest:
            started = time.perf_counter()
            result = ingest_document(args.file, kb, store=store, embedder=embedder)
            elapsed = time.perf_counter() - started
            pages = f", {result.pages} pages" if result.pages else ""
            print(
                f"Ingested {result.document_name}: {result.chunks} chunks"
                f"{pages} in {elapsed:.1f}s using {result.embedding_model}"
            )

        print(f"\nQ: {args.question}\n")
        thinking_shown = False
        for event in answer_stream(
            args.question,
            kb,
            chat_model=args.chat_model,
            client=client,
            store=store,
            embedder=embedder,
            num_ctx=args.num_ctx,
            think=args.think,
        ):
            if event.type == "sources":
                for number, chunk in enumerate(event.sources, start=1):
                    where = chunk.document_name
                    if chunk.page is not None:
                        where += f", p.{chunk.page}"
                    print(f"  [{number}] {where} (distance {chunk.distance:.3f})")
                print()
            elif event.type == "delta":
                if event.thinking and not thinking_shown:
                    print("(thinking...)")
                    thinking_shown = True
                sys.stdout.write(event.text if not event.thinking else "")
                sys.stdout.flush()
        print()
    except OllamaError as exc:
        print(f"\nOllama error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI should not dump a traceback
        print(f"\nFailed: {exc}", file=sys.stderr)
        return 1
    finally:
        if not args.keep and not args.no_ingest:
            store.drop(kb.id)
            print("\nVectors dropped (use --keep to keep them).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

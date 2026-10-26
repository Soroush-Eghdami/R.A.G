"""Development launcher for the backend (and the frontend once it exists).

Usage:
    python run.py                 # Django on 127.0.0.1:8000 + Vite if present
    python run.py --noreload      # also useful while testing ingestion
    python run.py --backend-only
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def _spawn(args: list[str], cwd: Path) -> subprocess.Popen:
    print(f"[dev] {' '.join(args)}  (cwd={cwd})")
    return subprocess.Popen(args, cwd=cwd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local RAG stack.")
    parser.add_argument("--port", default="127.0.0.1:8000", help="Django bind address")
    parser.add_argument("--noreload", action="store_true", help="Disable Django autoreload")
    parser.add_argument("--backend-only", action="store_true", help="Do not start Vite")
    args = parser.parse_args()

    backend_cmd = [sys.executable, str(BACKEND / "manage.py"), "runserver", args.port]
    if args.noreload:
        backend_cmd.append("--noreload")

    processes = [_spawn(backend_cmd, BACKEND)]

    if not args.backend_only and (FRONTEND / "package.json").exists():
        npm = shutil.which("npm")
        if npm:
            processes.append(_spawn([npm, "run", "dev"], FRONTEND))
        else:
            print("[dev] frontend/package.json found but npm is not on PATH; skipping Vite")

    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\n[dev] stopping...")
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

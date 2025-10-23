#!/usr/bin/env python3
"""
Simple API startup script for the RAG system.
This script starts the FastAPI server with proper path configuration.
"""

import sys
import os
import uvicorn

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    print("🚀 Starting RAG API Server...")
    print("📍 Project root:", project_root)
    print("🌐 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "app.api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

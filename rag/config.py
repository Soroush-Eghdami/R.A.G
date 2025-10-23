# rag/config.py

import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECTOR_DB_PATH = os.path.join(DATA_DIR, "chroma_db")

# Embedding & model configuration
EMBEDDING_MODEL = "all-minilm:latest"  # Available embedding model
OLLAMA_MODEL = "llama3:8b"  # Use llama3 8B model
OLLAMA_EMBEDDING_MODEL = "all-minilm:latest"  # Ollama embedding model

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Retrieval settings
TOP_K = 3

# Language support
SUPPORTED_LANGUAGES = ["en", "fa", "ar"]  # English, Persian, Arabic
DEFAULT_LANGUAGE = "en"
PERSIAN_SUPPORT = True

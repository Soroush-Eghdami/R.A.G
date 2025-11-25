# rag/config.py

import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECTOR_DB_PATH = os.path.join(DATA_DIR, "chroma_db")

# Embedding & model configuration
# Embedding model options:
# - "ollama:all-minilm:latest" - Use Ollama embedding model (fast, good for English)
# - "sentence-transformers:paraphrase-multilingual-MiniLM-L12-v2" - Multilingual model (recommended for Persian/Arabic)
# - "sentence-transformers:all-MiniLM-L6-v2" - Fast English model
EMBEDDING_MODEL = "sentence-transformers:paraphrase-multilingual-MiniLM-L12-v2"  # Recommended: Multilingual support
EMBEDDING_PROVIDER = "sentence-transformers"  # Options: "ollama" or "sentence-transformers"

# LLM model options:
# - "llama3:8b" - Current model (8 billion parameters)
# - "llama3.1:8b" - Better quality, same size (recommended upgrade)
# - "llama3.2:3b" - Faster, lighter (3 billion parameters)
# - "llama3.2:1b" - Very fast, lightest (1 billion parameters)
OLLAMA_MODEL = "llama3:8b"  # Current model (8 billion parameters)
OLLAMA_EMBEDDING_MODEL = "all-minilm:latest"  # Ollama embedding model (fallback)

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Retrieval settings
TOP_K = 3

# Language support
SUPPORTED_LANGUAGES = ["en", "fa", "ar"]  # English, Persian, Arabic
DEFAULT_LANGUAGE = "en"
PERSIAN_SUPPORT = True

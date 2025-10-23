# Smart RAG for Law Students - Documentation

## Overview

Smart RAG for Law Students is a Retrieval-Augmented Generation (RAG) system specifically designed for law students to ask questions and get comprehensive answers from their legal knowledge base. The system uses Ollama with Llama3 for language generation and Ollama's embedding models for document retrieval.

## Architecture

### Core Components

1. **Data Ingestion Pipeline** (`rag/ingestion.py`)
   - Loads documents from various sources (TXT, PDF, DOCX, APIs)
   - Chunks text into manageable pieces
   - Generates embeddings using Ollama
   - Stores in ChromaDB vector database

2. **Document Retrieval** (`rag/retriever.py`)
   - Searches for relevant documents using vector similarity
   - Supports topic-based and case-type searches
   - Returns ranked results with metadata

3. **Language Generation** (`rag/generator.py`)
   - Uses Ollama with Llama3 for response generation
   - Specialized prompts for law students
   - Generates summaries and answers

4. **Vector Storage** (`rag/vectorstore.py`)
   - Manages ChromaDB collections
   - Handles embedding storage and retrieval
   - Provides similarity search capabilities

### File Structure

```
smart_rag_student/
├── data/
│   ├── raw/                # Unprocessed documents
│   ├── processed/          # Cleaned text chunks
│   └── chroma_db/         # Vector database
├── rag/
│   ├── config.py          # Configuration settings
│   ├── embedding.py       # Ollama embedding model
│   ├── chunking.py        # Text splitting logic
│   ├── vectorstore.py     # ChromaDB management
│   ├── generator.py       # Ollama LLM integration
│   ├── retriever.py       # Document retrieval
│   ├── ingestion.py       # Data processing pipeline
│   ├── loaders/           # File type loaders
│   │   ├── txt_loader.py
│   │   ├── pdf_loader.py
│   │   ├── docx_loader.py
│   │   └── api_loader.py
│   └── utils/             # Helper functions
│       └── logging_utils.py
├── app/
│   ├── api.py             # FastAPI backend
│   └── interface.py       # Streamlit UI
├── main.py                # CLI interface
├── requirements.txt       # Dependencies
└── README.md             # Usage instructions
```

## Installation

### Prerequisites

1. **Python 3.13.3** (as specified)
2. **Ollama** installed and running
3. **Required Ollama models**:
   - `llama3` for text generation
   - `nomic-embed-text` for embeddings

### Setup Steps

1. **Clone and navigate to the project**:
   ```bash
   cd smart_rag_student
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and setup Ollama**:
   ```bash
   # Install Ollama (visit https://ollama.ai for installation)
   ollama pull llama3
   ollama pull nomic-embed-text
   ```

5. **Create necessary directories**:
   ```bash
   mkdir -p data/raw data/processed logs
   ```

## Usage

### 1. Command Line Interface

#### Interactive Mode
```bash
python main.py --interactive
```

#### Ask a Single Question
```bash
python main.py --question "What are the key elements of a valid contract?"
```

#### Ingest Documents
```bash
# Ingest from directory
python main.py --ingest-dir /path/to/your/documents

# Ingest single file
python main.py --ingest-file /path/to/document.pdf
```

### 2. Web Interface

#### Start the API Server
```bash
python -m app.api
```

#### Start the Web Interface
```bash
streamlit run app/interface.py
```

Then open your browser to `http://localhost:8501`

### 3. API Usage

The system provides a REST API with the following endpoints:

- `GET /` - API information
- `GET /health` - Health check
- `POST /query` - Ask questions
- `POST /ingest` - Ingest data
- `GET /search/{topic}` - Search by topic
- `GET /stats` - System statistics

#### Example API Usage
```python
import requests

# Ask a question
response = requests.post("http://localhost:8000/query", json={
    "question": "What is contract law?",
    "top_k": 3
})
print(response.json()["answer"])
```

## Configuration

### Model Configuration (`rag/config.py`)

```python
# Ollama models
OLLAMA_MODEL = "llama3"                    # Text generation model
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text" # Embedding model

# Chunking settings
CHUNK_SIZE = 500                           # Characters per chunk
CHUNK_OVERLAP = 50                         # Overlap between chunks

# Retrieval settings
TOP_K = 3                                  # Number of documents to retrieve
```

### Database Configuration

The system uses ChromaDB for vector storage. The database is automatically created at `data/chroma_db/`.

## Data Sources

### Supported File Types

1. **TXT Files** - Plain text documents
2. **PDF Files** - Legal documents, case studies
3. **DOCX Files** - Word documents
4. **API Endpoints** - External legal databases

### Data Ingestion Process

1. **Load** - Read documents from various sources
2. **Chunk** - Split text into overlapping chunks
3. **Embed** - Generate vector embeddings using Ollama
4. **Store** - Save embeddings in ChromaDB

## Advanced Features

### Topic-Based Search

```python
from rag.retriever import DocumentRetriever

retriever = DocumentRetriever()
documents = retriever.search_by_topic("contract law", top_k=5)
```

### Case Type Search

```python
documents = retriever.search_by_case_type("civil", top_k=3)
```

### Custom API Integration

```python
from rag.loaders.api_loader import load_from_multiple_apis

api_configs = [
    {
        "url": "https://api.law.example.com/cases",
        "headers": {"Authorization": "Bearer YOUR_API_KEY"},
        "params": {"limit": 100}
    }
]

texts = load_from_multiple_apis(api_configs)
```

## Troubleshooting

### Common Issues

1. **Ollama not running**:
   ```bash
   ollama serve
   ```

2. **Models not found**:
   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```

3. **ChromaDB errors**:
   - Delete `data/chroma_db/` directory
   - Restart the application

4. **Memory issues with large documents**:
   - Reduce `CHUNK_SIZE` in config
   - Process documents in smaller batches

### Performance Optimization

1. **Batch processing** for large document sets
2. **Adjust chunk size** based on document type
3. **Use GPU acceleration** for Ollama (if available)
4. **Monitor memory usage** during ingestion

## Legal Considerations

### Data Privacy
- Ensure compliance with data protection regulations
- Handle sensitive legal documents appropriately
- Implement proper access controls

### Academic Use
- Verify accuracy of generated responses
- Use as study aid, not replacement for legal research
- Cite original sources when using generated content

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is designed for educational purposes. Please ensure compliance with all applicable laws and regulations when using for legal research or academic purposes.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `logs/` directory
3. Ensure all dependencies are properly installed
4. Verify Ollama is running and models are available


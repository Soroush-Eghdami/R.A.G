# ⚖️ Smart RAG for Law Students

A specialized Retrieval-Augmented Generation (RAG) system designed for law students to ask questions and get comprehensive answers from their legal knowledge base. Built with Python 3.13.3, Ollama (Llama3), and ChromaDB.

[![Python 3.13.3](https://img.shields.io/badge/python-3.13.3-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/ollama-llama3-green.svg)](https://ollama.ai/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Quick Start

### Prerequisites
- **Python 3.13.3** or higher
- **Ollama** installed and running
- **Required Ollama models**: `llama3:8b` and `all-minilm:latest`

### Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:Soroush-Eghdami/R.A.G.git
   cd R.A.G
   ```

2. **Setup virtual environment**:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama models**:
   ```bash
   ollama pull llama3:8b
   ollama pull all-minilm:latest
   ```

5. **Create necessary directories**:
   ```bash
   mkdir -p data/raw data/processed logs
   ```

## ✅ **System Status: FULLY WORKING!**

Your RAG system is now fully functional with both CLI and Web UI modes! The system has been tested and verified to work correctly.

## 📖 Usage

### 🎯 Quick Start

1. **Add your legal documents** to `data/raw/` directory
2. **Ingest the documents** (see [COMMANDS.md](COMMANDS.md) for details)
3. **Start asking questions** via CLI or Web UI

### 💻 Command Line Interface

For detailed command reference, see **[COMMANDS.md](COMMANDS.md)**.

**Quick Examples:**
```bash
# Interactive mode (recommended)
python main.py --interactive

# Ask a single question
python main.py --question "What are the key elements of a valid contract?"

# Ingest documents
python main.py --ingest-file "data/raw/document.docx"
python main.py --ingest-dir "data/raw"
```

### 🌐 Web Interface

**Modern HTML/CSS/JS Interface (Recommended):**

1. **Start the API server**:
   ```bash
   python api.py
   ```

2. **Start the web UI** (in another terminal):
   ```bash
   cd web_ui
   python server.py
   ```

3. **Open your browser** to `http://localhost:8080`

**Features:**
- Dark/light mode toggle
- Real-time chat interface
- Document upload support
- System settings
- Connection status indicator

### 📚 Example Questions

- "What are the elements of negligence in tort law?"
- "Explain the difference between civil and criminal law"
- "What is the statute of limitations for contract disputes?"
- "How does the burden of proof work in criminal cases?"

## ✨ Features

### 🎓 Law Student Focused
- **Specialized prompts** for legal questions and case analysis
- **Legal terminology** understanding and explanation
- **Case law summaries** and legal concept explanations
- **Academic-friendly** responses with proper citations

### 📚 Document Support
- **TXT files** - Plain text legal documents
- **PDF files** - Case studies, legal papers, textbooks
- **DOCX files** - Word documents and legal briefs
- **API endpoints** - External legal databases

### 🔍 Smart Retrieval
- **Vector similarity search** for relevant documents
- **Topic-based queries** (e.g., "contract law", "tort law")
- **Case type filtering** (civil, criminal, constitutional)
- **Relevance ranking** with confidence scores

### 💻 Multiple Interfaces
- **Command Line** - Fast and efficient for power users
- **Web Interface** - User-friendly Streamlit UI
- **REST API** - For integration with other tools
- **Interactive Mode** - Conversational Q&A experience

## 📁 Project Structure

```
R.A.G/
├── data/
│   ├── raw/                # Your legal documents (.txt, .pdf, .docx)
│   ├── processed/          # Processed text chunks
│   └── chroma_db/          # Vector database (auto-created)
├── rag/                    # Core RAG components
│   ├── config.py          # Configuration settings
│   ├── embedding.py       # Ollama embeddings
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
│   └── utils/             # Helper utilities
│       ├── language_utils.py    # Multilingual support
│       └── logging_utils.py
├── app/                    # Web interface
│   ├── api.py             # FastAPI backend
│   └── interface.py       # Streamlit UI
├── web_ui/                 # Modern HTML/CSS/JS interface
│   ├── index.html         # Main web interface (Tailwind CSS)
│   ├── script.js          # JavaScript functionality (Alpine.js)
│   └── server.py          # Local web server
├── logs/                   # System logs
│   └── rag_main.log       # Main application logs
├── main.py                # CLI interface
├── api.py                 # FastAPI server
├── start_api.py           # API startup script
├── requirements.txt       # Python dependencies
├── test_contract_law.txt  # Sample legal document
├── DOCUMENTATION.md       # Technical documentation
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## ⚙️ Configuration

Edit `rag/config.py` to customize:

```python
# Model settings
OLLAMA_MODEL = "llama3:8b"                    # Text generation
OLLAMA_EMBEDDING_MODEL = "all-minilm:latest"  # Embeddings

# Chunking settings
CHUNK_SIZE = 500                              # Characters per chunk
CHUNK_OVERLAP = 50                            # Overlap between chunks

# Retrieval settings
TOP_K = 3                                     # Documents to retrieve
```

## 🔍 API Usage

The system provides a REST API for integration:

```python
import requests

# Ask a question
response = requests.post("http://localhost:8000/query", json={
    "question": "What is contract law?",
    "top_k": 3
})
print(response.json()["answer"])

# Ingest documents
response = requests.post("http://localhost:8000/ingest", json={
    "source_type": "directory",
    "source_path": "/path/to/documents"
})
```

## 🛠️ Troubleshooting

### Common Issues

1. **"Ollama not running"**:
   ```bash
   ollama serve
   ```

2. **"Model not found"**:
   ```bash
   ollama pull llama3:8b
   ollama pull all-minilm:latest
   ```

3. **"No documents found"**:
   - Check if documents are in `data/raw/`
   - Run ingestion: `python main.py --ingest-dir data/raw`

4. **Memory issues**:
   - Reduce `CHUNK_SIZE` in config
   - Process documents in smaller batches

### Performance Tips

- Use GPU acceleration for Ollama if available
- Adjust chunk size based on document type
- Monitor memory usage during large ingestions
- Use batch processing for multiple documents

## 📋 Requirements

- **Python 3.13.3** or higher
- **Ollama** with `llama3:8b` and `all-minilm:latest` models
- **ChromaDB** for vector storage
- **FastAPI** for web API
- **Streamlit** for web interface

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is designed for educational purposes. Please ensure compliance with all applicable laws and regulations when using for legal research.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs in the `logs/` directory
3. Ensure all dependencies are properly installed
4. Verify Ollama is running with required models

## 📖 Documentation

- **[COMMANDS.md](COMMANDS.md)** - Complete command reference guide
- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Technical documentation and architecture details

---

**Happy studying! 📚⚖️**


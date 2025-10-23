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

## 📖 Usage

### 🎯 Getting Started

1. **Add your legal documents** to `data/raw/`:
   ```bash
   # Copy your legal documents
   cp your_legal_documents/* data/raw/
   ```

2. **Ingest the documents**:
   ```bash
   python main.py --ingest-dir data/raw
   ```

3. **Start asking questions**:
   ```bash
   python main.py --interactive
   ```

### 💻 Command Line Interface

#### Interactive Mode (Recommended)
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
python main.py --ingest-dir /path/to/your/legal/documents

# Ingest single file
python main.py --ingest-file /path/to/case_study.pdf
```

### 🌐 Web Interface

1. **Start the API server**:
   ```bash
   python -m app.api
   ```

2. **Start the web interface** (in another terminal):
   ```bash
   streamlit run app/interface.py
   ```

3. **Open your browser** to `http://localhost:8501`

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
│       └── logging_utils.py
├── app/                    # Web interface
│   ├── api.py             # FastAPI backend
│   └── interface.py       # Streamlit UI
├── main.py                # CLI interface
├── requirements.txt       # Python dependencies
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

For detailed documentation, see [DOCUMENTATION.md](DOCUMENTATION.md).

---

**Happy studying! 📚⚖️**


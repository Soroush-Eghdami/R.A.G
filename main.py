# main.py

import argparse
import sys
import os
from typing import List, Dict, Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.ingestion import DataIngestion
from rag.retriever import DocumentRetriever
from rag.generator import LLMGenerator
from rag.utils.logging_utils import setup_logging, RAGLogger

def setup_environment():
    """Setup the environment and check dependencies."""
    print("Setting up Smart RAG for Law Students...")
    
    # Check if Ollama is running
    try:
        import ollama
        client = ollama.Client()
        models = client.list()
        print("Ollama is running")
        
        # Check for required models
        available_models = []
        for model in models.get('models', []):
            if isinstance(model, dict) and 'name' in model:
                available_models.append(model['name'])
            elif isinstance(model, str):
                available_models.append(model)
        
        if 'llama3' not in available_models:
            print("Warning: llama3 model not found. Please pull it with: ollama pull llama3")
        
        if 'nomic-embed-text' not in available_models:
            print("Warning: nomic-embed-text model not found. Please pull it with: ollama pull nomic-embed-text")
            
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        print("Please make sure Ollama is installed and running.")
        return False
    
    return True

def ingest_data(args):
    """Handle data ingestion."""
    logger = RAGLogger("main")
    ingestion = DataIngestion()
    
    if args.directory:
        print(f"Ingesting from directory: {args.directory}")
        result = ingestion.ingest_from_directory(args.directory)
        print(f"Ingested {result['total_chunks']} chunks from {result['successful_files']} files")
        
    elif args.file:
        print(f"Ingesting single file: {args.file}")
        result = ingestion.ingest_single_file(args.file)
        if result['status'] == 'success':
            print(f"Ingested {result['total_chunks']} chunks from {args.file}")
        else:
            print(f"Error: {result['error']}")
    
    elif args.api:
        print("Ingesting from API...")
        # This would need API configuration
        print("API ingestion requires configuration. Please use the web interface.")

def ask_question(question: str, top_k: int = 3):
    """Ask a question to the RAG system."""
    logger = RAGLogger("main")
    
    try:
        # Initialize components
        retriever = DocumentRetriever()
        generator = LLMGenerator()
        
        print(f"Question: {question}")
        print("Retrieving relevant documents...")
        
        # Retrieve relevant documents
        documents = retriever.retrieve_relevant_documents(question, top_k)
        
        if not documents:
            print("No relevant documents found. Please add more documents to the knowledge base.")
            return
        
        print(f"Found {len(documents)} relevant documents")
        print("Generating answer...")
        
        # Generate response
        answer = generator.generate_response(question, documents)
        
        print("\n" + "="*50)
        print("🎯 ANSWER:")
        print("="*50)
        print(answer)
        print("\n" + "="*50)
        print("📖 SOURCES:")
        print("="*50)
        for i, doc in enumerate(documents, 1):
            print(f"\nSource {i}:")
            print(doc[:200] + "..." if len(doc) > 200 else doc)
        
    except Exception as e:
        logger.log_error("question_answering", str(e))
        print(f"Error: {e}")

def interactive_mode():
    """Run in interactive question-answering mode."""
    print("\n🎓 Smart RAG for Law Students - Interactive Mode")
    print("Type 'quit' or 'exit' to stop, 'help' for commands")
    print("-" * 50)
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif question.lower() == 'help':
                print("\n📋 Available commands:")
                print("  - Ask any legal question")
                print("  - 'stats' - Show system statistics")
                print("  - 'quit' or 'exit' - Exit the program")
                continue
            elif question.lower() == 'stats':
                retriever = DocumentRetriever()
                stats = retriever.get_collection_stats()
                print(f"\n📊 System Statistics:")
                print(f"  - Total documents: {stats.get('total_documents', 0)}")
                print(f"  - Collection: {stats.get('collection_name', 'N/A')}")
                print(f"  - Status: {stats.get('status', 'unknown')}")
                continue
            elif not question:
                continue
            
            ask_question(question)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Smart RAG for Law Students")
    parser.add_argument("--question", "-q", help="Ask a specific question")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--ingest-dir", help="Ingest documents from directory")
    parser.add_argument("--ingest-file", help="Ingest a single file")
    parser.add_argument("--api", action="store_true", help="Ingest from API")
    parser.add_argument("--top-k", type=int, default=3, help="Number of documents to retrieve")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level, log_file="logs/rag_main.log")
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Handle different modes
    if args.ingest_dir or args.ingest_file or args.api:
        ingest_data(args)
    elif args.question:
        ask_question(args.question, args.top_k)
    elif args.interactive:
        interactive_mode()
    else:
        # Default to interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()


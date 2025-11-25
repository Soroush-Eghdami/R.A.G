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
        
        # Check for recommended LLM models
        recommended_models = ['llama3.1:8b', 'llama3:8b', 'llama3.2:3b']
        found_llm = False
        for model in recommended_models:
            if any(model in m for m in available_models):
                print(f"Found LLM model: {model}")
                found_llm = True
                break
        
        if not found_llm:
            print("Warning: Recommended LLM model not found.")
            print("Please pull one of these models:")
            print("  ollama pull llama3.1:8b  # Recommended: Better quality")
            print("  ollama pull llama3:8b    # Current model")
            print("  ollama pull llama3.2:3b  # Faster, lighter")
        
        # Check for embedding models (Ollama fallback)
        if 'all-minilm:latest' not in available_models:
            print("Note: Ollama embedding model not found, but using sentence-transformers instead.")
            print("If you want to use Ollama embeddings, pull with: ollama pull all-minilm:latest")
        
        return True  # Successfully connected to Ollama
            
    except Exception as e:
        print(f"Warning: Could not connect to Ollama: {e}")
        print("Note: Ollama is needed for querying, but ingestion can proceed with sentence-transformers.")
        print("Please make sure Ollama is installed and running before querying.")
        # Don't fail completely - ingestion can work without Ollama
        return True  # Changed to True to allow ingestion without Ollama

def ingest_data(args):
    """Handle data ingestion."""
    logger = RAGLogger("main")
    ingestion = DataIngestion()
    
    if args.ingest_dir:
        print(f"Ingesting from directory: {args.ingest_dir}")
        result = ingestion.ingest_from_directory(args.ingest_dir)
        print(f"Ingested {result['total_chunks']} chunks from {result['successful_files']} files")
        
    elif args.ingest_file:
        print(f"Ingesting single file: {args.ingest_file}")
        result = ingestion.ingest_single_file(args.ingest_file)
        if result['status'] == 'success':
            print(f"Ingested {result['total_chunks']} chunks from {args.ingest_file}")
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
        print("ANSWER:")
        print("="*50)
        print(answer)
        print("\n" + "="*50)
        print("SOURCES:")
        print("="*50)
        for i, doc in enumerate(documents, 1):
            print(f"\nSource {i}:")
            print(doc[:200] + "..." if len(doc) > 200 else doc)
        
    except Exception as e:
        logger.log_error("question_answering", str(e))
        print(f"Error: {e}")

def interactive_mode():
    """Run in interactive question-answering mode."""
    print("\nSmart RAG for Law Students - Interactive Mode")
    print("Type 'quit' or 'exit' to stop, 'help' for commands")
    print("-" * 50)
    
    while True:
        try:
            question = input("\nYour question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif question.lower() == 'help':
                print("\nAvailable commands:")
                print("  - Ask any legal question")
                print("  - 'stats' - Show system statistics")
                print("  - 'quit' or 'exit' - Exit the program")
                continue
            elif question.lower() == 'stats':
                retriever = DocumentRetriever()
                stats = retriever.get_collection_stats()
                print(f"\nSystem Statistics:")
                print(f"  - Total documents: {stats.get('total_documents', 0)}")
                print(f"  - Collection: {stats.get('collection_name', 'N/A')}")
                print(f"  - Status: {stats.get('status', 'unknown')}")
                continue
            elif not question:
                continue
            
            ask_question(question)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
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
    try:
        if args.ingest_dir or args.ingest_file or args.api:
            ingest_data(args)
        elif args.question:
            ask_question(args.question, args.top_k)
        elif args.interactive:
            interactive_mode()
        else:
            # Default to interactive mode
            interactive_mode()
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


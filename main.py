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
from rag.config import OLLAMA_MODEL

def get_available_models():
    """Get list of available Ollama models."""
    try:
        import ollama
        client = ollama.Client()
        models_response = client.list()
        
        available_models = []
        # Handle both dict format and Model object format
        models_list = models_response.get('models', [])
        if not models_list and hasattr(models_response, 'models'):
            models_list = models_response.models
        
        for model in models_list:
            # Handle Model object (has .model attribute)
            if hasattr(model, 'model'):
                model_name = model.model
            # Handle dict format
            elif isinstance(model, dict):
                model_name = model.get('name', model.get('model', ''))
            # Handle string format
            else:
                model_name = str(model)
            
            if model_name:
                available_models.append(model_name)
        
        # Remove duplicates and sort
        return sorted(list(set(available_models)))
    except Exception as e:
        print(f"Error getting models: {e}")
        return []

def get_available_embedding_models():
    """Get list of available embedding models (Ollama + sentence-transformers options)."""
    embedding_options = []
    
    # Get Ollama embedding models
    try:
        import ollama
        client = ollama.Client()
        models_response = client.list()
        models_list = models_response.get('models', [])
        if not models_list and hasattr(models_response, 'models'):
            models_list = models_response.models
        
        for model in models_list:
            if hasattr(model, 'model'):
                model_name = model.model
            elif isinstance(model, dict):
                model_name = model.get('name', model.get('model', ''))
            else:
                model_name = str(model)
            
            # Check if it's an embedding model
            if model_name and any(x in model_name.lower() for x in ['embed', 'minilm', 'nomic']):
                embedding_options.append({
                    'name': model_name,
                    'provider': 'ollama',
                    'display': f"Ollama: {model_name}"
                })
    except Exception as e:
        pass
    
    # Add sentence-transformers options
    sentence_transformer_models = [
        {
            'name': 'paraphrase-multilingual-MiniLM-L12-v2',
            'provider': 'sentence-transformers',
            'display': 'Sentence-Transformers: paraphrase-multilingual-MiniLM-L12-v2 (Multilingual - Recommended)'
        },
        {
            'name': 'all-MiniLM-L6-v2',
            'provider': 'sentence-transformers',
            'display': 'Sentence-Transformers: all-MiniLM-L6-v2 (Fast English)'
        },
        {
            'name': 'all-mpnet-base-v2',
            'provider': 'sentence-transformers',
            'display': 'Sentence-Transformers: all-mpnet-base-v2 (High Quality English)'
        }
    ]
    
    embedding_options.extend(sentence_transformer_models)
    
    return embedding_options

def select_embedding_model_interactive():
    """Interactive embedding model selection."""
    print("\n" + "="*60)
    print(" " * 12 + "EMBEDDING MODEL SELECTION")
    print("="*60)
    
    embedding_options = get_available_embedding_models()
    
    if not embedding_options:
        print("\n⚠️  Warning: No embedding models found.")
        print("Using default embedding model from config.")
        return None, None
    
    print(f"\n📋 Available Embedding Models:\n")
    for i, option in enumerate(embedding_options, 1):
        marker = "⭐" if "multilingual" in option['display'].lower() else "  "
        print(f"  {marker} {i}. {option['display']}")
    
    print(f"\n{'─'*60}")
    print(f"  Recommended: Multilingual model for Persian/Arabic support")
    print(f"{'─'*60}\n")
    
    while True:
        try:
            choice = input("Select an embedding model (number) or press Enter for default: ").strip()
            
            if not choice:
                return None, None  # Use default
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(embedding_options):
                selected = embedding_options[choice_num - 1]
                print(f"\n✅ Selected embedding model: {selected['display']}\n")
                return selected['name'], selected['provider']
            else:
                print(f"❌ Please enter a number between 1 and {len(embedding_options)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nUsing default embedding model.")
            return None, None

def select_model_interactive():
    """Interactive model selection with beautiful CLI interface."""
    print("\n" + "="*60)
    print(" " * 15 + "MODEL SELECTION")
    print("="*60)
    
    available_models = get_available_models()
    
    if not available_models:
        print("\n⚠️  Warning: Could not connect to Ollama or no models found.")
        print("Using default model from config:", OLLAMA_MODEL)
        return OLLAMA_MODEL
    
    # Filter for LLM models (not embedding models)
    llm_models = [m for m in available_models if any(x in m.lower() for x in ['llama', 'mistral', 'phi', 'gemma', 'qwen'])]
    
    if not llm_models:
        print("\n⚠️  No LLM models found. Available models:")
        for i, model in enumerate(available_models, 1):
            print(f"  {i}. {model}")
        print(f"\nUsing default model: {OLLAMA_MODEL}")
        return OLLAMA_MODEL
    
    print(f"\n📋 Available LLM Models:\n")
    for i, model in enumerate(llm_models, 1):
        marker = "⭐" if model == OLLAMA_MODEL else "  "
        print(f"  {marker} {i}. {model}")
    
    print(f"\n{'─'*60}")
    print(f"  Current default: {OLLAMA_MODEL}")
    print(f"{'─'*60}\n")
    
    while True:
        try:
            choice = input("Select a model (number) or press Enter for default: ").strip()
            
            if not choice:
                selected = OLLAMA_MODEL
                break
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(llm_models):
                selected = llm_models[choice_num - 1]
                break
            else:
                print(f"❌ Please enter a number between 1 and {len(llm_models)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nUsing default model:", OLLAMA_MODEL)
            return OLLAMA_MODEL
    
    print(f"\n✅ Selected model: {selected}\n")
    return selected

def setup_environment():
    """Setup the environment and check dependencies."""
    print("Setting up Smart RAG for Law Students...")
    
    # Check if Ollama is running
    try:
        import ollama
        client = ollama.Client()
        models_response = client.list()
        print("✓ Ollama is running")
        
        # Get available models using the same logic as get_available_models
        available_models = []
        models_list = models_response.get('models', [])
        if not models_list and hasattr(models_response, 'models'):
            models_list = models_response.models
        
        for model in models_list:
            # Handle Model object (has .model attribute)
            if hasattr(model, 'model'):
                model_name = model.model
            # Handle dict format
            elif isinstance(model, dict):
                model_name = model.get('name', model.get('model', ''))
            # Handle string format
            else:
                model_name = str(model)
            
            if model_name:
                available_models.append(model_name)
        
        # Print all available models for debugging
        if available_models:
            print(f"✓ Found {len(available_models)} model(s): {', '.join(available_models)}")
        
        # Check for recommended LLM models
        recommended_models = ['llama3.1:8b', 'llama3:8b', 'llama3.2:3b']
        found_llm = False
        found_models = []
        for model in recommended_models:
            # Check for exact match or if model name contains the recommended model
            for available in available_models:
                if model == available or model in available:
                    found_models.append(model)
                    found_llm = True
                    break
        
        if found_llm:
            print(f"✓ Found LLM model(s): {', '.join(found_models)}")
        else:
            print("⚠️  Warning: Recommended LLM model not found.")
            print("Available models:", ', '.join(available_models) if available_models else "None")
            print("Please pull one of these models:")
            print("  ollama pull llama3.1:8b  # Recommended: Better quality")
            print("  ollama pull llama3:8b    # Current model")
            print("  ollama pull llama3.2:3b  # Faster, lighter")
        
        # Check for embedding models (Ollama fallback)
        has_embedding = any('all-minilm' in m or 'nomic-embed' in m for m in available_models)
        if has_embedding:
            embedding_models = [m for m in available_models if 'all-minilm' in m or 'nomic-embed' in m]
            print(f"✓ Found embedding model(s): {', '.join(embedding_models)}")
        else:
            print("ℹ️  Note: Ollama embedding model not found, but using sentence-transformers instead.")
            print("If you want to use Ollama embeddings, pull with: ollama pull all-minilm:latest")
        
        return True  # Successfully connected to Ollama
            
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to Ollama: {e}")
        print("Note: Ollama is needed for querying, but ingestion can proceed with sentence-transformers.")
        print("Please make sure Ollama is installed and running before querying.")
        # Don't fail completely - ingestion can work without Ollama
        return True  # Changed to True to allow ingestion without Ollama

def ingest_data(args, embedding_model=None, embedding_provider=None):
    """Handle data ingestion."""
    logger = RAGLogger("main")
    
    print("\n" + "="*60)
    print(" " * 15 + "DATA INGESTION")
    print("="*60 + "\n")
    
    # Create ingestion with selected embedding model
    ingestion = DataIngestion(
        embedding_model=embedding_model,
        embedding_provider=embedding_provider
    )
    
    if embedding_model:
        print(f"📊 Using embedding model: {embedding_model} ({embedding_provider or 'default provider'})\n")
    
    if args.ingest_dir:
        print(f"📁 Ingesting from directory: {args.ingest_dir}\n")
        result = ingestion.ingest_from_directory(args.ingest_dir)
        print(f"\n{'='*60}")
        print(f"✓ Ingestion completed!")
        print(f"  - Total chunks: {result['total_chunks']}")
        print(f"  - Files processed: {result['successful_files']}")
        print(f"  - File types: {', '.join(result.get('file_types_processed', []))}")
        print(f"{'='*60}\n")
        
    elif args.ingest_file:
        print(f"📄 Ingesting single file: {args.ingest_file}\n")
        result = ingestion.ingest_single_file(args.ingest_file)
        if result['status'] == 'success':
            print(f"\n{'='*60}")
            print(f"✓ Successfully ingested {result['total_chunks']} chunks from {os.path.basename(args.ingest_file)}")
            print(f"{'='*60}\n")
        else:
            print(f"\n✗ Error: {result.get('error', 'Unknown error')}\n")
    
    elif args.api:
        print("🌐 Ingesting from API...")
        # This would need API configuration
        print("API ingestion requires configuration. Please use the web interface.")

def ask_question(question: str, top_k: int = 3, model_name: str = None):
    """Ask a question to the RAG system."""
    logger = RAGLogger("main")
    
    try:
        # Initialize components
        retriever = DocumentRetriever()
        generator = LLMGenerator(model_name=model_name) if model_name else LLMGenerator()
        
        print(f"Question: {question}")
        print(f"Using model: {generator.model_name}")
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

def interactive_mode(model_name: str = None):
    """Run in interactive question-answering mode."""
    print("\n" + "="*60)
    print(" " * 10 + "Smart RAG for Law Students")
    print(" " * 15 + "Interactive Mode")
    print("="*60)
    print("Type 'quit' or 'exit' to stop, 'help' for commands")
    print("-" * 60)
    
    # Initialize generator once
    generator = LLMGenerator(model_name=model_name) if model_name else LLMGenerator()
    retriever = DocumentRetriever()
    
    print(f"\nUsing model: {generator.model_name}\n")
    
    while True:
        try:
            question = input("Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            elif question.lower() == 'help':
                print("\n📖 Available commands:")
                print("  - Ask any legal question")
                print("  - 'stats' - Show system statistics")
                print("  - 'model' - Change model")
                print("  - 'clear' - Clear database")
                print("  - 'quit' or 'exit' - Exit the program")
                continue
            elif question.lower() == 'stats':
                stats = retriever.get_collection_stats()
                print(f"\n📊 System Statistics:")
                print(f"  - Total documents: {stats.get('total_documents', 0)}")
                print(f"  - Collection: {stats.get('collection_name', 'N/A')}")
                print(f"  - Status: {stats.get('status', 'unknown')}")
                print(f"  - Current model: {generator.model_name}\n")
                continue
            elif question.lower() == 'model':
                new_model = select_model_interactive()
                generator = LLMGenerator(model_name=new_model)
                print(f"✓ Model changed to: {new_model}\n")
                continue
            elif question.lower() == 'clear':
                confirm = input("⚠️  Are you sure you want to clear the database? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    from rag.vectorstore import VectorStore
                    vectorstore = VectorStore()
                    if vectorstore.delete_collection():
                        print("✓ Database cleared successfully!\n")
                    else:
                        print("❌ Failed to clear database\n")
                else:
                    print("Cancelled.\n")
                continue
            elif not question:
                continue
            
            print(f"\n🔍 Question: {question}")
            print(f"🤖 Model: {generator.model_name}")
            print("📚 Retrieving relevant documents...")
            
            # Retrieve relevant documents
            documents = retriever.retrieve_relevant_documents(question, 3)
            
            if not documents:
                print("❌ No relevant documents found. Please add more documents to the knowledge base.\n")
                continue
            
            print(f"✓ Found {len(documents)} relevant documents")
            print("💭 Generating answer...\n")
            
            # Generate response
            answer = generator.generate_response(question, documents)
            
            print("="*60)
            print("ANSWER:")
            print("="*60)
            print(answer)
            print("\n" + "="*60)
            print("SOURCES:")
            print("="*60)
            for i, doc in enumerate(documents, 1):
                print(f"\n📄 Source {i}:")
                print(doc[:200] + "..." if len(doc) > 200 else doc)
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

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
    parser.add_argument("--model", "-m", help="Specify LLM model to use (e.g., llama3.1:8b)")
    parser.add_argument("--select-model", action="store_true", help="Interactively select LLM model at startup")
    parser.add_argument("--select-embedding", action="store_true", help="Interactively select embedding model for ingestion")
    parser.add_argument("--embedding-model", help="Specify embedding model to use (e.g., all-minilm:latest or paraphrase-multilingual-MiniLM-L12-v2)")
    parser.add_argument("--embedding-provider", help="Specify embedding provider (ollama or sentence-transformers)")
    parser.add_argument("--clear-db", action="store_true", help="Clear the database before starting")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level, log_file="logs/rag_main.log")
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Model selection for LLM (only for query modes)
    selected_model = None
    if args.model:
        selected_model = args.model
    elif args.select_model or (not args.ingest_dir and not args.ingest_file and not args.api):
        # Show model selection for query modes
        selected_model = select_model_interactive()
    
    # Embedding model selection (for ingestion modes)
    selected_embedding_model = None
    selected_embedding_provider = None
    if args.ingest_dir or args.ingest_file or args.api:
        # Check if embedding model specified via command line
        if args.embedding_model:
            selected_embedding_model = args.embedding_model
            selected_embedding_provider = args.embedding_provider
        # Show embedding model selection for ingestion
        elif args.select_model or args.select_embedding:
            selected_embedding_model, selected_embedding_provider = select_embedding_model_interactive()
        else:
            # Ask if user wants to select embedding model
            print("\n" + "─"*60)
            choice = input("Do you want to select an embedding model? (y/n, default=n): ").strip().lower()
            if choice in ['y', 'yes']:
                selected_embedding_model, selected_embedding_provider = select_embedding_model_interactive()
    
    # Clear database if requested
    if args.clear_db:
        confirm = input("⚠️  Are you sure you want to clear the database? (yes/no): ").strip().lower()
        if confirm == 'yes':
            from rag.vectorstore import VectorStore
            vectorstore = VectorStore()
            if vectorstore.delete_collection():
                print("✓ Database cleared successfully!\n")
            else:
                print("❌ Failed to clear database\n")
                sys.exit(1)
        else:
            print("Cancelled.\n")
            sys.exit(0)
    
    # Handle different modes
    try:
        if args.ingest_dir or args.ingest_file or args.api:
            ingest_data(args, selected_embedding_model, selected_embedding_provider)
        elif args.question:
            ask_question(args.question, args.top_k, selected_model)
        elif args.interactive:
            interactive_mode(selected_model)
        else:
            # Default to interactive mode
            interactive_mode(selected_model)
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
RAG API Server - FastAPI backend for Smart RAG for Law Students
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.retriever import DocumentRetriever
from rag.generator import LLMGenerator
from rag.ingestion import DataIngestion
from rag.utils.logging_utils import setup_logging, RAGLogger

# Initialize FastAPI app
app = FastAPI(
    title="Smart RAG for Law Students",
    description="A RAG system specialized for law students",
    version="1.0.0"
)

# Add CORS middleware to allow web UI to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],    # Allow all headers
)

# Initialize components (will be reinitialized when model changes)
retriever = DocumentRetriever()
generator = LLMGenerator()
ingestion = DataIngestion()
logger = RAGLogger("api")

# Current model (can be changed via API)
current_model = None

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3
    include_sources: Optional[bool] = True

class QueryResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None

class IngestionRequest(BaseModel):
    source_type: str  # "directory", "file"
    source_path: str

class IngestionResponse(BaseModel):
    status: str
    total_chunks: int
    details: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    message: str
    model_available: Optional[bool] = None
    collection_stats: Optional[Dict[str, Any]] = None
    current_model: Optional[str] = None

class ModelListResponse(BaseModel):
    available_models: List[str]
    current_model: Optional[str] = None

class ModelChangeRequest(BaseModel):
    model_name: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        model_available = generator.check_model_availability()
        collection_stats = retriever.get_collection_stats()
        
        return HealthResponse(
            status="healthy" if model_available else "degraded",
            message="RAG API is running",
            model_available=model_available,
            collection_stats=collection_stats,
            current_model=generator.model_name
        )
    except Exception as e:
        return HealthResponse(
            status="error",
            message=f"Health check failed: {str(e)}"
        )

# Get available models
@app.get("/models", response_model=ModelListResponse)
async def get_models():
    """Get list of available Ollama models."""
    try:
        import ollama
        client = ollama.Client()
        models_response = client.list()
        
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
        
        # Remove duplicates and sort
        available_models = sorted(list(set(available_models)))
        
        return ModelListResponse(
            available_models=available_models,
            current_model=generator.model_name
        )
    except Exception as e:
        logger.log_error("get_models", str(e))
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

# Change model
@app.post("/models/change")
async def change_model(request: ModelChangeRequest):
    """Change the LLM model."""
    try:
        global generator
        # Create new generator with the selected model
        generator = LLMGenerator(model_name=request.model_name)
        
        # Verify model is available
        if not generator.check_model_availability():
            raise HTTPException(
                status_code=400, 
                detail=f"Model '{request.model_name}' is not available. Please pull it with: ollama pull {request.model_name}"
            )
        
        logger.log_info(f"Model changed to: {request.model_name}")
        return {
            "status": "success",
            "message": f"Model changed to {request.model_name}",
            "model": request.model_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("change_model", str(e))
        raise HTTPException(status_code=500, detail=f"Error changing model: {str(e)}")

# Query endpoint
@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Query the RAG system with a question.
    """
    try:
        # Retrieve relevant documents
        documents = retriever.retrieve_relevant_documents(
            request.question, 
            top_k=request.top_k
        )
        
        # Log after retrieval with actual document count
        logger.log_query_processed(request.question, len(documents))
        
        if not documents or len(documents) == 0:
            logger.log_error("query_processing", f"No documents retrieved for query: {request.question}")
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question. Please try rephrasing or adding more documents to the knowledge base.",
                sources=[] if not request.include_sources else [],
                confidence=0.0
            )
        
        # Generate response using LLM
        answer = generator.generate_response(request.question, documents)
        
        logger.log_response_generated(request.question, len(answer))
        
        return QueryResponse(
            answer=answer,
            sources=documents if request.include_sources else None,
            confidence=0.8  # Placeholder confidence score
        )
        
    except Exception as e:
        logger.log_error("query_processing", str(e))
        import traceback
        logger.log_error("query_processing", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

# Ingestion endpoint
@app.post("/ingest", response_model=IngestionResponse)
async def ingest_data(request: IngestionRequest):
    """
    Ingest data from a file or directory.
    """
    try:
        if request.source_type == "directory":
            result = ingestion.ingest_from_directory(request.source_path)
        elif request.source_type == "file":
            result = ingestion.ingest_single_file(request.source_path)
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type. Use 'directory' or 'file'")
        
        return IngestionResponse(
            status=result.get("status", "success"),
            total_chunks=result.get("total_chunks", 0),
            details=result
        )
        
    except Exception as e:
        logger.log_error("data_ingestion", str(e))
        raise HTTPException(status_code=500, detail=f"Error ingesting data: {str(e)}")

# Stats endpoint
@app.get("/stats")
async def get_stats():
    """
    Get statistics about the knowledge base.
    """
    try:
        stats = retriever.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

# Clear database endpoint
@app.post("/database/clear")
async def clear_database():
    """
    Clear the entire database (delete all documents).
    """
    try:
        from rag.vectorstore import VectorStore
        vectorstore = VectorStore()
        success = vectorstore.delete_collection()
        
        if success:
            logger.log_info("Database cleared successfully")
            return {
                "status": "success",
                "message": "Database cleared successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear database")
    except Exception as e:
        logger.log_error("clear_database", str(e))
        raise HTTPException(status_code=500, detail=f"Error clearing database: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Smart RAG for Law Students API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    # Setup logging
    setup_logging(log_file="logs/rag_api.log")
    
    print("Starting RAG API Server...")
    print("Server will be available at: http://localhost:8000")
    print("API docs will be available at: http://localhost:8000/docs")
    print("=" * 50)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")


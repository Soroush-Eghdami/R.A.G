# app/api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.retriever import DocumentRetriever
from rag.generator import LLMGenerator
from rag.ingestion import DataIngestion
from rag.utils.logging_utils import setup_logging, RAGLogger

# Initialize FastAPI app
app = FastAPI(
    title="Smart RAG for Law Students",
    description="A RAG system specialized for law students to ask questions and get comprehensive answers",
    version="1.0.0"
)

# Initialize components
retriever = DocumentRetriever()
generator = LLMGenerator()
ingestion = DataIngestion()
logger = RAGLogger("api")

# Pydantic models for API
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: Optional[float] = None

class IngestionRequest(BaseModel):
    source_type: str  # "directory", "file", "api"
    source_path: Optional[str] = None
    api_configs: Optional[List[Dict[str, Any]]] = None

class IngestionResponse(BaseModel):
    status: str
    total_chunks: int
    details: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    model_available: bool
    collection_stats: Dict[str, Any]

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Smart RAG for Law Students API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        model_available = generator.check_model_availability()
        collection_stats = retriever.get_collection_stats()
        
        return HealthResponse(
            status="healthy" if model_available else "degraded",
            model_available=model_available,
            collection_stats=collection_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Ask a question to the RAG system.
    """
    try:
        logger.log_query_processed(request.question, 0)
        
        # Retrieve relevant documents
        documents = retriever.retrieve_relevant_documents(
            request.question, 
            top_k=request.top_k
        )
        
        if not documents:
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question. Please try rephrasing or adding more documents to the knowledge base.",
                sources=[],
                confidence=0.0
            )
        
        # Generate response using LLM
        answer = generator.generate_response(request.question, documents)
        
        logger.log_response_generated(request.question, len(answer))
        
        return QueryResponse(
            answer=answer,
            sources=documents,
            confidence=0.8  # Placeholder confidence score
        )
        
    except Exception as e:
        logger.log_error("query_processing", str(e))
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/ingest", response_model=IngestionResponse)
async def ingest_data(request: IngestionRequest):
    """
    Ingest data from various sources.
    """
    try:
        if request.source_type == "directory":
            if not request.source_path:
                raise HTTPException(status_code=400, detail="source_path required for directory ingestion")
            
            result = ingestion.ingest_from_directory(request.source_path)
            
        elif request.source_type == "file":
            if not request.source_path:
                raise HTTPException(status_code=400, detail="source_path required for file ingestion")
            
            result = ingestion.ingest_single_file(request.source_path)
            
        elif request.source_type == "api":
            if not request.api_configs:
                raise HTTPException(status_code=400, detail="api_configs required for API ingestion")
            
            result = ingestion.ingest_from_apis(request.api_configs)
            
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")
        
        return IngestionResponse(
            status=result.get("status", "success"),
            total_chunks=result.get("total_chunks", 0),
            details=result
        )
        
    except Exception as e:
        logger.log_error("data_ingestion", str(e))
        raise HTTPException(status_code=500, detail=f"Error ingesting data: {str(e)}")

@app.get("/search/{topic}")
async def search_by_topic(topic: str, top_k: int = 3):
    """
    Search for documents related to a specific legal topic.
    """
    try:
        documents = retriever.search_by_topic(topic, top_k)
        return {
            "topic": topic,
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching topic: {str(e)}")

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

if __name__ == "__main__":
    # Setup logging
    setup_logging(log_file="logs/rag_api.log")
    
    # Run the API server
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


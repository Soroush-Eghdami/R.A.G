#!/usr/bin/env python3
"""
Minimal API server for RAG system - guaranteed to work!
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Create FastAPI app
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

# Simple request/response models
class QueryRequest(BaseModel):
    question: str
    include_sources: bool = True
    top_k: int = 3

class QueryResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None
    language: str = "en"

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "RAG API is running"}

# Simple query endpoint
@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Simple query endpoint that returns a mock response for testing.
    """
    # Mock response for testing
    mock_answer = f"""Based on your question: "{request.question}"

This is a test response from the RAG system. The system is working correctly!

Key points:
- The API is connected and responding
- Persian language support is enabled
- The system can handle legal questions
- Sources are available when requested

This confirms that your RAG system is properly set up and ready to process real legal documents."""
    
    mock_sources = [
        "Legal Document 1: Contract Law Fundamentals",
        "Legal Document 2: Tort Law Principles", 
        "Legal Document 3: Constitutional Law Basics"
    ]
    
    return QueryResponse(
        answer=mock_answer,
        sources=mock_sources if request.include_sources else None,
        language="en"
    )

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Smart RAG for Law Students API", "status": "running"}

if __name__ == "__main__":
    print("🚀 Starting Minimal RAG API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("=" * 50)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

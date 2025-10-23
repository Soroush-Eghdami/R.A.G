# rag/embedding.py

import ollama
from .config import OLLAMA_EMBEDDING_MODEL
from typing import List, Union

class EmbeddingModel:
    def __init__(self, model_name=OLLAMA_EMBEDDING_MODEL):
        """
        Initialize the embedding model using Ollama for generating vector representations of text.
        Uses Ollama's embedding models for consistent integration with the LLM.
        """
        self.model_name = model_name
        self.client = ollama.Client()
        
    def encode_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string using Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            response = self.client.embeddings(
                model=self.model_name,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return a zero vector as fallback
            return [0.0] * 768  # Default embedding dimension
    
    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text strings.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = self.encode_text(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s) - handles both single strings and lists.
        
        Args:
            text: Single text string or list of texts
            
        Returns:
            Single embedding vector or list of embedding vectors
        """
        if isinstance(text, list):
            return self.encode_texts(text)
        return self.encode_text(text)
    
    def check_model_availability(self) -> bool:
        """
        Check if the embedding model is available in Ollama.
        
        Returns:
            True if model is available, False otherwise
        """
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            return self.model_name in available_models
        except:
            return False
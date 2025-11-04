# rag/embedding.py

import ollama
from .config import EMBEDDING_MODEL, EMBEDDING_PROVIDER, OLLAMA_EMBEDDING_MODEL
from typing import List, Union
import os

class EmbeddingModel:
    def __init__(self, model_name=None, provider=None):
        """
        Initialize the embedding model.
        
        Supports both Ollama and sentence-transformers models.
        For best multilingual support (Persian/Arabic), use sentence-transformers.
        
        Args:
            model_name: Model name (e.g., "paraphrase-multilingual-MiniLM-L12-v2")
            provider: "ollama" or "sentence-transformers" (defaults to config)
        """
        self.provider = provider or EMBEDDING_PROVIDER
        self.model_name = model_name or EMBEDDING_MODEL
        
        # Extract model name if format is "provider:model_name"
        if ":" in self.model_name:
            parts = self.model_name.split(":", 1)
            if len(parts) == 2:
                self.provider = parts[0]
                self.model_name = parts[1]
        
        # Initialize based on provider
        if self.provider == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading sentence-transformers model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                self.client = None
                print(f"Successfully loaded {self.model_name}")
            except ImportError:
                print("Warning: sentence-transformers not installed. Falling back to Ollama.")
                print("Install with: pip install sentence-transformers")
                self.provider = "ollama"
                self.model_name = OLLAMA_EMBEDDING_MODEL
                self.model = None
                self.client = ollama.Client()
            except Exception as e:
                print(f"Error loading sentence-transformers model: {e}")
                print("Falling back to Ollama...")
                self.provider = "ollama"
                self.model_name = OLLAMA_EMBEDDING_MODEL
                self.model = None
                self.client = ollama.Client()
        else:
            # Default to Ollama
            self.model = None
            self.client = ollama.Client()
        
    def encode_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Supports both Ollama and sentence-transformers providers.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        if self.provider == "sentence-transformers" and self.model:
            try:
                # sentence-transformers handles single text
                embedding = self.model.encode(text, convert_to_numpy=False, show_progress_bar=False)
                # Convert to list if it's a numpy array
                if hasattr(embedding, 'tolist'):
                    return embedding.tolist()
                return list(embedding)
            except Exception as e:
                print(f"Error generating embedding with sentence-transformers: {e}")
                return [0.0] * 384  # Default embedding dimension
        else:
            # Use Ollama
            try:
                response = self.client.embeddings(
                    model=self.model_name,
                    prompt=text
                )
                return response['embedding']
            except Exception as e:
                print(f"Error generating embedding with Ollama: {e}")
                # Return a zero vector as fallback
                return [0.0] * 384  # Default embedding dimension
    
    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text strings.
        
        Uses batch processing for better performance with sentence-transformers.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.provider == "sentence-transformers" and self.model:
            try:
                # sentence-transformers can batch process - much faster!
                embeddings = self.model.encode(
                    texts, 
                    convert_to_numpy=False, 
                    show_progress_bar=False,
                    batch_size=32  # Process in batches for better performance
                )
                # Convert to list of lists
                if hasattr(embeddings, 'tolist'):
                    return embeddings.tolist()
                return [list(emb) for emb in embeddings]
            except Exception as e:
                print(f"Error generating batch embeddings with sentence-transformers: {e}")
                # Fall back to sequential processing
                return [[0.0] * 384 for _ in texts]
        else:
            # Use Ollama (sequential processing)
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
        Check if the embedding model is available.
        
        Supports both Ollama and sentence-transformers providers.
        
        Returns:
            True if model is available, False otherwise
        """
        if self.provider == "sentence-transformers":
            # For sentence-transformers, check if model is loaded
            return self.model is not None
        else:
            # For Ollama, check if model is in the list
            try:
                models = self.client.list()
                available_models = []
                for model in models.get('models', []):
                    if isinstance(model, dict) and 'name' in model:
                        available_models.append(model['name'])
                    elif isinstance(model, str):
                        available_models.append(model)
                return self.model_name in available_models
            except:
                return False
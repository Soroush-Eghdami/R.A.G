# rag/vectorstore.py

import chromadb
from chromadb.utils import embedding_functions
from .config import VECTOR_DB_PATH
from .embedding import EmbeddingModel

class VectorStore:
    def __init__(self, collection_name="student_rag", embedding_model=None, embedding_provider=None):
        """
        Initializes (or loads) a ChromaDB collection.
        If the collection already exists, it loads it;
        otherwise, it creates a new one.
        
        Args:
            collection_name: Name of the ChromaDB collection
            embedding_model: Custom embedding model name (optional)
            embedding_provider: Custom embedding provider (optional)
        """
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection_name = collection_name

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

        # Use custom embedding model if provided, otherwise use default
        if embedding_model:
            self.embedding_model = EmbeddingModel(model_name=embedding_model, provider=embedding_provider)
        else:
            self.embedding_model = EmbeddingModel()

    def add_documents(self, chunks):
        """
        Adds a list of text chunks to the vector store.
        Automatically generates embeddings.
        """
        # Embeddings are generated in encode_texts with progress bar
        embeddings = self.embedding_model.encode_texts(chunks)

        # Each document must have a unique ID
        # Use timestamp + index for better uniqueness
        import time
        base_id = int(time.time())
        ids = [f"doc_{base_id}_{i}" for i in range(len(chunks))]

        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids
        )
        print(f"✓ Added {len(chunks)} documents to the collection '{self.collection_name}'.")

    def query(self, query_text, top_k=3):
        """
        Searches for the most relevant documents to the query_text.
        Returns top_k matches based on vector similarity.
        """
        query_embedding = self.embedding_model.encode_text(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        documents = results.get("documents", [[]])[0]
        return documents
    
    def delete_collection(self):
        """
        Delete the entire collection to start fresh.
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"Collection '{self.collection_name}' deleted successfully.")
            # Recreate empty collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    def get_collection_stats(self):
        """
        Get statistics about the collection.
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "status": "active"
            }
        except Exception as e:
            return {
                "collection_name": self.collection_name,
                "total_documents": 0,
                "status": "error",
                "error": str(e)
            }

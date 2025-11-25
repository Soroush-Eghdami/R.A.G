# rag/vectorstore.py

import chromadb
from chromadb.utils import embedding_functions
from .config import VECTOR_DB_PATH
from .embedding import EmbeddingModel

class VectorStore:
    def __init__(self, collection_name="student_rag"):
        """
        Initializes (or loads) a ChromaDB collection.
        If the collection already exists, it loads it;
        otherwise, it creates a new one.
        """
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection_name = collection_name

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

        # Use your existing embedding model
        self.embedding_model = EmbeddingModel()

    def add_documents(self, chunks):
        """
        Adds a list of text chunks to the vector store.
        Automatically generates embeddings.
        """
        embeddings = self.embedding_model.encode_texts(chunks)

        # Each document must have a unique ID
        ids = [f"doc_{i}" for i in range(len(chunks))]

        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids
        )
        print(f"Added {len(chunks)} documents to the collection '{self.collection_name}'.")

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

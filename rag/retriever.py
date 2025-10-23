# rag/retriever.py

from .vectorstore import VectorStore
from .config import TOP_K
from typing import List, Dict, Any

class DocumentRetriever:
    def __init__(self, collection_name="student_rag"):
        """
        Initialize the document retriever.
        
        Args:
            collection_name: Name of the ChromaDB collection to use
        """
        self.vectorstore = VectorStore(collection_name=collection_name)
        self.collection_name = collection_name
    
    def retrieve_relevant_documents(self, query: str, top_k: int = TOP_K) -> List[str]:
        """
        Retrieve the most relevant documents for a given query.
        
        Args:
            query: User's question or search query
            top_k: Number of top documents to retrieve
            
        Returns:
            List of relevant document chunks
        """
        try:
            documents = self.vectorstore.query(query, top_k=top_k)
            return documents
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
    
    def retrieve_with_metadata(self, query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
        """
        Retrieve documents with additional metadata.
        
        Args:
            query: User's question or search query
            top_k: Number of top documents to retrieve
            
        Returns:
            List of dictionaries containing documents and metadata
        """
        try:
            query_embedding = self.vectorstore.embedding_model.encode_text(query)
            results = self.vectorstore.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            results_with_metadata = []
            for i, doc in enumerate(documents):
                result = {
                    'document': doc,
                    'metadata': metadatas[i] if i < len(metadatas) else {},
                    'distance': distances[i] if i < len(distances) else 0.0,
                    'relevance_score': 1 - distances[i] if i < len(distances) else 0.0
                }
                results_with_metadata.append(result)
            
            return results_with_metadata
            
        except Exception as e:
            print(f"Error retrieving documents with metadata: {e}")
            return []
    
    def search_by_topic(self, topic: str, top_k: int = TOP_K) -> List[str]:
        """
        Search for documents related to a specific legal topic.
        
        Args:
            topic: Legal topic to search for (e.g., "contract law", "criminal procedure")
            top_k: Number of top documents to retrieve
            
        Returns:
            List of relevant document chunks
        """
        # Enhance the query for better topic-based retrieval
        enhanced_query = f"legal topic: {topic} law legal concepts principles"
        return self.retrieve_relevant_documents(enhanced_query, top_k)
    
    def search_by_case_type(self, case_type: str, top_k: int = TOP_K) -> List[str]:
        """
        Search for documents related to a specific type of legal case.
        
        Args:
            case_type: Type of legal case (e.g., "civil", "criminal", "constitutional")
            top_k: Number of top documents to retrieve
            
        Returns:
            List of relevant document chunks
        """
        enhanced_query = f"{case_type} case law legal precedent court decision"
        return self.retrieve_relevant_documents(enhanced_query, top_k)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the document collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.vectorstore.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.collection_name,
                'status': 'active'
            }
        except Exception as e:
            return {
                'total_documents': 0,
                'collection_name': self.collection_name,
                'status': 'error',
                'error': str(e)
            }

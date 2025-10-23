# rag/generator.py

import ollama
from .config import OLLAMA_MODEL
from typing import List

class LLMGenerator:
    def __init__(self, model_name=OLLAMA_MODEL):
        """
        Initialize the LLM generator using Ollama.
        
        Args:
            model_name: Name of the Ollama model to use (default: llama3)
        """
        self.model_name = model_name
        self.client = ollama.Client()
        
    def generate_response(self, query: str, context_documents: List[str]) -> str:
        """
        Generate a response using the LLM with retrieved context.
        
        Args:
            query: User's question
            context_documents: Retrieved relevant documents
            
        Returns:
            Generated response from the LLM
        """
        # Prepare context from retrieved documents
        context = "\n\n".join(context_documents)
        
        # Create a law-student focused prompt
        prompt = f"""You are a helpful AI assistant specialized in legal studies for law students. 
        Use the following context to answer the student's question accurately and comprehensively.
        
        Context:
        {context}
        
        Student's Question: {query}
        
        Please provide a detailed, accurate answer based on the context provided. 
        If the context doesn't contain enough information to fully answer the question, 
        say so and provide what information you can. 
        Focus on being helpful for law students and cite relevant legal concepts when applicable.
        
        Answer:"""
        
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.7,  # Balanced creativity and accuracy
                    'top_p': 0.9,
                    'max_tokens': 1000
                }
            )
            
            return response['response']
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_law_summary(self, documents: List[str]) -> str:
        """
        Generate a summary of legal documents for law students.
        
        Args:
            documents: List of legal documents to summarize
            
        Returns:
            Summary of the legal content
        """
        context = "\n\n".join(documents)
        
        prompt = f"""You are a legal expert helping law students understand complex legal documents.
        Please provide a clear, structured summary of the following legal content:
        
        {context}
        
        Please organize your summary with:
        1. Key legal concepts
        2. Important cases or statutes mentioned
        3. Main legal principles
        4. Practical implications for law students
        
        Summary:"""
        
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.5,  # Lower temperature for more factual summaries
                    'top_p': 0.8
                }
            )
            
            return response['response']
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def check_model_availability(self) -> bool:
        """
        Check if the specified Ollama model is available.
        
        Returns:
            True if model is available, False otherwise
        """
        try:
            models = self.client.list()
            available_models = [str(model) for model in models.get('models', [])]
            # Check if our model name appears in any of the model strings
            return any(self.model_name in model for model in available_models)
        except:
            return False

# rag/generator.py

import ollama
from .config import OLLAMA_MODEL
from .utils.language_utils import language_detector
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
        # Detect query language for multilingual support
        query_language = language_detector.detect_language(query)
        
        # Prepare context from retrieved documents
        context = "\n\n".join(context_documents)
        
        # Get language-specific prompt prefix
        language_prefix = language_detector.get_language_prompt_prefix(query_language)
        
        # Create a law-student focused prompt with language awareness
        # Improved prompt to reduce hallucination
        prompt = f"""{language_prefix}
        
You are a helpful AI assistant specialized in legal studies for law students. 
Your task is to answer questions based ONLY on the provided context documents.

IMPORTANT RULES:
1. Base your answer STRICTLY on the information provided in the context below
2. If the context does not contain enough information to answer the question, explicitly state: "Based on the provided documents, I cannot find sufficient information to fully answer this question."
3. DO NOT make up information, cite sources that aren't in the context, or add knowledge from outside the context
4. If you reference specific information, indicate it comes from the provided documents
5. Be precise and factual - avoid speculation or assumptions

Context Documents:
{context}

Student's Question: {query}

Answer (based only on the context provided above):"""
        
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.3,  # Lower temperature for more factual, less creative responses
                    'top_p': 0.8,  # Lower top_p for more focused responses
                    'num_predict': 1000,  # max_tokens equivalent in Ollama
                    'repeat_penalty': 1.1  # Reduce repetition
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
        Provide a clear, structured summary based ONLY on the following legal content:
        
        {context}
        
        IMPORTANT: Base your summary STRICTLY on the information provided above. Do not add information not present in the documents.
        
        Please organize your summary with:
        1. Key legal concepts mentioned in the documents
        2. Important cases or statutes mentioned (only if present in the documents)
        3. Main legal principles described
        4. Practical implications for law students
        
        Summary:"""
        
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.3,  # Lower temperature for more factual summaries
                    'top_p': 0.8,
                    'num_predict': 800,
                    'repeat_penalty': 1.1
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
            models_response = self.client.list()
            models_list = models_response.get('models', [])
            if not models_list and hasattr(models_response, 'models'):
                models_list = models_response.models
            
            available_models = []
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
            
            # Check if our model name matches exactly or is contained in available models
            return any(self.model_name == m or self.model_name in m or m in self.model_name for m in available_models)
        except Exception as e:
            return False

# app/interface.py

import streamlit as st
import requests
import json
from typing import List, Dict, Any
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Smart RAG for Law Students",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

class RAGInterface:
    def __init__(self):
        self.api_url = API_BASE_URL
    
    def check_api_health(self) -> bool:
        """Check if the API is running and healthy."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def ask_question(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """Send a question to the RAG system."""
        try:
            response = requests.post(
                f"{self.api_url}/query",
                json={"question": question, "top_k": top_k},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def ingest_data(self, source_type: str, source_path: str = None, api_configs: List[Dict] = None) -> Dict[str, Any]:
        """Ingest data into the RAG system."""
        try:
            payload = {"source_type": source_type}
            if source_path:
                payload["source_path"] = source_path
            if api_configs:
                payload["api_configs"] = api_configs
            
            response = requests.post(
                f"{self.api_url}/ingest",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def main():
    """Main Streamlit interface."""
    st.title("⚖️ Smart RAG for Law Students")
    st.markdown("Ask questions about legal topics and get comprehensive answers from your knowledge base.")
    
    # Initialize interface
    rag_interface = RAGInterface()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Ask Questions", "Data Ingestion", "System Stats"])
    
    # Check API health
    if not rag_interface.check_api_health():
        st.error("❌ API is not running. Please start the API server first.")
        st.code("python -m app.api")
        return
    
    if page == "Ask Questions":
        render_question_page(rag_interface)
    elif page == "Data Ingestion":
        render_ingestion_page(rag_interface)
    elif page == "System Stats":
        render_stats_page(rag_interface)

def render_question_page(rag_interface: RAGInterface):
    """Render the question asking page."""
    st.header("Ask a Legal Question")
    
    # Question input
    question = st.text_area(
        "Enter your legal question:",
        placeholder="e.g., What are the key elements of a valid contract?",
        height=100
    )
    
    # Advanced options
    with st.expander("Advanced Options"):
        top_k = st.slider("Number of documents to retrieve", 1, 10, 3)
        temperature = st.slider("Response creativity", 0.0, 1.0, 0.7)
    
    # Ask question button
    if st.button("Ask Question", type="primary"):
        if question:
            with st.spinner("Thinking..."):
                result = rag_interface.ask_question(question, top_k)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                # Display answer
                st.subheader("Answer")
                st.write(result["answer"])
                
                # Display sources
                if result.get("sources"):
                    st.subheader("Sources")
                    for i, source in enumerate(result["sources"], 1):
                        with st.expander(f"Source {i}"):
                            st.text(source)
                
                # Display confidence
                if result.get("confidence"):
                    st.metric("Confidence", f"{result['confidence']:.2%}")
        else:
            st.warning("Please enter a question.")

def render_ingestion_page(rag_interface: RAGInterface):
    """Render the data ingestion page."""
    st.header("Data Ingestion")
    
    # Ingestion type selection
    ingestion_type = st.selectbox(
        "Select ingestion type:",
        ["Directory", "Single File", "API"]
    )
    
    if ingestion_type == "Directory":
        st.subheader("Ingest from Directory")
        directory_path = st.text_input("Directory path:", placeholder="/path/to/your/documents")
        
        if st.button("Ingest Directory"):
            if directory_path:
                with st.spinner("Ingesting data..."):
                    result = rag_interface.ingest_data("directory", source_path=directory_path)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"✅ Ingested {result['total_chunks']} chunks successfully!")
                    st.json(result)
            else:
                st.warning("Please enter a directory path.")
    
    elif ingestion_type == "Single File":
        st.subheader("Ingest Single File")
        file_path = st.text_input("File path:", placeholder="/path/to/your/document.pdf")
        
        if st.button("Ingest File"):
            if file_path:
                with st.spinner("Ingesting file..."):
                    result = rag_interface.ingest_data("file", source_path=file_path)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"✅ Ingested {result['total_chunks']} chunks successfully!")
                    st.json(result)
            else:
                st.warning("Please enter a file path.")
    
    elif ingestion_type == "API":
        st.subheader("Ingest from API")
        st.info("Configure your API endpoints in the code or use the example configuration.")
        
        # Example API configuration
        example_config = [
            {
                "url": "https://api.law.example.com/cases",
                "headers": {"Authorization": "Bearer YOUR_API_KEY"},
                "params": {"limit": 100}
            }
        ]
        
        api_configs_text = st.text_area(
            "API Configuration (JSON):",
            value=json.dumps(example_config, indent=2),
            height=200
        )
        
        if st.button("Ingest from API"):
            try:
                api_configs = json.loads(api_configs_text)
                with st.spinner("Ingesting from APIs..."):
                    result = rag_interface.ingest_data("api", api_configs=api_configs)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"✅ Ingested {result['total_chunks']} chunks successfully!")
                    st.json(result)
            except json.JSONDecodeError:
                st.error("Invalid JSON configuration.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def render_stats_page(rag_interface: RAGInterface):
    """Render the system statistics page."""
    st.header("System Statistics")
    
    if st.button("Refresh Stats"):
        with st.spinner("Loading statistics..."):
            stats = rag_interface.get_stats()
        
        if "error" in stats:
            st.error(f"Error: {stats['error']}")
        else:
            # Display key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Documents", stats.get("total_documents", 0))
            
            with col2:
                st.metric("Collection Name", stats.get("collection_name", "N/A"))
            
            with col3:
                status = stats.get("status", "unknown")
                st.metric("Status", "✅ Active" if status == "active" else "❌ Error")
            
            # Display full stats
            st.subheader("Detailed Statistics")
            st.json(stats)

if __name__ == "__main__":
    main()


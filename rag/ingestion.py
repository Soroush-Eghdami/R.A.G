# rag/ingestion.py

import os
from typing import List, Dict, Any
from tqdm import tqdm

from .loaders.txt_loader import load_txt_files
from .loaders.pdf_loader import load_pdf_files
from .loaders.docx_loader import load_docx_files
from .loaders.api_loader import load_from_multiple_apis, load_law_api_data
from .chunking import chunk_multiple_texts
from .vectorstore import VectorStore
from .config import DATA_DIR

class DataIngestion:
    def __init__(self, collection_name="student_rag"):
        """
        Initialize the data ingestion pipeline.
        
        Args:
            collection_name: Name of the ChromaDB collection to use
        """
        self.vectorstore = VectorStore(collection_name=collection_name)
        self.collection_name = collection_name
        
    def ingest_from_directory(self, directory_path: str, file_types: List[str] = None) -> Dict[str, Any]:
        """
        Ingest all supported files from a directory.
        
        Args:
            directory_path: Path to directory containing files
            file_types: List of file types to process (e.g., ['txt', 'pdf', 'docx'])
            
        Returns:
            Dictionary with ingestion results
        """
        if file_types is None:
            file_types = ['txt', 'pdf', 'docx']
        
        all_texts = []
        results = {
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_chunks': 0,
            'file_types_processed': []
        }
        
        print(f"Starting ingestion from: {directory_path}")
        
        # Process different file types
        for file_type in file_types:
            try:
                if file_type == 'txt':
                    texts = load_txt_files(directory_path)
                elif file_type == 'pdf':
                    texts = load_pdf_files(directory_path)
                elif file_type == 'docx':
                    texts = load_docx_files(directory_path)
                else:
                    print(f"⚠️ Unsupported file type: {file_type}")
                    continue
                
                all_texts.extend(texts)
                results['file_types_processed'].append(file_type)
                results['successful_files'] += len(texts)
                print(f"Processed {len(texts)} {file_type} files")
                
            except Exception as e:
                print(f"Error processing {file_type} files: {e}")
                results['failed_files'] += 1
        
        # Chunk and store the texts
        if all_texts:
            print("Chunking documents...")
            chunks = chunk_multiple_texts(all_texts)
            results['total_chunks'] = len(chunks)
            
            print(f"Storing {len(chunks)} chunks in vector database...")
            self.vectorstore.add_documents(chunks)
            
            print(f"Ingestion completed successfully!")
            print(f"   - Total chunks: {results['total_chunks']}")
            print(f"   - File types: {', '.join(results['file_types_processed'])}")
        
        return results
    
    def ingest_single_file(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest a single file.
        
        Args:
            file_path: Path to the file to ingest
            
        Returns:
            Dictionary with ingestion results
        """
        print(f"Ingesting single file: {file_path}")
        
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.txt':
                from .loaders.txt_loader import load_txt_file
                text = load_txt_file(file_path)
            elif file_extension == '.pdf':
                from .loaders.pdf_loader import load_pdf_file
                text = load_pdf_file(file_path)
            elif file_extension == '.docx':
                from .loaders.docx_loader import load_docx_file
                text = load_docx_file(file_path)
            else:
                return {
                    'status': 'error',
                    'error': f'Unsupported file type: {file_extension}'
                }
            
            # Chunk and store
            chunks = chunk_multiple_texts([text])
            self.vectorstore.add_documents(chunks)
            
            return {
                'file_path': file_path,
                'total_chunks': len(chunks),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'file_path': file_path,
                'status': 'error',
                'error': str(e)
            }
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the ingested data.
        
        Returns:
            Dictionary with ingestion statistics
        """
        return self.vectorstore.get_collection_stats()

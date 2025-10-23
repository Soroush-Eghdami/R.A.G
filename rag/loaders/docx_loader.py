# rag/loaders/docx_loader.py

from docx import Document
import os
from typing import List

def load_docx_file(file_path: str) -> str:
    """
    Load text content from a .docx file.
    
    Args:
        file_path: Path to the .docx file
        
    Returns:
        String content extracted from the DOCX
        
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If DOCX cannot be processed
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        doc = Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    
    except Exception as e:
        raise Exception(f"Error processing DOCX {file_path}: {str(e)}")

def load_docx_files(directory_path: str) -> List[str]:
    """
    Load all .docx files from a directory.
    
    Args:
        directory_path: Path to directory containing .docx files
        
    Returns:
        List of text contents from all .docx files
    """
    contents = []
    
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    for filename in os.listdir(directory_path):
        if filename.endswith('.docx'):
            file_path = os.path.join(directory_path, filename)
            try:
                content = load_docx_file(file_path)
                contents.append(content)
                print(f"✅ Loaded: {filename}")
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    
    return contents


# rag/loaders/pdf_loader.py

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available. PDF processing will be limited.")

import os
from typing import List

def load_pdf_file(file_path: str) -> str:
    """
    Load text content from a PDF file.
    
    Args:
        file_path: Path to the .pdf file
        
    Returns:
        String content extracted from the PDF
        
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If PDF cannot be processed
    """
    if not PYMUPDF_AVAILABLE:
        raise Exception("PyMuPDF is not available. Cannot process PDF files.")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        doc = fitz.open(file_path)
        text = ""
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()
            text += "\n"  # Add newline between pages
        
        doc.close()
        return text.strip()
    
    except Exception as e:
        raise Exception(f"Error processing PDF {file_path}: {str(e)}")

def load_pdf_files(directory_path: str) -> List[str]:
    """
    Load all .pdf files from a directory.
    
    Args:
        directory_path: Path to directory containing .pdf files
        
    Returns:
        List of text contents from all .pdf files
    """
    contents = []
    
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(directory_path, filename)
            try:
                content = load_pdf_file(file_path)
                contents.append(content)
                print(f"✅ Loaded: {filename}")
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    
    return contents


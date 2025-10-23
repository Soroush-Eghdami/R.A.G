# rag/loaders/txt_loader.py

import os
from typing import List

def load_txt_file(file_path: str) -> str:
    """
    Load text content from a .txt file.
    
    Args:
        file_path: Path to the .txt file
        
    Returns:
        String content of the file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file encoding is not supported
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as file:
            content = file.read()
        return content

def load_txt_files(directory_path: str) -> List[str]:
    """
    Load all .txt files from a directory.
    
    Args:
        directory_path: Path to directory containing .txt files
        
    Returns:
        List of text contents from all .txt files
    """
    contents = []
    
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    for filename in os.listdir(directory_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            try:
                content = load_txt_file(file_path)
                contents.append(content)
                print(f"✅ Loaded: {filename}")
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    
    return contents


# rag/chunking.py

from .config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_text(text):
    """
    Splits text into overlapping chunks for RAG.
    Each chunk has length CHUNK_SIZE with CHUNK_OVERLAP overlap.
    
    Example:
        If CHUNK_SIZE=500 and CHUNK_OVERLAP=50,
        chunks will be 500 characters long, and
        each next chunk will start 450 characters after the previous one.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + CHUNK_SIZE, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def chunk_multiple_texts(texts):
    """
    Splits multiple documents into chunks.
    :param texts: list of strings (documents)
    :return: list of chunks (strings)
    """
    all_chunks = []
    for doc in texts:
        all_chunks.extend(chunk_text(doc))
    return all_chunks

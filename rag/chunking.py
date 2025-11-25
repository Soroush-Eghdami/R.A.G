# rag/chunking.py

import re
from .config import CHUNK_SIZE, CHUNK_OVERLAP
from .utils.language_utils import language_detector

def chunk_text(text, preserve_structure: bool = True):
    """
    Splits text into overlapping chunks for RAG.
    Intelligently handles structured documents (especially .docx with headings).
    Each chunk has length CHUNK_SIZE with CHUNK_OVERLAP overlap.
    Supports Persian and Arabic text with appropriate chunking.

    Args:
        text: Text to chunk
        preserve_structure: If True, tries to preserve document structure (headings, sections)

    Example:
        If CHUNK_SIZE=500 and CHUNK_OVERLAP=50,
        chunks will be 500 characters long, and
        each next chunk will start 450 characters after the previous one.
    """
    # Detect language and normalize if needed
    language = language_detector.detect_language(text)
    
    if language_detector.is_persian_text(text):
        text = language_detector.normalize_persian_text(text)
    
    # Check if text has structured markers (from .docx with headings)
    has_structure = preserve_structure and '[HEADING_LEVEL_' in text
    
    if has_structure:
        return chunk_structured_text(text)
    else:
        return chunk_simple_text(text)


def chunk_structured_text(text):
    """
    Chunk text that contains structured markers (headings from .docx files).
    Tries to keep sections together and preserve heading context.
    """
    chunks = []
    
    # Split by heading markers to identify sections
    # Pattern: [HEADING_LEVEL_N]heading text[/HEADING_LEVEL_N]
    heading_pattern = r'\[HEADING_LEVEL_(\d+)\](.*?)\[/HEADING_LEVEL_\1\]'
    
    # Find all headings and their positions
    sections = []
    last_end = 0
    
    for match in re.finditer(heading_pattern, text):
        # Get content before this heading
        if match.start() > last_end:
            prev_content = text[last_end:match.start()].strip()
            if prev_content:
                sections.append({"type": "content", "text": prev_content})
        
        # Add heading
        heading_level = int(match.group(1))
        heading_text = match.group(2).strip()
        sections.append({
            "type": "heading",
            "level": heading_level,
            "text": heading_text
        })
        
        last_end = match.end()
    
    # Add remaining content after last heading
    if last_end < len(text):
        remaining = text[last_end:].strip()
        if remaining:
            sections.append({"type": "content", "text": remaining})
    
    # If no headings found, fall back to simple chunking
    if not sections:
        return chunk_simple_text(text)
    
    # Build chunks preserving structure
    current_chunk = ""
    current_heading = None
    current_heading_level = 0
    heading_context = []  # Stack of headings for nested sections
    
    for section in sections:
        if section["type"] == "heading":
            # Update heading context stack
            heading_level = section["level"]
            # Remove headings at same or deeper level
            heading_context = [h for h in heading_context if h["level"] < heading_level]
            # Add new heading
            heading_context.append({
                "level": heading_level,
                "text": section["text"]
            })
            
            # Start new chunk with heading context (don't save old chunk yet, wait for content)
            current_heading = section["text"]
            current_heading_level = heading_level
            
            # Build heading prefix with hierarchy
            if heading_context:
                heading_prefix = " > ".join([h["text"] for h in heading_context])
                current_chunk = f"[Section: {heading_prefix}]\n"
            else:
                current_chunk = f"[Section: {current_heading}]\n"
        else:
            # Add content to current chunk
            content = section["text"]
            
            # If adding this content would exceed chunk size
            if len(current_chunk) + len(content) > CHUNK_SIZE:
                # Only save if chunk has meaningful content (more than just heading)
                chunk_text = current_chunk.strip()
                if chunk_text and len(chunk_text) > 100:  # Minimum meaningful chunk size
                    chunks.append(chunk_text)
                    # Start new chunk with heading context
                    if heading_context:
                        heading_prefix = " > ".join([h["text"] for h in heading_context])
                        current_chunk = f"[Section: {heading_prefix}]\n{content}"
                    elif current_heading:
                        current_chunk = f"[Section: {current_heading}]\n{content}"
                    else:
                        current_chunk = content
                else:
                    # Chunk too small, just add content and continue
                    current_chunk += content + "\n"
            else:
                current_chunk += content + "\n"
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # If chunks are too large, split them further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= CHUNK_SIZE:
            final_chunks.append(chunk)
        else:
            # Split large chunks while preserving structure
            final_chunks.extend(split_large_chunk(chunk))
    
    return final_chunks


def split_large_chunk(chunk):
    """Split a chunk that's too large into smaller pieces with overlap."""
    chunks = []
    start = 0
    chunk_length = len(chunk)
    
    while start < chunk_length:
        end = min(start + CHUNK_SIZE, chunk_length)
        
        # Try to break at sentence boundary
        if end < chunk_length:
            # Look for sentence endings near the end
            for i in range(end, max(start + CHUNK_SIZE - 100, start), -1):
                if chunk[i] in '.!?\n':
                    end = i + 1
                    break
        
        sub_chunk = chunk[start:end].strip()
        if sub_chunk:
            chunks.append(sub_chunk)
        
        start += CHUNK_SIZE - CHUNK_OVERLAP
    
    return chunks


def chunk_simple_text(text):
    """
    Simple character-based chunking for unstructured text.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + CHUNK_SIZE, text_length)
        
        # Try to break at sentence boundary if possible
        if end < text_length:
            # Look for sentence endings near the end
            for i in range(end, max(start + CHUNK_SIZE - 100, start), -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def chunk_multiple_texts(texts):
    """
    Splits multiple documents into chunks.
    Automatically detects and preserves structure in .docx files.
    
    Args:
        texts: list of strings (documents)
        
    Returns:
        list of chunks (strings)
    """
    all_chunks = []
    for doc in texts:
        all_chunks.extend(chunk_text(doc, preserve_structure=True))
    return all_chunks

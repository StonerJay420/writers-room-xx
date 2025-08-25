"""Text chunking utilities for RAG."""
from typing import List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


def chunk_text(
    text: str, 
    max_tokens: int = 900, 
    stride: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunk text into overlapping segments.
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk (using word count as proxy)
        stride: Overlap between chunks in tokens
        
    Returns:
        List of chunk dictionaries with metadata
    """
    # Split into words (simple tokenization)
    words = text.split()
    chunks = []
    
    # Calculate chunk parameters
    chunk_size = max_tokens
    step_size = max(1, chunk_size - stride)
    
    for i in range(0, len(words), step_size):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        
        # Skip empty chunks
        if not chunk_text.strip():
            continue
            
        chunks.append({
            "chunk_id": f"chunk_{i}",
            "text": chunk_text,
            "start_word": i,
            "end_word": min(i + chunk_size, len(words)),
            "word_count": len(chunk_words)
        })
        
        # Stop if we've reached the end
        if i + chunk_size >= len(words):
            break
    
    return chunks


def chunk_markdown(
    text: str, 
    max_tokens: int = 900, 
    stride: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunk markdown text with awareness of structure.
    
    Args:
        text: Markdown text to chunk
        max_tokens: Maximum tokens per chunk
        stride: Overlap between chunks
        
    Returns:
        List of chunk dictionaries with line-based metadata
    """
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_tokens = 0
    start_line = 0
    
    for i, line in enumerate(lines):
        # Estimate tokens (words as proxy)
        line_tokens = len(line.split())
        
        # Check if adding this line would exceed limit
        if current_tokens + line_tokens > max_tokens and current_chunk:
            # Save current chunk
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                "chunk_id": f"chunk_{len(chunks)}",
                "start_line": start_line + 1,  # 1-indexed
                "end_line": i,  # 1-indexed, exclusive
                "text": chunk_text,
                "token_count": current_tokens
            })
            
            # Start new chunk with overlap
            overlap_start = max(0, len(current_chunk) - (stride // 10))  # Approximate overlap
            current_chunk = current_chunk[overlap_start:]
            current_tokens = sum(len(c.split()) for c in current_chunk)
            start_line = i - len(current_chunk) + 1
        
        # Add line to current chunk
        current_chunk.append(line)
        current_tokens += line_tokens
    
    # Save final chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        chunks.append({
            "chunk_id": f"chunk_{len(chunks)}",
            "start_line": start_line + 1,
            "end_line": len(lines),
            "text": chunk_text,
            "token_count": current_tokens
        })
    
    return chunks
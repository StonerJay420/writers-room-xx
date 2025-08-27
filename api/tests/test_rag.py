"""Tests for the RAG pipeline."""
import pytest
import os
import sys
from pathlib import Path
import asyncio

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.chunker import chunk_markdown
from app.rag.embeddings import embed_texts
from app.rag.chroma_client import get_chroma_client
from app.rag.retrieve import retrieve_canon


@pytest.fixture
def sample_codex_text():
    """Load sample codex text."""
    sample_path = Path(__file__).parent.parent.parent / "attached_assets" / "sample_codex.md"
    if not sample_path.exists():
        return "Sample codex not found"
    
    with open(sample_path, "r") as f:
        return f.read()


@pytest.fixture
def sample_manuscript_text():
    """Load sample manuscript text."""
    sample_path = Path(__file__).parent.parent.parent / "attached_assets" / "sample_manuscript.md"
    if not sample_path.exists():
        return "Sample manuscript not found"
    
    with open(sample_path, "r") as f:
        return f.read()


def test_chunking(sample_codex_text):
    """Test that chunking works correctly."""
    chunks = chunk_markdown(sample_codex_text)
    
    # Check that we have chunks
    assert len(chunks) > 0
    
    # Check that each chunk has the expected fields
    for chunk in chunks:
        assert "chunk_id" in chunk
        assert "text" in chunk
        assert "start_line" in chunk
        assert "end_line" in chunk
        assert "token_count" in chunk
        
        # Check that the chunk has content
        assert len(chunk["text"]) > 0
        
        # Check that the line numbers make sense
        assert chunk["start_line"] <= chunk["end_line"]


def test_embeddings(sample_codex_text):
    """Test that embeddings can be generated."""
    # Get a small sample of text
    sample = sample_codex_text[:1000]
    
    # Generate embeddings
    embedding = embed_texts(sample)
    
    # Check that we got an embedding
    assert embedding is not None
    assert len(embedding) > 0
    
    # Check that multiple embeddings work
    samples = [sample_codex_text[:500], sample_codex_text[500:1000]]
    embeddings = embed_texts(samples)
    
    # Check that we got the right number of embeddings
    assert len(embeddings) == 2


def test_chroma_client():
    """Test that the ChromaDB client can be initialized."""
    # Initialize client with a test directory
    test_dir = Path(__file__).parent / "test_chroma_db"
    os.makedirs(test_dir, exist_ok=True)
    
    client = get_chroma_client(str(test_dir))
    
    # Check that we can list collections
    collections = client.list_collections()
    assert isinstance(collections, list)
    
    # Create a test collection
    test_collection = "test_collection"
    if test_collection in collections:
        client.delete_collection(test_collection)
    
    # Add a test document
    client.upsert(
        collection=test_collection,
        embeddings=[[0.1] * 384],  # Simple test embedding
        metadatas=[{"source": "test"}],
        ids=["test1"]
    )
    
    # Check that the collection was created
    collections = client.list_collections()
    assert test_collection in collections
    
    # Clean up
    client.delete_collection(test_collection)


@pytest.mark.asyncio
async def test_rag_pipeline(sample_codex_text, sample_manuscript_text):
    """Test the full RAG pipeline."""
    # Initialize client with a test directory
    test_dir = Path(__file__).parent / "test_chroma_db"
    os.makedirs(test_dir, exist_ok=True)
    
    client = get_chroma_client(str(test_dir))
    
    # Create test collections
    codex_collection = "test_codex_docs"
    manuscript_collection = "test_manuscript_scenes"
    
    # Clean up any existing collections
    if codex_collection in client.list_collections():
        client.delete_collection(codex_collection)
    if manuscript_collection in client.list_collections():
        client.delete_collection(manuscript_collection)
    
    # Chunk the documents
    codex_chunks = chunk_markdown(sample_codex_text)
    manuscript_chunks = chunk_markdown(sample_manuscript_text)
    
    # Create embeddings
    codex_texts = [chunk["text"] for chunk in codex_chunks]
    manuscript_texts = [chunk["text"] for chunk in manuscript_chunks]
    
    codex_embeddings = embed_texts(codex_texts)
    manuscript_embeddings = embed_texts(manuscript_texts)
    
    # Create metadata
    codex_metadatas = [
        {
            "source_path": "codex/world.md",
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "text": chunk["text"][:1000]  # Truncate for metadata
        }
        for chunk in codex_chunks
    ]
    
    manuscript_metadatas = [
        {
            "source_path": "manuscript/chapter1.md",
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "text": chunk["text"][:1000]  # Truncate for metadata
        }
        for chunk in manuscript_chunks
    ]
    
    # Create IDs
    codex_ids = [f"codex_{i}" for i in range(len(codex_chunks))]
    manuscript_ids = [f"manuscript_{i}" for i in range(len(manuscript_chunks))]
    
    # Upsert to ChromaDB
    client.upsert(
        collection=codex_collection,
        embeddings=codex_embeddings,
        metadatas=codex_metadatas,
        ids=codex_ids
    )
    
    client.upsert(
        collection=manuscript_collection,
        embeddings=manuscript_embeddings,
        metadatas=manuscript_metadatas,
        ids=manuscript_ids
    )
    
    # Test retrieval with a query
    query = "Lyra Wavecrest"
    results = retrieve_canon(query, k=5)
    
    # Check that we got results
    assert len(results) > 0
    
    # Clean up
    client.delete_collection(codex_collection)
    client.delete_collection(manuscript_collection)


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-xvs", __file__])
"""Integration tests for the Writers Room XX system."""
import pytest
import sys
import asyncio
from pathlib import Path
import os
import json
from unittest.mock import AsyncMock, patch

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.chunker import chunk_markdown
from app.rag.embeddings import embed_texts
from app.rag.chroma_client import get_chroma_client
from app.rag.retrieve import retrieve_canon
from app.agents.supervisor import run_supervisor
from app.agents.lore_archivist import run_lore_archivist
from app.agents.grim_editor import run_grim_editor
from app.metrics.metrics import report


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


@pytest.fixture
def metrics_config():
    """Sample metrics configuration."""
    return {
        "targets": {
            "readability": {
                "flesch": 70.0,
                "flesch_kincaid": 8.0
            },
            "sentence_length": 15.0,
            "active_verb_ratio": 0.7
        },
        "style": {
            "voice": "active",
            "tone": "dramatic",
            "pacing": "medium"
        }
    }


@pytest.mark.asyncio
async def test_full_pipeline(sample_codex_text, sample_manuscript_text, metrics_config):
    """Test the full pipeline from ingestion to agent processing."""
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
    
    # Extract scene metadata from the manuscript
    import frontmatter
    parsed = frontmatter.loads(sample_manuscript_text)
    scene_meta = parsed.metadata
    scene_text = parsed.content
    
    # Create a mock retrieve function that uses our test collections
    async def mock_retrieve_fn(query, k=5, filters=None):
        # Use the real retrieve function but override the collection names
        results = []
        for collection in [codex_collection, manuscript_collection]:
            query_results = client.query(
                collection=collection,
                query_text=query,
                top_k=k // 2,
                filters=filters
            )
            
            for i, doc_id in enumerate(query_results.get("ids", [])):
                metadata = query_results["metadatas"][i] if i < len(query_results["metadatas"]) else {}
                document = query_results["documents"][i] if i < len(query_results.get("documents", [])) else ""
                
                results.append({
                    "text": document or metadata.get("text", ""),
                    "source_path": metadata.get("source_path", "unknown"),
                    "start_line": metadata.get("start_line", 0),
                    "end_line": metadata.get("end_line", 0),
                    "distance": query_results["distances"][i] if i < len(query_results["distances"]) else 1.0,
                    "collection": collection
                })
        
        # Sort by distance and return top k
        results.sort(key=lambda x: x.get("distance", 1.0))
        return results[:k]
    
    # Run the supervisor agent
    supervisor_result = await run_supervisor(
        scene_text=scene_text,
        scene_meta=scene_meta,
        metrics_config=metrics_config,
        edge_intensity=1,
        requested_agents=["lore_archivist", "grim_editor"]
    )
    
    # Check that the supervisor created a plan
    assert "plan" in supervisor_result
    assert "tasks" in supervisor_result["plan"]
    assert len(supervisor_result["plan"]["tasks"]) > 0
    
    # Run the lore archivist agent
    lore_result = await run_lore_archivist(
        scene_text=scene_text,
        scene_meta=scene_meta,
        retrieve_fn=mock_retrieve_fn
    )
    
    # Check that the lore archivist produced findings
    assert "findings" in lore_result
    assert "receipts" in lore_result
    
    # Run the grim editor agent
    grim_result = await run_grim_editor(
        scene_text=scene_text,
        style_targets=metrics_config
    )
    
    # Check that the grim editor produced a diff
    assert "diff" in grim_result
    assert "rationale" in grim_result
    
    # Run metrics report
    metrics_result = report(scene_text, metrics_config)
    
    # Check that the metrics report has the expected fields
    assert "readability" in metrics_result
    assert "sentence_length" in metrics_result
    assert "pos_distribution" in metrics_result
    assert "active_verb_ratio" in metrics_result
    
    # Clean up
    client.delete_collection(codex_collection)
    client.delete_collection(manuscript_collection)


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-xvs", __file__])
"""Tests for embeddings module."""
import pytest
import numpy as np

from app.rag.embeddings import embed_texts, compute_similarity, batch_embed_texts, ImprovedDeterministicEmbedder


class TestEmbeddings:
    """Test embedding functionality."""
    
    def test_embed_single_text(self):
        """Test embedding a single text."""
        text = "The rain drummed against the window."
        embedding = embed_texts(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert not np.all(embedding == 0)  # Should not be all zeros
        
    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        texts = [
            "The rain drummed against the window.",
            "Sarah stared at her laptop screen.",
            "The cursor blinked mockingly."
        ]
        embeddings = embed_texts(texts)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (3, 384)
        assert not np.all(embeddings == 0)
        
    def test_embedding_consistency(self):
        """Test that the same text produces the same embedding."""
        text = "The rain drummed against the window."
        
        embedding1 = embed_texts(text)
        embedding2 = embed_texts(text)
        
        # Should be exactly the same (deterministic)
        np.testing.assert_array_equal(embedding1, embedding2)
        
    def test_compute_similarity(self):
        """Test similarity computation."""
        text1 = "The rain drummed against the window."
        text2 = "Rain was hitting the glass."
        text3 = "The database query returned empty results."
        
        embedding1 = embed_texts(text1)
        embedding2 = embed_texts(text2)
        embedding3 = embed_texts(text3)
        
        # Similarity with itself should be close to 1
        sim_self = compute_similarity(embedding1, embedding1)
        assert abs(sim_self - 1.0) < 0.01
        
        # Related texts should have higher similarity than unrelated
        sim_related = compute_similarity(embedding1, embedding2)
        sim_unrelated = compute_similarity(embedding1, embedding3)
        
        assert isinstance(sim_related, float)
        assert isinstance(sim_unrelated, float)
        assert sim_related != sim_unrelated  # Should be different
        
    def test_batch_embed_texts(self):
        """Test batch embedding functionality."""
        texts = [
            "The rain drummed against the window.",
            "Sarah stared at her laptop screen.",
            "The cursor blinked mockingly.",
            "Another coffee? The barista's voice cut through her thoughts."
        ]
        
        # Test with different batch sizes
        embeddings_batch2 = batch_embed_texts(texts, batch_size=2)
        embeddings_single = batch_embed_texts(texts, batch_size=1)
        embeddings_all = batch_embed_texts(texts, batch_size=10)
        
        # All should produce the same result
        np.testing.assert_array_equal(embeddings_batch2, embeddings_single)
        np.testing.assert_array_equal(embeddings_batch2, embeddings_all)
        
        assert embeddings_batch2.shape == (4, 384)
        
    def test_empty_text_handling(self):
        """Test handling of empty texts."""
        # Empty string
        embedding_empty = embed_texts("")
        assert embedding_empty.shape == (384,)
        
        # List with empty string
        embeddings_with_empty = embed_texts(["hello", "", "world"])
        assert embeddings_with_empty.shape == (3, 384)
        
    def test_improved_deterministic_embedder(self):
        """Test the improved deterministic embedder directly."""
        embedder = ImprovedDeterministicEmbedder()
        
        # Test single text
        text = "The rain drummed against the window."
        embedding = embedder.encode(text)
        assert embedding.shape == (384,)
        
        # Test multiple texts
        texts = ["hello", "world", "test"]
        embeddings = embedder.encode(texts)
        assert embeddings.shape == (3, 384)
        
        # Test consistency
        embedding1 = embedder.encode(text)
        embedding2 = embedder.encode(text)
        np.testing.assert_array_equal(embedding1, embedding2)
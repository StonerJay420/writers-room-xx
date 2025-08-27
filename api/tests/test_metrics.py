"""Tests for the metrics engine."""
import pytest
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.metrics.metrics import (
    compute_readability,
    avg_sentence_length,
    pos_distribution,
    active_verb_ratio,
    report
)


@pytest.fixture
def sample_text():
    """Sample text for testing metrics."""
    return """
    The quick brown fox jumps over the lazy dog. This sentence is a pangram, 
    containing every letter of the alphabet. Writers often use pangrams to test 
    typewriters and fonts. The five boxing wizards jump quickly. 
    
    How vexingly quick daft zebras jump! Pack my box with five dozen liquor jugs.
    Amazingly few discotheques provide jukeboxes. Crazy Fredrick bought many very 
    exquisite opal jewels. The job requires extra pluck and zeal from every young wage earner.
    """


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
        }
    }


def test_compute_readability(sample_text):
    """Test readability metrics computation."""
    readability = compute_readability(sample_text)
    
    # Check that we have the expected metrics
    assert "flesch" in readability
    assert "flesch_kincaid" in readability
    assert "automated_readability" in readability
    assert "coleman_liau" in readability
    
    # Check that the values are reasonable
    assert 0 <= readability["flesch"] <= 100
    assert readability["flesch_kincaid"] >= 0


def test_avg_sentence_length(sample_text):
    """Test average sentence length calculation."""
    avg_length = avg_sentence_length(sample_text)
    
    # Check that the value is reasonable
    assert avg_length > 0
    
    # Test with empty text
    assert avg_sentence_length("") == 0.0
    
    # Test with single sentence
    assert avg_sentence_length("This is a test.") == 4.0


def test_pos_distribution(sample_text):
    """Test part-of-speech distribution calculation."""
    pos_dist = pos_distribution(sample_text)
    
    # Check that we have the expected categories
    assert "nouns" in pos_dist
    assert "verbs" in pos_dist
    assert "adjectives" in pos_dist
    assert "adverbs" in pos_dist
    assert "pronouns" in pos_dist
    assert "other" in pos_dist
    
    # Check that the values are reasonable
    assert pos_dist["nouns"] > 0
    assert pos_dist["verbs"] > 0
    
    # Test with empty text
    empty_dist = pos_distribution("")
    assert sum(empty_dist.values()) == 0


def test_active_verb_ratio(sample_text):
    """Test active verb ratio calculation."""
    ratio = active_verb_ratio(sample_text)
    
    # Check that the value is reasonable
    assert 0 <= ratio <= 1.0
    
    # Test with text containing only active verbs
    active_text = "Run jump swim fly drive write read speak think"
    active_ratio = active_verb_ratio(active_text)
    assert active_ratio > 0.5
    
    # Test with text containing only passive verbs
    passive_text = "is was were been has had"
    passive_ratio = active_verb_ratio(passive_text)
    assert passive_ratio < 0.5


def test_report(sample_text, metrics_config):
    """Test metrics report generation."""
    metrics_report = report(sample_text, metrics_config)
    
    # Check that we have the expected sections
    assert "readability" in metrics_report
    assert "sentence_length" in metrics_report
    assert "pos_distribution" in metrics_report
    assert "active_verb_ratio" in metrics_report
    assert "targets" in metrics_report
    assert "status" in metrics_report
    
    # Check that the targets are included
    assert "flesch" in metrics_report["targets"]
    assert "flesch_kincaid" in metrics_report["targets"]
    assert "sentence_length" in metrics_report["targets"]
    assert "active_verb_ratio" in metrics_report["targets"]
    
    # Check that the status is valid
    assert metrics_report["status"] in ["ok", "warning", "error"]


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-xvs", __file__])
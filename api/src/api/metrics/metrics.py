"""Text metrics computation for manuscript analysis."""
import textstat
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def compute_readability(text: str) -> Dict[str, float]:
    """
    Compute readability metrics using textstat.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with readability scores
    """
    try:
        return {
            "flesch": textstat.flesch_reading_ease(text),
            "flesch_kincaid": textstat.flesch_kincaid_grade(text),
            "automated_readability": textstat.automated_readability_index(text),
            "coleman_liau": textstat.coleman_liau_index(text)
        }
    except Exception as e:
        logger.error(f"Error computing readability: {e}")
        return {"flesch": 50.0, "flesch_kincaid": 10.0, "automated_readability": 10.0, "coleman_liau": 10.0}


def avg_sentence_length(text: str) -> float:
    """
    Calculate average sentence length in words.
    
    Args:
        text: Text to analyze
        
    Returns:
        Average words per sentence
    """
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return 0.0
    
    total_words = sum(len(sentence.split()) for sentence in sentences)
    return total_words / len(sentences)


def pos_distribution(text: str) -> Dict[str, int]:
    """
    Get part-of-speech distribution (simplified without spaCy).
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with POS counts
    """
    # Simple heuristic-based POS tagging
    words = text.lower().split()
    
    # Common patterns
    pronouns = {"i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their"}
    auxiliary_verbs = {"am", "is", "are", "was", "were", "be", "being", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can"}
    common_verbs = {"go", "goes", "went", "gone", "going", "come", "comes", "came", "coming", "take", "takes", "took", "taken", "taking", "make", "makes", "made", "making", "get", "gets", "got", "getting", "say", "says", "said", "saying", "see", "sees", "saw", "seen", "seeing", "know", "knows", "knew", "known", "knowing", "think", "thinks", "thought", "thinking", "look", "looks", "looked", "looking", "want", "wants", "wanted", "wanting", "give", "gives", "gave", "given", "giving", "use", "uses", "used", "using", "find", "finds", "found", "finding", "tell", "tells", "told", "telling", "ask", "asks", "asked", "asking", "work", "works", "worked", "working", "seem", "seems", "seemed", "seeming", "feel", "feels", "felt", "feeling", "try", "tries", "tried", "trying", "leave", "leaves", "left", "leaving", "call", "calls", "called", "calling"}
    
    counts = {
        "nouns": 0,
        "verbs": 0, 
        "adjectives": 0,
        "adverbs": 0,
        "pronouns": 0,
        "other": 0
    }
    
    for word in words:
        word_clean = re.sub(r'[^\w]', '', word)
        if not word_clean:
            continue
            
        if word_clean in pronouns:
            counts["pronouns"] += 1
        elif word_clean in auxiliary_verbs or word_clean in common_verbs or word_clean.endswith(('ed', 'ing')):
            counts["verbs"] += 1
        elif word_clean.endswith(('ly')):
            counts["adverbs"] += 1
        elif word_clean.endswith(('ful', 'less', 'ous', 'ive', 'able', 'ible', 'al', 'ic')):
            counts["adjectives"] += 1
        elif word_clean.endswith(('tion', 'sion', 'ness', 'ment', 'ity', 'er', 'or', 'ist')):
            counts["nouns"] += 1
        else:
            # Default to noun for unclassified words
            counts["nouns"] += 1
    
    return counts


def active_verb_ratio(text: str) -> float:
    """
    Calculate ratio of active verbs to total verbs.
    
    Args:
        text: Text to analyze
        
    Returns:
        Ratio of active verbs (0.0 to 1.0)
    """
    pos_dist = pos_distribution(text)
    total_verbs = pos_dist["verbs"]
    
    if total_verbs == 0:
        return 0.0
    
    # Simple heuristic: count words that are likely active verbs
    words = text.lower().split()
    auxiliary_verbs = {"am", "is", "are", "was", "were", "be", "being", "been", "have", "has", "had"}
    
    active_verbs = 0
    for word in words:
        word_clean = re.sub(r'[^\w]', '', word)
        if word_clean and word_clean not in auxiliary_verbs and (word_clean.endswith('ed') or word_clean.endswith('ing') or word_clean in {"go", "come", "take", "make", "get", "say", "see", "know", "think", "look", "want", "give", "use", "find", "tell", "ask", "work", "seem", "feel", "try", "leave", "call"}):
            active_verbs += 1
    
    return min(active_verbs / total_verbs, 1.0)


def report(text: str, metrics_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive metrics report with target comparison.
    
    Args:
        text: Text to analyze
        metrics_cfg: Configuration with target values
        
    Returns:
        Dictionary with metrics, targets, and status
    """
    # Compute all metrics
    readability = compute_readability(text)
    sentence_len = avg_sentence_length(text)
    pos_dist = pos_distribution(text)
    active_ratio = active_verb_ratio(text)
    
    # Get targets from config
    targets = metrics_cfg.get("targets", {})
    
    # Calculate status for each metric
    def get_status(value: float, target_range: Dict[str, float]) -> str:
        if not target_range:
            return "unknown"
        
        min_val = target_range.get("min", float('-inf'))
        max_val = target_range.get("max", float('inf'))
        ideal = target_range.get("ideal")
        
        if min_val <= value <= max_val:
            if ideal and abs(value - ideal) <= target_range.get("tolerance", 2.0):
                return "green"
            return "yellow"
        return "red"
    
    report_data = {
        "metrics": {
            "readability": readability,
            "avg_sentence_length": sentence_len,
            "pos_distribution": pos_dist,
            "active_verb_ratio": active_ratio
        },
        "targets": targets,
        "status": {
            "flesch": get_status(readability["flesch"], targets.get("flesch", {})),
            "sentence_length": get_status(sentence_len, targets.get("sentence_length", {})),
            "active_verbs": get_status(active_ratio, targets.get("active_verb_ratio", {}))
        },
        "overall_status": "green"  # Will be calculated based on individual statuses
    }
    
    # Calculate overall status
    statuses = list(report_data["status"].values())
    if "red" in statuses:
        report_data["overall_status"] = "red"
    elif "yellow" in statuses:
        report_data["overall_status"] = "yellow"
    else:
        report_data["overall_status"] = "green"
    
    return report_data
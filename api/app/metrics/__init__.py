"""Metrics computation module."""
from .metrics import (
    compute_readability,
    avg_sentence_length,
    pos_distribution,
    active_verb_ratio,
    report
)

__all__ = [
    "compute_readability",
    "avg_sentence_length", 
    "pos_distribution",
    "active_verb_ratio",
    "report"
]
"""Metrics configuration mapper to bridge config file structure with agent expectations."""
from typing import Dict, Any
import yaml
from pathlib import Path


def load_metrics_config() -> Dict[str, Any]:
    """
    Load metrics configuration from YAML and map to flat structure.
    
    Maps nested structure like:
        readability.flesch_reading_ease
        sentence_structure.avg_sentence_length
        
    To flat structure like:
        flesch
        sentence_length
    """
    config_path = Path("configs/metrics.yaml")
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Map nested structure to flat keys expected by tone_metrics
    flat_config = {}
    
    if 'targets' in data:
        targets = data['targets']
        
        # Readability metrics
        if 'readability' in targets:
            if 'flesch_reading_ease' in targets['readability']:
                flat_config['flesch'] = targets['readability']['flesch_reading_ease']
            if 'flesch_kincaid_grade' in targets['readability']:
                flat_config['grade_level'] = targets['readability']['flesch_kincaid_grade']
        
        # Sentence structure
        if 'sentence_structure' in targets:
            if 'avg_sentence_length' in targets['sentence_structure']:
                flat_config['sentence_length'] = targets['sentence_structure']['avg_sentence_length']
        
        # Word usage
        if 'word_usage' in targets:
            if 'avg_syllables_per_word' in targets['word_usage']:
                flat_config['syllable_density'] = targets['word_usage']['avg_syllables_per_word']
        
        # Dialogue
        if 'dialogue' in targets:
            if 'dialogue_percentage' in targets['dialogue']:
                flat_config['dialogue_ratio'] = targets['dialogue']['dialogue_percentage']
    
    return flat_config


def map_metrics_results(flat_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map flat metrics results back to nested structure for reports.
    
    Maps flat structure like:
        flesch: 65.0
        sentence_length: 15.5
        
    To nested structure like:
        readability:
            flesch_reading_ease: 65.0
        sentence_structure:
            avg_sentence_length: 15.5
    """
    nested = {
        'readability': {},
        'sentence_structure': {},
        'word_usage': {},
        'dialogue': {}
    }
    
    # Map flat keys back to nested structure
    mapping = {
        'flesch': ('readability', 'flesch_reading_ease'),
        'grade_level': ('readability', 'flesch_kincaid_grade'),
        'sentence_length': ('sentence_structure', 'avg_sentence_length'),
        'syllable_density': ('word_usage', 'avg_syllables_per_word'),
        'dialogue_ratio': ('dialogue', 'dialogue_percentage')
    }
    
    for flat_key, value in flat_results.items():
        if flat_key in mapping:
            category, nested_key = mapping[flat_key]
            nested[category][nested_key] = value
    
    return nested
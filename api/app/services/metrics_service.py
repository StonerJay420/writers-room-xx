"""Text metrics calculation service."""
import textstat
from typing import Dict, Any, List, Optional
import re
import json
from dataclasses import dataclass, asdict


@dataclass
class TextMetrics:
    """Container for text metrics."""
    # Readability scores
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float
    smog_index: float
    coleman_liau_index: float
    automated_readability_index: float
    
    # Text statistics
    word_count: int
    sentence_count: int
    syllable_count: int
    lexicon_count: int
    avg_words_per_sentence: float
    avg_syllables_per_word: float
    
    # Content analysis
    dialogue_proportion: float
    active_voice_ratio: float
    adverb_density: float
    passive_sentences: int
    
    # Complexity
    complex_word_count: int
    long_sentence_count: int
    unique_words: int
    vocabulary_richness: float


class MetricsService:
    """Service for calculating text metrics and analysis."""
    
    def __init__(self):
        # Load metrics configuration
        self.load_config()
    
    def load_config(self):
        """Load metrics configuration from YAML file."""
        try:
            import yaml
            with open("config/metrics.yaml", "r") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            # Default configuration
            self.config = {
                "targets": {
                    "flesch_reading_ease": {"min": 50, "max": 70},
                    "flesch_kincaid_grade": {"min": 7, "max": 12},
                    "avg_words_per_sentence": {"min": 12, "max": 20},
                    "dialogue_proportion": {"min": 0.3, "max": 0.6},
                    "active_voice_ratio": {"min": 0.7, "max": 1.0}
                },
                "weights": {
                    "readability": 0.3,
                    "engagement": 0.3,
                    "clarity": 0.2,
                    "variety": 0.2
                },
                "thresholds": {
                    "complex_word_length": 3,
                    "long_sentence_words": 25,
                    "min_paragraph_sentences": 3
                }
            }
    
    def calculate_metrics(self, text: str) -> TextMetrics:
        """Calculate comprehensive text metrics."""
        
        # Basic readability scores
        flesch_reading_ease = textstat.flesch_reading_ease(text)
        flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
        gunning_fog = textstat.gunning_fog(text)
        smog_index = textstat.smog_index(text)
        coleman_liau = textstat.coleman_liau_index(text)
        ari = textstat.automated_readability_index(text)
        
        # Text statistics
        word_count = textstat.lexicon_count(text, removepunct=True)
        sentence_count = textstat.sentence_count(text)
        syllable_count = textstat.syllable_count(text)
        lexicon_count = textstat.lexicon_count(text)
        
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        avg_syllables_per_word = syllable_count / max(word_count, 1)
        
        # Content analysis
        dialogue_proportion = self._calculate_dialogue_proportion(text)
        active_voice_ratio = self._estimate_active_voice_ratio(text)
        adverb_density = self._calculate_adverb_density(text)
        passive_sentences = self._count_passive_sentences(text)
        
        # Complexity
        complex_word_count = self._count_complex_words(text)
        long_sentence_count = self._count_long_sentences(text)
        unique_words = len(set(text.lower().split()))
        vocabulary_richness = unique_words / max(word_count, 1)
        
        return TextMetrics(
            flesch_reading_ease=flesch_reading_ease,
            flesch_kincaid_grade=flesch_kincaid_grade,
            gunning_fog=gunning_fog,
            smog_index=smog_index,
            coleman_liau_index=coleman_liau,
            automated_readability_index=ari,
            word_count=word_count,
            sentence_count=sentence_count,
            syllable_count=syllable_count,
            lexicon_count=lexicon_count,
            avg_words_per_sentence=avg_words_per_sentence,
            avg_syllables_per_word=avg_syllables_per_word,
            dialogue_proportion=dialogue_proportion,
            active_voice_ratio=active_voice_ratio,
            adverb_density=adverb_density,
            passive_sentences=passive_sentences,
            complex_word_count=complex_word_count,
            long_sentence_count=long_sentence_count,
            unique_words=unique_words,
            vocabulary_richness=vocabulary_richness
        )
    
    def _calculate_dialogue_proportion(self, text: str) -> float:
        """Calculate proportion of text that is dialogue."""
        # Find text within quotes
        dialogue_pattern = r'"[^"]*"'
        dialogue_matches = re.findall(dialogue_pattern, text)
        dialogue_text = " ".join(dialogue_matches)
        
        dialogue_words = len(dialogue_text.split())
        total_words = len(text.split())
        
        return dialogue_words / max(total_words, 1)
    
    def _estimate_active_voice_ratio(self, text: str) -> float:
        """Estimate ratio of active voice sentences."""
        # Simple heuristic: look for passive voice indicators
        passive_indicators = [
            r'\b(was|were|been|being|is|are|am)\s+\w+ed\b',
            r'\b(was|were|been|being|is|are|am)\s+\w+en\b',
            r'\bby\s+\w+\s+(was|were|is|are)',
        ]
        
        sentences = text.split('.')
        passive_count = 0
        
        for sentence in sentences:
            for pattern in passive_indicators:
                if re.search(pattern, sentence, re.IGNORECASE):
                    passive_count += 1
                    break
        
        active_count = len(sentences) - passive_count
        return active_count / max(len(sentences), 1)
    
    def _calculate_adverb_density(self, text: str) -> float:
        """Calculate density of adverbs in text."""
        # Simple heuristic: words ending in 'ly'
        adverb_pattern = r'\b\w+ly\b'
        adverbs = re.findall(adverb_pattern, text, re.IGNORECASE)
        
        word_count = len(text.split())
        return len(adverbs) / max(word_count, 1)
    
    def _count_passive_sentences(self, text: str) -> int:
        """Count number of passive voice sentences."""
        passive_patterns = [
            r'\b(was|were|been|being|is|are|am)\s+\w+ed\b',
            r'\b(was|were|been|being|is|are|am)\s+\w+en\b',
        ]
        
        sentences = text.split('.')
        passive_count = 0
        
        for sentence in sentences:
            for pattern in passive_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    passive_count += 1
                    break
        
        return passive_count
    
    def _count_complex_words(self, text: str) -> int:
        """Count words with 3+ syllables."""
        words = text.split()
        complex_count = 0
        
        for word in words:
            # Remove punctuation
            word = re.sub(r'[^\w]', '', word)
            if textstat.syllable_count(word) >= self.config["thresholds"]["complex_word_length"]:
                complex_count += 1
        
        return complex_count
    
    def _count_long_sentences(self, text: str) -> int:
        """Count sentences with 25+ words."""
        sentences = text.split('.')
        long_count = 0
        threshold = self.config["thresholds"]["long_sentence_words"]
        
        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count >= threshold:
                long_count += 1
        
        return long_count
    
    def compare_metrics(
        self,
        original_metrics: TextMetrics,
        revised_metrics: TextMetrics
    ) -> Dict[str, Any]:
        """Compare two sets of metrics and calculate improvements."""
        
        original_dict = asdict(original_metrics)
        revised_dict = asdict(revised_metrics)
        
        comparison = {}
        improvements = 0
        regressions = 0
        
        for key in original_dict:
            original_val = original_dict[key]
            revised_val = revised_dict[key]
            
            if isinstance(original_val, (int, float)):
                diff = revised_val - original_val
                pct_change = (diff / max(abs(original_val), 1)) * 100
                
                comparison[key] = {
                    "original": original_val,
                    "revised": revised_val,
                    "difference": diff,
                    "percent_change": pct_change
                }
                
                # Check against targets if available
                if key in self.config.get("targets", {}):
                    target = self.config["targets"][key]
                    
                    # Check if revised is closer to target range
                    original_distance = self._distance_from_range(original_val, target)
                    revised_distance = self._distance_from_range(revised_val, target)
                    
                    if revised_distance < original_distance:
                        improvements += 1
                        comparison[key]["improved"] = True
                    elif revised_distance > original_distance:
                        regressions += 1
                        comparison[key]["improved"] = False
        
        return {
            "comparison": comparison,
            "improvements": improvements,
            "regressions": regressions,
            "overall_score": self._calculate_overall_score(revised_metrics)
        }
    
    def _distance_from_range(self, value: float, target: Dict[str, float]) -> float:
        """Calculate distance from target range."""
        min_val = target.get("min", float('-inf'))
        max_val = target.get("max", float('inf'))
        
        if value < min_val:
            return min_val - value
        elif value > max_val:
            return value - max_val
        else:
            return 0
    
    def _calculate_overall_score(self, metrics: TextMetrics) -> float:
        """Calculate overall quality score based on metrics."""
        
        score = 0
        weights = self.config.get("weights", {})
        
        # Readability component
        readability_score = 0
        if 50 <= metrics.flesch_reading_ease <= 70:
            readability_score += 0.5
        if 7 <= metrics.flesch_kincaid_grade <= 12:
            readability_score += 0.5
        score += readability_score * weights.get("readability", 0.25)
        
        # Engagement component (dialogue, variety)
        engagement_score = 0
        if 0.3 <= metrics.dialogue_proportion <= 0.6:
            engagement_score += 0.5
        if metrics.vocabulary_richness >= 0.4:
            engagement_score += 0.5
        score += engagement_score * weights.get("engagement", 0.25)
        
        # Clarity component (active voice, sentence length)
        clarity_score = 0
        if metrics.active_voice_ratio >= 0.7:
            clarity_score += 0.5
        if 12 <= metrics.avg_words_per_sentence <= 20:
            clarity_score += 0.5
        score += clarity_score * weights.get("clarity", 0.25)
        
        # Variety component (vocabulary richness, sentence variety)
        variety_score = metrics.vocabulary_richness
        score += variety_score * weights.get("variety", 0.25)
        
        return min(max(score, 0), 1)
    
    def generate_feedback(self, metrics: TextMetrics) -> List[str]:
        """Generate actionable feedback based on metrics."""
        
        feedback = []
        
        # Readability feedback
        if metrics.flesch_reading_ease < 50:
            feedback.append("Consider simplifying language - readability score is low")
        elif metrics.flesch_reading_ease > 70:
            feedback.append("Text may be too simple - consider more sophisticated language")
        
        # Sentence length feedback
        if metrics.avg_words_per_sentence > 25:
            feedback.append("Sentences are quite long - consider breaking them up")
        elif metrics.avg_words_per_sentence < 10:
            feedback.append("Sentences are very short - consider combining some")
        
        # Active voice feedback
        if metrics.active_voice_ratio < 0.7:
            feedback.append(f"High passive voice usage ({metrics.passive_sentences} sentences) - consider more active constructions")
        
        # Dialogue feedback
        if metrics.dialogue_proportion < 0.2:
            feedback.append("Very little dialogue - consider adding character interactions")
        elif metrics.dialogue_proportion > 0.7:
            feedback.append("Heavy dialogue - consider adding more narrative description")
        
        # Adverb feedback
        if metrics.adverb_density > 0.05:
            feedback.append("High adverb density - consider stronger verbs instead")
        
        # Vocabulary feedback
        if metrics.vocabulary_richness < 0.3:
            feedback.append("Repetitive vocabulary - consider more word variety")
        
        return feedback


# Global metrics service instance
metrics_service = MetricsService()
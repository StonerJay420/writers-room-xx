import textstat
import re
from typing import Dict, Any

class MetricsService:
    def __init__(self):
        self.targets = {
            "flesch_reading_ease": {"target": 80, "min": 75, "max": 88},
            "avg_sentence_length": {"target": 13, "min": 9.7, "max": 15.6},
            "active_voice_ratio": {"target": 0.98, "min": 0.95, "max": 0.99},
            "dialogue_proportion": {"target": 0.42, "min": 0.09, "max": 0.76}
        }
    
    def calculate_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate basic text metrics"""
        if not text.strip():
            return {"error": "Empty text provided"}
        
        try:
            metrics = {}
            
            # Basic readability
            metrics["flesch_reading_ease"] = textstat.flesch_reading_ease(text)
            metrics["flesch_kincaid_grade"] = textstat.flesch_kincaid_grade(text)
            
            # Sentence analysis
            sentences = textstat.sentence_count(text)
            words = textstat.lexicon_count(text, removepunct=True)
            metrics["sentence_count"] = sentences
            metrics["word_count"] = words
            metrics["avg_sentence_length"] = words / sentences if sentences > 0 else 0
            
            # Syllable and complexity
            metrics["syllable_count"] = textstat.syllable_count(text, lang='en_US')
            metrics["avg_syllables_per_word"] = metrics["syllable_count"] / words if words > 0 else 0
            
            # Dialogue analysis
            dialogue_ratio = self._calculate_dialogue_ratio(text)
            metrics["dialogue_proportion"] = dialogue_ratio
            
            # Active voice estimation (simplified)
            active_ratio = self._estimate_active_voice_ratio(text)
            metrics["active_voice_ratio"] = active_ratio
            
            # Add target comparisons
            metrics["target_analysis"] = self._analyze_against_targets(metrics)
            
            return metrics
            
        except Exception as e:
            return {"error": f"Metrics calculation failed: {str(e)}"}
    
    def _calculate_dialogue_ratio(self, text: str) -> float:
        """Estimate dialogue proportion in text"""
        lines = text.split('\n')
        dialogue_lines = 0
        total_lines = 0
        
        for line in lines:
            line = line.strip()
            if line:
                total_lines += 1
                # Simple dialogue detection (lines with quotes)
                if '"' in line or "'" in line:
                    dialogue_lines += 1
        
        return dialogue_lines / total_lines if total_lines > 0 else 0
    
    def _estimate_active_voice_ratio(self, text: str) -> float:
        """Estimate active voice ratio (simplified)"""
        sentences = re.split(r'[.!?]+', text)
        active_count = 0
        total_sentences = 0
        
        passive_indicators = [
            r'\bwas\s+\w+ed\b',
            r'\bwere\s+\w+ed\b',
            r'\bbeing\s+\w+ed\b',
            r'\bbeen\s+\w+ed\b'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 5:  # Skip very short fragments
                total_sentences += 1
                
                # Check for passive voice indicators
                is_passive = any(re.search(pattern, sentence, re.IGNORECASE) 
                               for pattern in passive_indicators)
                
                if not is_passive:
                    active_count += 1
        
        return active_count / total_sentences if total_sentences > 0 else 1.0
    
    def _analyze_against_targets(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare metrics against targets"""
        analysis = {}
        
        for metric_name, target_info in self.targets.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                target = target_info["target"]
                min_val = target_info["min"]
                max_val = target_info["max"]
                
                if min_val <= value <= max_val:
                    status = "good"
                elif abs(value - target) <= abs(max_val - min_val) * 0.2:
                    status = "okay"
                else:
                    status = "needs_improvement"
                
                analysis[metric_name] = {
                    "value": value,
                    "target": target,
                    "status": status,
                    "deviation": value - target
                }
        
        return analysis

metrics_service = MetricsService()

"""Tone & Metrics agent for text analysis as specified in Prompt 15."""
import json
from typing import Dict, Any, List, Optional
import logging
import textstat

from .base import Agent
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MetricScore(BaseModel):
    """Individual metric with score and assessment."""
    name: str
    score: float
    target_min: Optional[float] = None
    target_max: Optional[float] = None
    status: str  # "within_target", "above_target", "below_target"
    recommendation: str


class ToneMetricsResult(BaseModel):
    """Schema for tone & metrics agent output."""
    metrics_before: Dict[str, MetricScore]
    metrics_after: Optional[Dict[str, MetricScore]] = None  # Only if comparing texts
    overall_assessment: str
    recommendations: List[str]
    readability_grade: str
    tone_analysis: Dict[str, Any]


def run_tone_metrics(
    scene_text: str,
    edited_text: Optional[str] = None,
    targets: Optional[Dict[str, Dict[str, float]]] = None,
    model: str = "anthropic/claude-3-haiku"
) -> Dict[str, Any]:
    """
    Run tone & metrics analysis with consistent numerical analysis.
    
    Args:
        scene_text: Original scene text to analyze
        edited_text: Optional edited text for before/after comparison
        targets: Target metrics configuration
        model: LLM model to use (temperature=0.1 for consistency)
        
    Returns:
        Dictionary with metrics analysis and recommendations
    """
    try:
        targets = targets or {}
        
        # Analyze original text metrics
        metrics_before = _compute_text_metrics(scene_text, targets)
        
        # Analyze edited text metrics if provided
        metrics_after = None
        if edited_text:
            metrics_after = _compute_text_metrics(edited_text, targets)
        
        # Generate overall assessment
        overall_assessment = _generate_overall_assessment(metrics_before, metrics_after)
        
        # Generate recommendations
        recommendations = _generate_recommendations(metrics_before, metrics_after, targets)
        
        # Determine readability grade
        readability_grade = _determine_readability_grade(scene_text)
        
        # Analyze tone characteristics
        tone_analysis = _analyze_tone(scene_text)
        
        result = ToneMetricsResult(
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            overall_assessment=overall_assessment,
            recommendations=recommendations,
            readability_grade=readability_grade,
            tone_analysis=tone_analysis
        )
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Tone & metrics analysis failed: {str(e)}")
        return {
            "metrics_before": {},
            "metrics_after": None,
            "overall_assessment": "Analysis failed due to error",
            "recommendations": ["Review input text for analysis"],
            "readability_grade": "Unknown",
            "tone_analysis": {},
            "error": str(e)
        }


def _compute_text_metrics(text: str, targets: Dict[str, Dict[str, float]]) -> Dict[str, MetricScore]:
    """Compute comprehensive text metrics using textstat."""
    if not text.strip():
        return {}
    
    metrics = {}
    
    # Flesch Reading Ease
    try:
        flesch_score = float(textstat.flesch_reading_ease(text) or 0)
    except:
        flesch_score = 0.0
    flesch_target = targets.get("flesch", {})
    metrics["flesch_reading_ease"] = MetricScore(
        name="Flesch Reading Ease",
        score=flesch_score,
        target_min=flesch_target.get("min", 60.0),
        target_max=flesch_target.get("max", 80.0),
        status=_assess_target_compliance(flesch_score, flesch_target.get("min", 60.0), flesch_target.get("max", 80.0)),
        recommendation=_get_flesch_recommendation(flesch_score, flesch_target)
    )
    
    # Flesch-Kincaid Grade Level  
    try:
        fk_grade = float(textstat.flesch_kincaid_grade(text) or 0)
    except:
        fk_grade = 0.0
    fk_target = targets.get("grade_level", {})
    metrics["flesch_kincaid_grade"] = MetricScore(
        name="Flesch-Kincaid Grade",
        score=fk_grade,
        target_min=fk_target.get("min", 6.0),
        target_max=fk_target.get("max", 10.0),
        status=_assess_target_compliance(fk_grade, fk_target.get("min", 6.0), fk_target.get("max", 10.0)),
        recommendation=_get_grade_recommendation(fk_grade, fk_target)
    )
    
    # Average Sentence Length
    try:
        sentences = int(textstat.sentence_count(text) or 1)
        words = int(textstat.lexicon_count(text, removepunct=True) or 0)
    except:
        sentences = 1
        words = len(text.split())
    avg_sentence_length = words / sentences if sentences > 0 else 0
    sentence_target = targets.get("sentence_length", {})
    metrics["avg_sentence_length"] = MetricScore(
        name="Average Sentence Length",
        score=avg_sentence_length,
        target_min=sentence_target.get("min", 15.0),
        target_max=sentence_target.get("max", 25.0),
        status=_assess_target_compliance(avg_sentence_length, sentence_target.get("min", 15.0), sentence_target.get("max", 25.0)),
        recommendation=_get_sentence_length_recommendation(avg_sentence_length, sentence_target)
    )
    
    # Syllable Count per Word
    try:
        syllables = int(textstat.syllable_count(text) or 0)
    except:
        syllables = words * 1.5  # Estimate
    syllables_per_word = syllables / words if words > 0 else 0
    syllable_target = targets.get("syllable_density", {})
    metrics["syllables_per_word"] = MetricScore(
        name="Syllables per Word", 
        score=syllables_per_word,
        target_min=syllable_target.get("min", 1.3),
        target_max=syllable_target.get("max", 1.7),
        status=_assess_target_compliance(syllables_per_word, syllable_target.get("min", 1.3), syllable_target.get("max", 1.7)),
        recommendation=_get_syllable_recommendation(syllables_per_word, syllable_target)
    )
    
    # Dialogue Ratio
    dialogue_ratio = _calculate_dialogue_ratio(text)
    dialogue_target = targets.get("dialogue_ratio", {})
    metrics["dialogue_ratio"] = MetricScore(
        name="Dialogue Ratio",
        score=dialogue_ratio,
        target_min=dialogue_target.get("min", 0.2),
        target_max=dialogue_target.get("max", 0.6),
        status=_assess_target_compliance(dialogue_ratio, dialogue_target.get("min", 0.2), dialogue_target.get("max", 0.6)),
        recommendation=_get_dialogue_recommendation(dialogue_ratio, dialogue_target)
    )
    
    return metrics


def _assess_target_compliance(score: float, target_min: float, target_max: float) -> str:
    """Assess if score falls within target range."""
    if target_min <= score <= target_max:
        return "within_target"
    elif score < target_min:
        return "below_target"
    else:
        return "above_target"


def _get_flesch_recommendation(score: float, target: Dict[str, float]) -> str:
    """Generate recommendation for Flesch Reading Ease score."""
    target_min = target.get("min", 60.0)
    target_max = target.get("max", 80.0)
    
    if score < target_min:
        return "Text is too difficult. Shorten sentences and use simpler words."
    elif score > target_max:
        return "Text may be too simple. Consider more varied vocabulary and sentence structure."
    else:
        return "Reading ease is within target range."


def _get_grade_recommendation(score: float, target: Dict[str, float]) -> str:
    """Generate recommendation for grade level."""
    target_min = target.get("min", 6.0)
    target_max = target.get("max", 10.0)
    
    if score < target_min:
        return "Text is below target complexity. Consider more sophisticated language."
    elif score > target_max:
        return "Text is above target complexity. Simplify sentence structure and vocabulary."
    else:
        return "Grade level is appropriate for target audience."


def _get_sentence_length_recommendation(score: float, target: Dict[str, float]) -> str:
    """Generate recommendation for sentence length."""
    target_min = target.get("min", 15.0)
    target_max = target.get("max", 25.0)
    
    if score < target_min:
        return "Sentences are too short. Combine some sentences for better flow."
    elif score > target_max:
        return "Sentences are too long. Break up complex sentences for clarity."
    else:
        return "Sentence length is well-balanced."


def _get_syllable_recommendation(score: float, target: Dict[str, float]) -> str:
    """Generate recommendation for syllable density."""
    target_min = target.get("min", 1.3)
    target_max = target.get("max", 1.7)
    
    if score < target_min:
        return "Words are too simple. Use more varied vocabulary."
    elif score > target_max:
        return "Words are too complex. Use simpler alternatives where appropriate."
    else:
        return "Word complexity is appropriate."


def _get_dialogue_recommendation(score: float, target: Dict[str, float]) -> str:
    """Generate recommendation for dialogue ratio."""
    target_min = target.get("min", 0.2)
    target_max = target.get("max", 0.6)
    
    if score < target_min:
        return "Consider adding more dialogue to bring characters to life."
    elif score > target_max:
        return "Too much dialogue. Balance with narrative description and action."
    else:
        return "Dialogue balance is appropriate for the scene."


def _calculate_dialogue_ratio(text: str) -> float:
    """Calculate the ratio of dialogue to total text."""
    import re
    
    # Count characters in dialogue (text within quotes)
    dialogue_matches = re.findall(r'"[^"]*"', text)
    dialogue_chars = sum(len(match) - 2 for match in dialogue_matches)  # Exclude quote marks
    
    total_chars = len(text.replace(' ', '').replace('\n', ''))
    
    return dialogue_chars / total_chars if total_chars > 0 else 0.0


def _generate_overall_assessment(
    metrics_before: Dict[str, MetricScore], 
    metrics_after: Optional[Dict[str, MetricScore]]
) -> str:
    """Generate overall assessment of the text metrics."""
    if not metrics_before:
        return "Unable to analyze text metrics"
    
    within_target = sum(1 for m in metrics_before.values() if m.status == "within_target")
    total_metrics = len(metrics_before)
    
    if metrics_after:
        within_target_after = sum(1 for m in metrics_after.values() if m.status == "within_target")
        if within_target_after > within_target:
            return f"Improvements made: {within_target_after}/{total_metrics} metrics now within targets (was {within_target}/{total_metrics})"
        elif within_target_after < within_target:
            return f"Regression detected: {within_target_after}/{total_metrics} metrics within targets (was {within_target}/{total_metrics})"
        else:
            return f"Metrics unchanged: {within_target}/{total_metrics} metrics within targets"
    else:
        if within_target >= total_metrics * 0.8:
            return f"Strong performance: {within_target}/{total_metrics} metrics within targets"
        elif within_target >= total_metrics * 0.5:
            return f"Mixed performance: {within_target}/{total_metrics} metrics within targets"
        else:
            return f"Needs improvement: {within_target}/{total_metrics} metrics within targets"


def _generate_recommendations(
    metrics_before: Dict[str, MetricScore],
    metrics_after: Optional[Dict[str, MetricScore]],
    targets: Dict[str, Dict[str, float]]
) -> List[str]:
    """Generate actionable recommendations based on metrics analysis."""
    recommendations = []
    
    # Focus on metrics that are out of target
    out_of_target = [m for m in metrics_before.values() if m.status != "within_target"]
    
    if not out_of_target:
        recommendations.append("All metrics are within target ranges - maintain current writing style")
        return recommendations
    
    # Prioritize the most important metrics
    for metric in out_of_target:
        if metric.name == "Flesch Reading Ease":
            recommendations.append(metric.recommendation)
        elif metric.name == "Average Sentence Length":
            recommendations.append(metric.recommendation)
        elif metric.name == "Dialogue Ratio":
            recommendations.append(metric.recommendation)
    
    # Limit to 3 most actionable recommendations
    return recommendations[:3]


def _determine_readability_grade(text: str) -> str:
    """Determine human-readable grade level assessment."""
    try:
        grade = float(textstat.flesch_kincaid_grade(text) or 0)
    except:
        grade = 10.0
    
    if grade < 6:
        return "Elementary (grades 1-5)"
    elif grade < 9:
        return "Middle school (grades 6-8)"
    elif grade < 13:
        return "High school (grades 9-12)"
    elif grade < 16:
        return "College level"
    else:
        return "Graduate level"


def _analyze_tone(text: str) -> Dict[str, Any]:
    """Analyze tone characteristics of the text."""
    try:
        word_count = int(textstat.lexicon_count(text, removepunct=True) or 0)
        sentence_count = int(textstat.sentence_count(text) or 1)
        difficult_count = int(textstat.difficult_words(text) or 0)
    except:
        word_count = len(text.split())
        sentence_count = text.count('.') + text.count('!') + text.count('?') or 1
        difficult_count = 0
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
        "complex_word_ratio": difficult_count / word_count if word_count > 0 else 0,
        "avg_words_per_sentence": word_count / sentence_count if sentence_count > 0 else 0,
        "reading_time_minutes": round(word_count / 200, 1)  # Estimate 200 words per minute
    }


class ToneMetricsAgent(Agent):
    """Tone & Metrics agent implementation."""
    
    def __init__(self):
        super().__init__(
            name="tone_metrics",
            model="anthropic/claude-3-haiku",
            tools=["analyze_metrics", "assess_readability"]
        )
    
    async def run(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the tone & metrics agent.
        
        Args:
            task: Task parameters with scene_text, edited_text
            context: Context with targets configuration
            
        Returns:
            Metrics analysis with scores and recommendations
        """
        scene_text = task.get("scene_text", "")
        edited_text = task.get("edited_text")
        targets = context.get("targets", {})
        
        result = run_tone_metrics(
            scene_text=scene_text,
            edited_text=edited_text,
            targets=targets,
            model="anthropic/claude-3-haiku"
        )
        
        self.log_result(result)
        return result
    
    def build_system_prompt(self) -> str:
        """Build system prompt for tone & metrics agent."""
        return """You are the Tone & Metrics Analyst, providing precise numerical assessment of text characteristics.

Your analysis covers:

1. READABILITY METRICS: Flesch Reading Ease, Flesch-Kincaid Grade Level
2. STRUCTURAL ANALYSIS: Sentence length, syllable density, word complexity  
3. CONTENT BALANCE: Dialogue vs narrative ratio, paragraph structure
4. TARGET COMPLIANCE: Assessment against editorial standards
5. IMPROVEMENT TRACKING: Before/after comparisons when applicable

You operate at temperature 0.1 for consistent, reliable numerical analysis.

Provide objective metrics with clear target assessments and actionable recommendations.
Focus on measurable improvements that align with editorial goals.
No text editing - analysis and guidance only."""
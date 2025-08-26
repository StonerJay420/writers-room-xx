"""Pacing Surgeon agent for narrative flow improvements as specified in Prompt 69."""
from typing import Dict, Any, List, Optional
import re
from pydantic import BaseModel


class PacingAnalysis(BaseModel):
    """Analysis of pacing issues in a scene."""
    section: str
    current_pace: str  # "slow", "medium", "fast", "variable"
    issues: List[str]
    suggestions: List[str]


class PacingSurgeonResult(BaseModel):
    """Schema for Pacing Surgeon output."""
    scene_pace_score: float
    beat_analysis: List[Dict[str, Any]]
    slow_sections: List[PacingAnalysis]
    recommendations: List[str]
    proposed_edits: Dict[str, str]
    rationale: List[str]


async def run_pacing_surgeon(
    scene_text: str,
    target_pace: str = "variable",
    edge_intensity: int = 0,
    model: str = "anthropic/claude-3-opus"
) -> Dict[str, Any]:
    """
    Run Pacing Surgeon to improve narrative flow and tension.
    
    Focuses on:
    - Scene beats and rhythm
    - Tension escalation
    - Paragraph and sentence variation
    - Action vs reflection balance
    - Micro-tension in prose
    
    Args:
        scene_text: The scene text to analyze
        target_pace: Desired pacing ("slow", "medium", "fast", "variable")
        edge_intensity: 0-3 for how aggressive to be with cuts
        model: LLM model to use
        
    Returns:
        Dictionary with pacing analysis and improvements
    """
    # Analyze current pacing
    paragraphs = scene_text.split('\n\n')
    beat_analysis = []
    slow_sections = []
    proposed_edits = {}
    
    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
            
        # Analyze paragraph characteristics
        sentences = _split_sentences(para)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        has_dialogue = bool(re.search(r'"[^"]+"', para))
        has_action = _contains_action_verbs(para)
        
        # Determine pace
        if avg_sentence_length > 25:
            pace = "slow"
        elif avg_sentence_length < 10 and has_action:
            pace = "fast"
        elif has_dialogue:
            pace = "medium"
        else:
            pace = "variable"
        
        beat = {
            "paragraph": i,
            "pace": pace,
            "avg_sentence_length": avg_sentence_length,
            "has_dialogue": has_dialogue,
            "has_action": has_action,
            "word_count": len(para.split())
        }
        beat_analysis.append(beat)
        
        # Identify slow sections
        if pace == "slow" and target_pace != "slow":
            issues = []
            suggestions = []
            
            if avg_sentence_length > 25:
                issues.append("Sentences too long")
                suggestions.append("Break into shorter sentences")
            
            if not has_action and not has_dialogue:
                issues.append("Lacks action or dialogue")
                suggestions.append("Add action beats or dialogue")
            
            if len(para.split()) > 150:
                issues.append("Paragraph too long")
                suggestions.append("Split into smaller paragraphs")
            
            slow_sections.append(PacingAnalysis(
                section=f"Paragraph {i}",
                current_pace=pace,
                issues=issues,
                suggestions=suggestions
            ))
            
            # Generate edit based on intensity
            if edge_intensity > 0:
                edited = _improve_pacing(para, target_pace, edge_intensity)
                if edited != para:
                    proposed_edits[para[:50] + "..."] = edited
    
    # Calculate overall pace score
    pace_variety = len(set(b["pace"] for b in beat_analysis))
    ideal_variety = 3 if target_pace == "variable" else 1
    pace_score = min(pace_variety / ideal_variety, 1.0)
    
    # Generate recommendations
    recommendations = []
    if len(slow_sections) > len(beat_analysis) / 2:
        recommendations.append("Scene has too many slow sections - consider cutting or adding tension")
    
    if pace_variety == 1:
        recommendations.append("Add pace variation to maintain reader interest")
    
    avg_para_length = sum(b["word_count"] for b in beat_analysis) / max(len(beat_analysis), 1)
    if avg_para_length > 100:
        recommendations.append("Consider breaking up longer paragraphs")
    
    # Build rationale
    rationale = [
        f"Analyzed {len(beat_analysis)} paragraphs for pacing",
        f"Current pace distribution: {_get_pace_distribution(beat_analysis)}",
        f"Identified {len(slow_sections)} sections needing pace improvement"
    ]
    
    result = PacingSurgeonResult(
        scene_pace_score=pace_score,
        beat_analysis=beat_analysis,
        slow_sections=slow_sections,
        recommendations=recommendations,
        proposed_edits=proposed_edits,
        rationale=rationale
    )
    
    return result.model_dump()


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitter
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def _contains_action_verbs(text: str) -> bool:
    """Check if text contains action verbs."""
    action_verbs = [
        "ran", "jumped", "grabbed", "struck", "threw", "dodged",
        "attacked", "fled", "charged", "slammed", "kicked", "punched"
    ]
    text_lower = text.lower()
    return any(verb in text_lower for verb in action_verbs)


def _improve_pacing(text: str, target_pace: str, intensity: int) -> str:
    """Improve pacing of text based on target and intensity."""
    sentences = _split_sentences(text)
    
    if target_pace == "fast" and intensity >= 1:
        # Shorten sentences for faster pace
        improved = []
        for sent in sentences:
            words = sent.split()
            if len(words) > 20:
                # Split long sentences
                mid = len(words) // 2
                improved.append(' '.join(words[:mid]) + '.')
                improved.append(' '.join(words[mid:]) + '.')
            else:
                improved.append(sent + '.')
        return ' '.join(improved)
    
    elif target_pace == "variable" and intensity >= 2:
        # Add variation
        improved = []
        for i, sent in enumerate(sentences):
            if i % 3 == 0 and len(sent.split()) > 15:
                # Make every third long sentence shorter
                words = sent.split()[:10]
                improved.append(' '.join(words) + '.')
            else:
                improved.append(sent + '.')
        return ' '.join(improved)
    
    return text


def _get_pace_distribution(beat_analysis: List[Dict]) -> str:
    """Get distribution of pacing in beats."""
    paces = [b["pace"] for b in beat_analysis]
    pace_counts = {}
    for pace in ["slow", "medium", "fast", "variable"]:
        count = paces.count(pace)
        if count > 0:
            pace_counts[pace] = count
    
    return ", ".join(f"{pace}: {count}" for pace, count in pace_counts.items())
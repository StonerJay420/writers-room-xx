"""Dialogue Demon agent for dialogue improvements as specified in Prompt 68."""
from typing import Dict, Any, List, Optional
import json
import re
from pydantic import BaseModel

from .base import Agent


class DialogueAnalysis(BaseModel):
    """Analysis of dialogue issues."""
    character_name: str
    line: str
    issues: List[str]
    suggestions: List[str]


class DialogueDemonResult(BaseModel):
    """Schema for Dialogue Demon output."""
    analysis: List[DialogueAnalysis]
    improvements: Dict[str, str]  # old_line -> new_line
    voice_consistency_score: float
    recommendations: List[str]
    rationale: List[str]


async def run_dialogue_demon(
    scene_text: str,
    character_profiles: Dict[str, Dict[str, Any]],
    edge_intensity: int = 0,
    model: str = "anthropic/claude-3-opus"
) -> Dict[str, Any]:
    """
    Run Dialogue Demon to improve character dialogue.
    
    Focuses on:
    - Character voice consistency
    - Natural speech patterns
    - Dialogue attribution
    - Subtext and tension
    - Dialect and speech quirks
    
    Args:
        scene_text: The scene text containing dialogue
        character_profiles: Character voice profiles with speech patterns
        edge_intensity: 0-3 for how bold to make changes
        model: LLM model to use
        
    Returns:
        Dictionary with dialogue improvements and analysis
    """
    # Extract dialogue from scene
    dialogue_lines = _extract_dialogue(scene_text)
    
    # Analyze each line for character voice consistency
    analysis_results = []
    improvements = {}
    
    for line_info in dialogue_lines:
        char_name = line_info.get("speaker", "Unknown")
        line = line_info.get("text", "")
        
        # Check against character profile if available
        profile = character_profiles.get(char_name, {})
        voice_tags = profile.get("voice_tags", [])
        preferred_words = profile.get("preferred_words", [])
        banned_words = profile.get("banned_words", [])
        
        issues = []
        suggestions = []
        
        # Check for banned words
        for banned in banned_words:
            if banned.lower() in line.lower():
                issues.append(f"Contains banned word: {banned}")
                suggestions.append(f"Remove or replace '{banned}'")
        
        # Check for voice consistency
        if voice_tags and not _matches_voice_tags(line, voice_tags):
            issues.append("Doesn't match character voice tags")
            suggestions.append(f"Adjust to match: {', '.join(voice_tags[:3])}")
        
        # Check dialogue attribution
        if not line_info.get("has_attribution", True):
            issues.append("Missing clear attribution")
            suggestions.append("Add dialogue tag or action beat")
        
        # Generate improved version based on edge_intensity
        if issues:
            improved = _improve_dialogue_line(
                line=line,
                character=char_name,
                profile=profile,
                edge_intensity=edge_intensity
            )
            improvements[line] = improved
            
        analysis_results.append(DialogueAnalysis(
            character_name=char_name,
            line=line,
            issues=issues,
            suggestions=suggestions
        ))
    
    # Calculate voice consistency score
    total_lines = len(dialogue_lines)
    problematic_lines = len([a for a in analysis_results if a.issues])
    voice_score = 1.0 - (problematic_lines / max(total_lines, 1))
    
    # Generate recommendations
    recommendations = []
    if voice_score < 0.7:
        recommendations.append("Consider reviewing character voice profiles")
    if any("attribution" in str(a.issues) for a in analysis_results):
        recommendations.append("Add clearer dialogue attribution with action beats")
    if edge_intensity >= 2:
        recommendations.append("Consider adding more subtext and tension")
    
    # Build rationale
    rationale = [
        f"Analyzed {total_lines} dialogue lines for character consistency",
        f"Voice consistency score: {voice_score:.1%}",
        f"Applied {len(improvements)} improvements at intensity {edge_intensity}"
    ]
    
    result = DialogueDemonResult(
        analysis=analysis_results,
        improvements=improvements,
        voice_consistency_score=voice_score,
        recommendations=recommendations,
        rationale=rationale
    )
    
    return result.model_dump()


def _extract_dialogue(text: str) -> List[Dict[str, Any]]:
    """Extract dialogue lines with speaker attribution."""
    dialogue_pattern = r'"([^"]+)"'
    lines = []
    
    for match in re.finditer(dialogue_pattern, text):
        dialogue_text = match.group(1)
        start_pos = match.start()
        
        # Look for speaker before dialogue
        before_text = text[max(0, start_pos-100):start_pos]
        speaker = _find_speaker(before_text)
        
        # Check if has attribution tag
        after_text = text[match.end():min(len(text), match.end()+50)]
        has_attribution = bool(re.search(r'(said|asked|replied|muttered|whispered)', after_text))
        
        lines.append({
            "text": dialogue_text,
            "speaker": speaker,
            "has_attribution": has_attribution,
            "position": start_pos
        })
    
    return lines


def _find_speaker(text: str) -> str:
    """Find speaker name from text before dialogue."""
    # Simple heuristic - look for capitalized names
    words = text.split()[-10:]  # Last 10 words before dialogue
    for word in reversed(words):
        if word and word[0].isupper() and len(word) > 1:
            return word.rstrip('.,;:')
    return "Unknown"


def _matches_voice_tags(line: str, tags: List[str]) -> bool:
    """Check if dialogue matches character voice tags."""
    line_lower = line.lower()
    matches = 0
    
    for tag in tags:
        tag_lower = tag.lower()
        # Check for conceptual matches (simplified)
        if "formal" in tag_lower and any(w in line_lower for w in ["shall", "perhaps", "indeed"]):
            matches += 1
        elif "casual" in tag_lower and any(w in line_lower for w in ["gonna", "yeah", "kinda"]):
            matches += 1
        elif "technical" in tag_lower and len([w for w in line.split() if len(w) > 8]) > 2:
            matches += 1
    
    return matches > 0


def _improve_dialogue_line(
    line: str,
    character: str,
    profile: Dict[str, Any],
    edge_intensity: int
) -> str:
    """Generate improved version of dialogue line."""
    improved = line
    
    # Apply character-specific improvements
    voice_tags = profile.get("voice_tags", [])
    preferred = profile.get("preferred_words", [])
    
    # Simple improvements based on intensity
    if edge_intensity == 0:
        # Safe: minor punctuation and clarity
        improved = improved.rstrip('.') + '.'
    elif edge_intensity == 1:
        # Bold: add character flavor
        if preferred and len(improved) < 100:
            improved = improved.rstrip('.') + f", {preferred[0]}."
    elif edge_intensity >= 2:
        # Red team: significant rewrites
        if "formal" in str(voice_tags).lower():
            improved = re.sub(r"\bcan't\b", "cannot", improved)
            improved = re.sub(r"\bwon't\b", "will not", improved)
        elif "casual" in str(voice_tags).lower():
            improved = re.sub(r"\bcannot\b", "can't", improved)
            improved = re.sub(r"\bwill not\b", "won't", improved)
    
    return improved
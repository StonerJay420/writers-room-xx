"""Voice Simulator agent for author style matching as specified in Prompt 73."""
from typing import Dict, Any, List, Optional
import re
from pydantic import BaseModel


class VoiceProfile(BaseModel):
    """Profile of detected voice characteristics."""
    sentence_rhythm: str  # "short", "varied", "long", "staccato"
    vocabulary_level: str  # "simple", "moderate", "complex", "literary"
    tone: str  # "formal", "casual", "poetic", "direct"
    signature_patterns: List[str]
    unique_phrases: List[str]


class VoiceSimulatorResult(BaseModel):
    """Schema for Voice Simulator output."""
    original_voice: VoiceProfile
    target_voice: Optional[VoiceProfile]
    voice_match_score: float
    adjustments_made: List[Dict[str, str]]
    rewritten_sample: Optional[str]
    consistency_analysis: Dict[str, float]
    rationale: List[str]


async def run_voice_simulator(
    scene_text: str,
    target_author_samples: Optional[List[str]] = None,
    author_name: Optional[str] = None,
    edge_intensity: int = 1,
    model: str = "anthropic/claude-3-opus"
) -> Dict[str, Any]:
    """
    Run Voice Simulator to match or enhance authorial voice.
    
    Can either:
    - Analyze and strengthen existing voice
    - Match a target author's style
    - Ensure voice consistency across scenes
    
    Args:
        scene_text: The scene text to analyze/modify
        target_author_samples: Sample texts from target author
        author_name: Name of author to emulate (if known style)
        edge_intensity: 0-3 for how much to modify voice
        model: LLM model to use
        
    Returns:
        Dictionary with voice analysis and adjustments
    """
    # Analyze original voice
    original_voice = _analyze_voice(scene_text)
    
    # If target samples provided, analyze target voice
    target_voice = None
    if target_author_samples:
        combined_target = ' '.join(target_author_samples)
        target_voice = _analyze_voice(combined_target)
    elif author_name:
        target_voice = _get_known_author_voice(author_name)
    
    # Calculate voice match score
    voice_match_score = 1.0
    if target_voice:
        voice_match_score = _calculate_voice_similarity(original_voice, target_voice)
    
    # Make adjustments based on intensity
    adjustments_made = []
    rewritten_sample = None
    
    if edge_intensity > 0 and target_voice:
        adjustments = _identify_adjustments(original_voice, target_voice, edge_intensity)
        adjustments_made = adjustments
        
        if edge_intensity >= 2:
            # Rewrite a sample paragraph
            first_para = scene_text.split('\n\n')[0] if '\n\n' in scene_text else scene_text[:500]
            rewritten_sample = _rewrite_in_voice(first_para, target_voice, edge_intensity)
    
    # Analyze consistency
    consistency_analysis = _analyze_consistency(scene_text)
    
    # Generate rationale
    rationale = [
        f"Analyzed voice characteristics: {original_voice.tone} tone with {original_voice.sentence_rhythm} rhythm",
        f"Voice match score: {voice_match_score:.1%}" if target_voice else "No target voice provided",
        f"Made {len(adjustments_made)} adjustments at intensity {edge_intensity}"
    ]
    
    result = VoiceSimulatorResult(
        original_voice=original_voice,
        target_voice=target_voice,
        voice_match_score=voice_match_score,
        adjustments_made=adjustments_made,
        rewritten_sample=rewritten_sample,
        consistency_analysis=consistency_analysis,
        rationale=rationale
    )
    
    return result.model_dump()


def _analyze_voice(text: str) -> VoiceProfile:
    """Analyze voice characteristics of text."""
    sentences = re.split(r'[.!?]+', text)
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
    
    # Determine sentence rhythm
    avg_length = sum(sentence_lengths) / max(len(sentence_lengths), 1)
    if avg_length < 10:
        rhythm = "staccato"
    elif avg_length < 15:
        rhythm = "short"
    elif avg_length < 25:
        rhythm = "varied"
    else:
        rhythm = "long"
    
    # Analyze vocabulary
    words = text.split()
    complex_words = [w for w in words if len(w) > 8]
    vocab_complexity = len(complex_words) / max(len(words), 1)
    
    if vocab_complexity < 0.05:
        vocabulary = "simple"
    elif vocab_complexity < 0.1:
        vocabulary = "moderate"
    elif vocab_complexity < 0.15:
        vocabulary = "complex"
    else:
        vocabulary = "literary"
    
    # Determine tone
    formal_markers = ["however", "therefore", "moreover", "furthermore"]
    casual_markers = ["gonna", "yeah", "okay", "stuff", "things"]
    poetic_markers = ["like", "as if", "seemed to", "whispered"]
    
    has_formal = any(marker in text.lower() for marker in formal_markers)
    has_casual = any(marker in text.lower() for marker in casual_markers)
    has_poetic = any(marker in text.lower() for marker in poetic_markers)
    
    if has_formal and not has_casual:
        tone = "formal"
    elif has_casual and not has_formal:
        tone = "casual"
    elif has_poetic:
        tone = "poetic"
    else:
        tone = "direct"
    
    # Find signature patterns
    patterns = []
    if text.count("—") > 2:
        patterns.append("Uses em-dashes frequently")
    if text.count(";") > 2:
        patterns.append("Uses semicolons")
    if text.count("...") > 1:
        patterns.append("Uses ellipses")
    
    # Find unique phrases (simplified)
    unique_phrases = []
    if "in the way that" in text:
        unique_phrases.append("in the way that")
    
    return VoiceProfile(
        sentence_rhythm=rhythm,
        vocabulary_level=vocabulary,
        tone=tone,
        signature_patterns=patterns,
        unique_phrases=unique_phrases
    )


def _get_known_author_voice(author: str) -> VoiceProfile:
    """Get voice profile for known authors."""
    known_voices = {
        "hemingway": VoiceProfile(
            sentence_rhythm="short",
            vocabulary_level="simple",
            tone="direct",
            signature_patterns=["Short sentences", "Simple words", "Repetition"],
            unique_phrases=[]
        ),
        "fitzgerald": VoiceProfile(
            sentence_rhythm="long",
            vocabulary_level="literary",
            tone="poetic",
            signature_patterns=["Elaborate metaphors", "Jazz rhythm"],
            unique_phrases=["so we beat on"]
        )
    }
    
    return known_voices.get(author.lower(), VoiceProfile(
        sentence_rhythm="varied",
        vocabulary_level="moderate",
        tone="direct",
        signature_patterns=[],
        unique_phrases=[]
    ))


def _calculate_voice_similarity(voice1: VoiceProfile, voice2: VoiceProfile) -> float:
    """Calculate similarity between two voice profiles."""
    score = 0.0
    
    if voice1.sentence_rhythm == voice2.sentence_rhythm:
        score += 0.3
    if voice1.vocabulary_level == voice2.vocabulary_level:
        score += 0.3
    if voice1.tone == voice2.tone:
        score += 0.2
    
    # Check pattern overlap
    pattern_overlap = len(set(voice1.signature_patterns) & set(voice2.signature_patterns))
    score += min(0.2, pattern_overlap * 0.1)
    
    return min(1.0, score)


def _identify_adjustments(
    original: VoiceProfile,
    target: VoiceProfile,
    intensity: int
) -> List[Dict[str, str]]:
    """Identify adjustments needed to match target voice."""
    adjustments = []
    
    if original.sentence_rhythm != target.sentence_rhythm:
        adjustments.append({
            "aspect": "sentence_rhythm",
            "from": original.sentence_rhythm,
            "to": target.sentence_rhythm,
            "action": f"Adjust sentences to {target.sentence_rhythm} rhythm"
        })
    
    if original.vocabulary_level != target.vocabulary_level and intensity >= 2:
        adjustments.append({
            "aspect": "vocabulary",
            "from": original.vocabulary_level,
            "to": target.vocabulary_level,
            "action": f"Shift vocabulary to {target.vocabulary_level} level"
        })
    
    if original.tone != target.tone and intensity >= 1:
        adjustments.append({
            "aspect": "tone",
            "from": original.tone,
            "to": target.tone,
            "action": f"Adjust tone from {original.tone} to {target.tone}"
        })
    
    return adjustments


def _rewrite_in_voice(text: str, target_voice: VoiceProfile, intensity: int) -> str:
    """Rewrite text to match target voice."""
    rewritten = text
    
    # Simple transformations based on target voice
    if target_voice.sentence_rhythm == "staccato" and intensity >= 2:
        # Break up long sentences
        rewritten = rewritten.replace(", and", ". And")
        rewritten = rewritten.replace(", but", ". But")
    
    if target_voice.tone == "formal" and intensity >= 1:
        # Make more formal
        rewritten = rewritten.replace("can't", "cannot")
        rewritten = rewritten.replace("won't", "will not")
    elif target_voice.tone == "casual" and intensity >= 1:
        # Make more casual
        rewritten = rewritten.replace("cannot", "can't")
        rewritten = rewritten.replace("will not", "won't")
    
    return rewritten


def _analyze_consistency(text: str) -> Dict[str, float]:
    """Analyze voice consistency throughout text."""
    paragraphs = text.split('\n\n')
    
    if len(paragraphs) < 2:
        return {"overall_consistency": 1.0}
    
    # Check consistency metrics
    paragraph_voices = [_analyze_voice(p) for p in paragraphs if p.strip()]
    
    # Check if rhythm stays consistent
    rhythms = [v.sentence_rhythm for v in paragraph_voices]
    rhythm_consistency = len(set(rhythms)) == 1
    
    # Check if tone stays consistent
    tones = [v.tone for v in paragraph_voices]
    tone_consistency = len(set(tones)) == 1
    
    overall_consistency = (
        (1.0 if rhythm_consistency else 0.5) +
        (1.0 if tone_consistency else 0.5)
    ) / 2
    
    return {
        "overall_consistency": overall_consistency,
        "rhythm_consistency": 1.0 if rhythm_consistency else 0.5,
        "tone_consistency": 1.0 if tone_consistency else 0.5
    }
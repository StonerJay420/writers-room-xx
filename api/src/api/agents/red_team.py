"""Red Team agent for aggressive editorial challenges as specified in Prompt 71."""
from typing import Dict, Any, List, Optional
import re
from pydantic import BaseModel


class RedTeamChallenge(BaseModel):
    """A challenge or critique from red team analysis."""
    category: str  # "logic", "consistency", "effectiveness", "originality"
    severity: str  # "minor", "moderate", "major", "critical"
    issue: str
    evidence: str
    fix: str


class RedTeamResult(BaseModel):
    """Schema for Red Team output."""
    challenges: List[RedTeamChallenge]
    weakest_elements: List[Dict[str, str]]
    cliches_found: List[str]
    logic_gaps: List[Dict[str, str]]
    aggressive_edits: Dict[str, str]
    brutality_score: float
    rationale: List[str]


async def run_red_team(
    scene_text: str,
    canon_rules: Dict[str, Any],
    edge_intensity: int = 3,  # Red team defaults to maximum intensity
    model: str = "anthropic/claude-3-opus"
) -> Dict[str, Any]:
    """
    Run Red Team agent for brutal, honest critique.
    
    Acts as hostile editor finding every weakness:
    - Logic holes and inconsistencies
    - Clichés and tired tropes
    - Weak prose and filler
    - Character inconsistencies
    - Plot conveniences
    
    Args:
        scene_text: The scene text to attack
        canon_rules: Canon/lore rules to check against
        edge_intensity: 0-3, but red team works best at 3
        model: LLM model to use
        
    Returns:
        Dictionary with brutal critique and aggressive fixes
    """
    challenges = []
    cliches_found = []
    logic_gaps = []
    aggressive_edits = {}
    
    # Hunt for clichés
    cliche_patterns = [
        r'heart (was )?pounding',
        r'breath caught',
        r'shivers? down (his|her|their) spine',
        r'time seemed to (stop|slow)',
        r'could have heard a pin drop',
        r'deafening silence',
        r'storm was brewing',
        r'calm before the storm',
        r'piercing (blue|green) eyes',
        r'raven(-| )black hair'
    ]
    
    for pattern in cliche_patterns:
        matches = re.finditer(pattern, scene_text, re.IGNORECASE)
        for match in matches:
            cliches_found.append(match.group())
            challenges.append(RedTeamChallenge(
                category="originality",
                severity="moderate",
                issue="Cliché detected",
                evidence=match.group(),
                fix="Replace with fresh, specific imagery"
            ))
    
    # Hunt for weak words and filler
    weak_words = [
        (r'\b(very|really|quite|rather|somewhat)\b', "Weak intensifier"),
        (r'\b(thing|stuff|something)\b', "Vague noun"),
        (r'\b(good|bad|nice|great)\b', "Generic adjective"),
        (r'\b(suddenly|then|just)\b', "Filter word"),
        (r'\b(started to|began to)\b', "Unnecessary phrasal verb")
    ]
    
    for pattern, issue_type in weak_words:
        matches = re.finditer(pattern, scene_text, re.IGNORECASE)
        for match in matches:
            challenges.append(RedTeamChallenge(
                category="effectiveness",
                severity="minor",
                issue=issue_type,
                evidence=match.group(),
                fix="Cut or replace with stronger word"
            ))
    
    # Analyze paragraph structure for weaknesses
    paragraphs = scene_text.split('\n\n')
    weakest_elements = []
    
    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
            
        # Check for weak opening
        first_sentence = para.split('.')[0] if '.' in para else para
        if any(first_sentence.lower().startswith(w) for w in ['there was', 'there were', 'it was']):
            weakest_elements.append({
                "element": f"Paragraph {i} opening",
                "issue": "Weak, passive opening",
                "current": first_sentence[:50],
                "suggestion": "Start with action or specific detail"
            })
        
        # Check for repetitive sentence structure
        sentences = re.split(r'[.!?]+', para)
        if len(sentences) > 3:
            starts = [s.split()[0].lower() if s.split() else '' for s in sentences[:4]]
            if len(set(starts)) == 1 and starts[0]:
                weakest_elements.append({
                    "element": f"Paragraph {i} structure",
                    "issue": "Repetitive sentence beginnings",
                    "current": f"All start with '{starts[0]}'",
                    "suggestion": "Vary sentence structure"
                })
    
    # Check for logic gaps (simplified)
    if "but" in scene_text and "because" not in scene_text:
        logic_gaps.append({
            "type": "causation",
            "issue": "Contradiction without explanation",
            "suggestion": "Add causal connection or motivation"
        })
    
    # Generate aggressive edits based on intensity
    if edge_intensity >= 2:
        # Find and mark sections for deletion
        for para in paragraphs[:3]:
            if len(para) > 200 and not re.search(r'"[^"]+"', para):
                aggressive_edits[para[:50] + "..."] = "[DELETE - Excessive exposition, show don't tell]"
    
    if edge_intensity == 3:
        # Maximum brutality - suggest major cuts
        word_count = len(scene_text.split())
        if word_count > 1000:
            aggressive_edits["OVERALL"] = f"Cut 30% ({int(word_count * 0.3)} words) - too bloated"
    
    # Calculate brutality score (how harsh the critique is)
    brutality_score = min(1.0, (
        len(challenges) * 0.05 +
        len(cliches_found) * 0.1 +
        len(weakest_elements) * 0.1 +
        len(logic_gaps) * 0.2 +
        (edge_intensity / 3)
    ) / 2)
    
    # Build rationale
    rationale = [
        f"Applied maximum scrutiny at intensity {edge_intensity}",
        f"Found {len(challenges)} issues requiring attention",
        f"Identified {len(cliches_found)} clichés and {len(weakest_elements)} weak elements"
    ]
    
    result = RedTeamResult(
        challenges=challenges,
        weakest_elements=weakest_elements,
        cliches_found=cliches_found,
        logic_gaps=logic_gaps,
        aggressive_edits=aggressive_edits,
        brutality_score=brutality_score,
        rationale=rationale
    )
    
    return result.model_dump()
"""Plot Twister agent for narrative complexity as specified in Prompt 70."""
from typing import Dict, Any, List, Optional
import re
from pydantic import BaseModel


class PlotElement(BaseModel):
    """A plot element that could be twisted or enhanced."""
    element_type: str  # "reveal", "reversal", "complication", "foreshadowing"
    current_text: str
    enhancement: str
    impact_level: str  # "subtle", "moderate", "dramatic"


class PlotTwisterResult(BaseModel):
    """Schema for Plot Twister output."""
    plot_elements: List[PlotElement]
    foreshadowing_opportunities: List[Dict[str, str]]
    tension_points: List[Dict[str, Any]]
    proposed_twists: List[Dict[str, str]]
    complexity_score: float
    rationale: List[str]


async def run_plot_twister(
    scene_text: str,
    scene_context: Dict[str, Any],
    edge_intensity: int = 0,
    model: str = "anthropic/claude-3-opus"
) -> Dict[str, Any]:
    """
    Run Plot Twister to add narrative complexity and intrigue.
    
    Focuses on:
    - Plot reversals and reveals
    - Foreshadowing placement
    - Tension escalation
    - Subplot weaving
    - Misdirection and red herrings
    
    Args:
        scene_text: The scene text to enhance
        scene_context: Context about plot threads and story arc
        edge_intensity: 0-3 for how dramatic to make twists
        model: LLM model to use
        
    Returns:
        Dictionary with plot enhancements and twists
    """
    # Identify existing plot elements
    plot_elements = []
    
    # Look for potential reveal moments
    reveal_patterns = [
        r'realized that',
        r'discovered',
        r'the truth was',
        r'suddenly understood',
        r'it became clear'
    ]
    
    for pattern in reveal_patterns:
        matches = re.finditer(pattern, scene_text, re.IGNORECASE)
        for match in matches:
            start = max(0, match.start() - 50)
            end = min(len(scene_text), match.end() + 100)
            context = scene_text[start:end]
            
            element = PlotElement(
                element_type="reveal",
                current_text=context,
                enhancement=_enhance_reveal(context, edge_intensity),
                impact_level=_get_impact_level(edge_intensity)
            )
            plot_elements.append(element)
    
    # Identify foreshadowing opportunities
    foreshadowing_ops = []
    
    # Look for descriptive passages that could hint at future events
    paragraphs = scene_text.split('\n\n')
    for i, para in enumerate(paragraphs[:3]):  # Focus on early paragraphs
        if len(para) > 100 and not re.search(r'"[^"]+"', para):  # Non-dialogue
            foreshadowing_ops.append({
                "location": f"Paragraph {i}",
                "suggestion": _generate_foreshadowing(para, edge_intensity),
                "subtlety": "high" if edge_intensity == 0 else "medium" if edge_intensity == 1 else "low"
            })
    
    # Identify tension points
    tension_points = []
    tension_words = ["but", "however", "suddenly", "without warning", "unexpected"]
    
    for word in tension_words:
        count = scene_text.lower().count(word)
        if count > 0:
            tension_points.append({
                "trigger": word,
                "frequency": count,
                "effectiveness": "high" if count <= 2 else "overused"
            })
    
    # Generate plot twist proposals based on intensity
    proposed_twists = []
    
    if edge_intensity >= 1:
        proposed_twists.append({
            "type": "character_reversal",
            "description": "Reveal hidden motivation for key character",
            "implementation": "Add subtle contradiction in dialogue or action"
        })
    
    if edge_intensity >= 2:
        proposed_twists.append({
            "type": "false_assumption",
            "description": "Undermine reader's assumption about scene",
            "implementation": "Plant evidence that things aren't as they seem"
        })
        
    if edge_intensity >= 3:
        proposed_twists.append({
            "type": "major_revelation",
            "description": "Completely reframe the scene's meaning",
            "implementation": "Add game-changing reveal or reversal"
        })
    
    # Calculate complexity score
    complexity_factors = [
        len(plot_elements) > 0,
        len(tension_points) > 2,
        len(foreshadowing_ops) > 0,
        bool(re.search(r'(but|however|yet|although)', scene_text)),
        len(proposed_twists) > 0
    ]
    complexity_score = sum(complexity_factors) / len(complexity_factors)
    
    # Build rationale
    rationale = [
        f"Identified {len(plot_elements)} existing plot elements",
        f"Found {len(foreshadowing_ops)} foreshadowing opportunities",
        f"Proposed {len(proposed_twists)} plot enhancements at intensity {edge_intensity}"
    ]
    
    result = PlotTwisterResult(
        plot_elements=plot_elements,
        foreshadowing_opportunities=foreshadowing_ops,
        tension_points=tension_points,
        proposed_twists=proposed_twists,
        complexity_score=complexity_score,
        rationale=rationale
    )
    
    return result.model_dump()


def _enhance_reveal(text: str, intensity: int) -> str:
    """Enhance a reveal moment based on intensity."""
    if intensity == 0:
        return "Add a beat before reveal for emphasis"
    elif intensity == 1:
        return "Layer in sensory details during realization"
    elif intensity == 2:
        return "Add contradictory evidence before reveal"
    else:
        return "Complete misdirection followed by shocking reversal"


def _get_impact_level(intensity: int) -> str:
    """Get impact level based on intensity."""
    if intensity == 0:
        return "subtle"
    elif intensity <= 1:
        return "moderate"
    else:
        return "dramatic"


def _generate_foreshadowing(text: str, intensity: int) -> str:
    """Generate foreshadowing suggestion."""
    if intensity == 0:
        return "Add subtle environmental detail that gains meaning later"
    elif intensity == 1:
        return "Include character's offhand remark that proves prophetic"
    elif intensity == 2:
        return "Plant seemingly unrelated detail that becomes crucial"
    else:
        return "Hide major clue in plain sight through misdirection"
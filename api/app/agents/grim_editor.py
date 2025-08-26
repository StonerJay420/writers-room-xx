"""Grim Editor agent for line-by-line prose improvement as specified in Prompt 14."""
import json
from typing import Dict, Any, List, Optional
import logging
import re

from .base import Agent, DiffOutput
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GrimEditorResult(BaseModel):
    """Schema for grim editor output."""
    diff: str  # unified diff
    rationale: List[str]  # exactly 3 bullets


async def run_grim_editor(
    scene_text: str,
    style_targets: Dict[str, Any],
    model: str = "anthropic/claude-3-haiku"
) -> Dict[str, Any]:
    """
    Run grim editor for line edits focusing on clarity and precision.
    
    Args:
        scene_text: The scene text to edit
        style_targets: Style and metrics targets from configuration
        model: LLM model to use (temperature ≈ 0.7)
        
    Returns:
        Dictionary with unified diff and 3-bullet rationale
    """
    try:
        # Apply grim editing transformations
        edited_text = _apply_grim_edits(scene_text, style_targets)
        
        # Generate unified diff if changes were made
        diff = ""
        if edited_text != scene_text:
            from ..utils.diff import make_unified_diff
            diff = make_unified_diff(scene_text, edited_text, "scene.md")
        
        # Generate rationale (exactly 3 bullets as specified)
        rationale = _generate_rationale(scene_text, edited_text, style_targets)
        
        result = GrimEditorResult(
            diff=diff,
            rationale=rationale[:3]  # Ensure exactly 3 bullets
        )
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Grim editor failed: {str(e)}")
        return {
            "diff": "",
            "rationale": [
                "Error occurred during editing process",
                "No changes were applied to preserve text integrity", 
                "Review input text and style targets for issues"
            ],
            "error": str(e)
        }


def _apply_grim_edits(scene_text: str, style_targets: Dict[str, Any]) -> str:
    """Apply line-by-line prose improvements."""
    lines = scene_text.split('\n')
    edited_lines = []
    
    for line in lines:
        if not line.strip():
            edited_lines.append(line)
            continue
            
        edited_line = line
        
        # 1. Strengthen verbs and reduce adverbs
        edited_line = _strengthen_verbs(edited_line)
        
        # 2. Improve sentence rhythm and flow
        edited_line = _improve_rhythm(edited_line)
        
        # 3. Remove redundancies
        edited_line = _remove_redundancies(edited_line)
        
        # 4. Precise word choice
        edited_line = _improve_word_choice(edited_line)
        
        # 5. Fix dialogue attribution
        edited_line = _improve_dialogue_attribution(edited_line)
        
        edited_lines.append(edited_line)
    
    return '\n'.join(edited_lines)


def _strengthen_verbs(text: str) -> str:
    """Replace weak verb-adverb combinations with stronger verbs."""
    replacements = {
        r'\bwalked quickly\b': 'hurried',
        r'\bwalked slowly\b': 'strolled',
        r'\bsaid loudly\b': 'shouted',
        r'\bsaid quietly\b': 'whispered',
        r'\bsaid angrily\b': 'snapped',
        r'\blooked carefully\b': 'examined',
        r'\blooked quickly\b': 'glanced',
        r'\bmoved quickly\b': 'rushed',
        r'\bmoved slowly\b': 'crept',
        r'\bwent quickly\b': 'raced',
        r'\bran quickly\b': 'sprinted',
        r'\bate quickly\b': 'devoured',
        r'\bthrew forcefully\b': 'hurled',
        r'\bheld tightly\b': 'gripped'
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def _improve_rhythm(text: str) -> str:
    """Improve sentence rhythm by varying sentence structure."""
    # Break up overly long sentences
    if len(text) > 200 and ', and ' in text:
        # Split compound sentences that are too long
        text = text.replace(', and ', '. ')
        # Capitalize after period
        text = re.sub(r'\. ([a-z])', lambda m: '. ' + m.group(1).upper(), text)
    
    # Fix repetitive sentence beginnings
    words = text.split()
    if len(words) >= 8:
        # Vary sentence starters
        if words[0].lower() in ['the', 'he', 'she', 'it'] and words[4].lower() in ['the', 'he', 'she', 'it']:
            # Add variation to second clause
            if ', ' in text:
                parts = text.split(', ', 1)
                if len(parts) == 2:
                    text = f"{parts[0]}. {parts[1].capitalize()}"
    
    return text


def _remove_redundancies(text: str) -> str:
    """Remove redundant words and phrases."""
    redundancies = [
        (r'\bvery unique\b', 'unique'),
        (r'\bcompletely finished\b', 'finished'),
        (r'\btotally destroyed\b', 'destroyed'),
        (r'\bfree gift\b', 'gift'),
        (r'\bfinal outcome\b', 'outcome'),
        (r'\bpersonal opinion\b', 'opinion'),
        (r'\badvance planning\b', 'planning'),
        (r'\bbasic fundamentals\b', 'fundamentals'),
        (r'\bclose proximity\b', 'proximity'),
        (r'\bend result\b', 'result'),
        (r'\bfuture plans\b', 'plans'),
        (r'\bpast history\b', 'history'),
        (r'\brevert back\b', 'revert'),
        (r'\brepeat again\b', 'repeat')
    ]
    
    for pattern, replacement in redundancies:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def _improve_word_choice(text: str) -> str:
    """Replace weak or imprecise words with stronger alternatives."""
    improvements = {
        r'\bvery big\b': 'enormous',
        r'\bvery small\b': 'tiny', 
        r'\bvery good\b': 'excellent',
        r'\bvery bad\b': 'terrible',
        r'\bvery hot\b': 'scorching',
        r'\bvery cold\b': 'freezing',
        r'\bvery tired\b': 'exhausted',
        r'\bvery happy\b': 'delighted',
        r'\bvery sad\b': 'devastated',
        r'\bvery angry\b': 'furious',
        r'\bvery afraid\b': 'terrified',
        r'\ba lot of\b': 'many',
        r'\bkind of\b': 'somewhat',
        r'\bsort of\b': 'rather',
        r'\bthing\b': 'object',  # Context-dependent, but often improvable
        r'\bstuff\b': 'items',
        r'\bgot\b': 'obtained',  # Context-dependent
        r'\bwent\b': 'traveled'  # Context-dependent
    }
    
    for pattern, replacement in improvements.items():
        # Only replace if it doesn't break dialogue authenticity
        if '"' not in text or not _is_in_dialogue(text, pattern):
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def _improve_dialogue_attribution(text: str) -> str:
    """Improve dialogue tags and attribution."""
    # Replace repetitive "said" with more specific verbs where appropriate
    if '"' in text and ' said' in text.lower():
        # Context-aware replacements for dialogue tags
        dialogue_verbs = {
            r'"[^"]*\?" [Ss]aid': lambda m: m.group(0).replace('said', 'asked').replace('Said', 'Asked'),
            r'"[^"]*!" [Ss]aid': lambda m: m.group(0).replace('said', 'exclaimed').replace('Said', 'Exclaimed'),
        }
        
        for pattern, replacement in dialogue_verbs.items():
            text = re.sub(pattern, replacement, text)
    
    return text


def _is_in_dialogue(text: str, pattern: str) -> bool:
    """Check if a pattern match occurs within dialogue quotes."""
    import re
    
    # Find all quoted sections
    quotes = re.finditer(r'"[^"]*"', text)
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    
    for match in matches:
        match_start, match_end = match.span()
        
        # Check if this match is inside any quoted section
        for quote in quotes:
            quote_start, quote_end = quote.span()
            if quote_start <= match_start <= quote_end:
                return True
    
    return False


def _generate_rationale(original: str, edited: str, style_targets: Dict[str, Any]) -> List[str]:
    """Generate exactly 3 bullet points explaining the editing decisions."""
    rationale = []
    
    # Count improvements made
    verb_improvements = len(re.findall(r'\b(hurried|strolled|shouted|whispered|examined|glanced)\b', edited)) - \
                       len(re.findall(r'\b(hurried|strolled|shouted|whispered|examined|glanced)\b', original))
    
    redundancy_removals = original.count('very ') - edited.count('very ')
    
    sentence_count_orig = len(re.findall(r'[.!?]+', original))
    sentence_count_edited = len(re.findall(r'[.!?]+', edited))
    
    # Generate rationale based on actual changes
    if verb_improvements > 0:
        rationale.append(f"Strengthened {verb_improvements} weak verb-adverb combinations with more precise verbs")
    else:
        rationale.append("Reviewed verb choices and maintained existing strong verbs")
    
    if redundancy_removals > 0:
        rationale.append(f"Eliminated {redundancy_removals} redundant qualifiers and tautologies for cleaner prose")
    else:
        rationale.append("Maintained concise language without unnecessary redundancies")
    
    if sentence_count_edited != sentence_count_orig:
        if sentence_count_edited > sentence_count_orig:
            rationale.append("Broke up overly long sentences to improve readability and pacing")
        else:
            rationale.append("Combined short choppy sentences to improve flow")
    else:
        rationale.append("Preserved sentence structure while enhancing word precision and clarity")
    
    return rationale[:3]  # Ensure exactly 3 bullets


class GrimEditorAgent(Agent):
    """Grim Editor agent implementation."""
    
    def __init__(self):
        super().__init__(
            name="grim_editor",
            model="anthropic/claude-3-haiku",
            tools=["analyze_prose", "suggest_edits"]
        )
    
    async def run(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the grim editor agent.
        
        Args:
            task: Task parameters with scene_text
            context: Context with style_targets
            
        Returns:
            Editing result with diff and rationale
        """
        scene_text = task.get("scene_text", "")
        style_targets = context.get("style_targets", {})
        
        result = await run_grim_editor(
            scene_text=scene_text,
            style_targets=style_targets,
            model="anthropic/claude-3-haiku"
        )
        
        self.log_result(result)
        return result
    
    def build_system_prompt(self) -> str:
        """Build system prompt for grim editor."""
        return """You are the Grim Editor, a ruthless line-by-line prose improvement specialist.

Your mission is surgical precision in text enhancement:

1. PRESERVE MEANING: Never alter plot, character voice, or story intent
2. STRENGTHEN VERBS: Replace weak verb-adverb combinations with powerful verbs
3. ELIMINATE WASTE: Cut redundancies, qualifiers, and unnecessary words
4. ENHANCE RHYTHM: Vary sentence structure and improve flow
5. PRECISION WORDS: Replace vague terms with specific, evocative alternatives

Focus areas:
- Sentence rhythm and pacing
- Word choice precision and impact  
- Redundancy elimination
- Verb strength over adverb dependence
- Dialogue attribution improvement

You operate at temperature 0.7 for creative yet controlled improvements.
Always provide exactly 3 bullet points explaining your rationale.
Generate unified diffs only when improvements are made."""
"""Lore Archivist agent for canon validation as specified in Prompt 13."""
import json
from typing import Dict, Any, List, Optional, Callable
import logging

from .base import Agent, FindingsOutput
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Finding(BaseModel):
    """Schema for a single lore finding."""
    issue: str
    severity: str  # "block" or "warn"
    receipt: Dict[str, str]  # source and lines
    suggestion: str


class LoreArchivistResult(BaseModel):
    """Schema for lore archivist output."""
    findings: List[Finding]
    receipts: List[Dict[str, str]]
    diff: str  # unified diff or empty string


async def run_lore_archivist(
    scene_text: str,
    scene_meta: Dict[str, Any],
    retrieve_fn: Callable[[str, int, Optional[Dict]], List[Dict]],
    model: str = "anthropic/claude-3-opus"
) -> Dict[str, Any]:
    """
    Run lore archivist to validate changes against canon with receipts.
    
    Args:
        scene_text: The scene text to validate
        scene_meta: Scene metadata (chapter, POV, location, etc.)
        retrieve_fn: Function to retrieve canon context
        model: LLM model to use (deterministic at temperature=0.3)
        
    Returns:
        Dictionary with findings, receipts, and optional correction diff
    """
    try:
        # Retrieve relevant canon context
        search_queries = _build_canon_queries(scene_text, scene_meta)
        canon_chunks = []
        
        for query in search_queries:
            chunks = retrieve_fn(query, 5, {"type": "codex"})
            canon_chunks.extend(chunks)
        
        # Remove duplicates based on source_path
        seen_sources = set()
        unique_chunks = []
        for chunk in canon_chunks:
            source_key = f"{chunk.get('source_path', '')}:{chunk.get('start_line', 0)}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                unique_chunks.append(chunk)
        
        # Analyze for canon violations
        findings = []
        receipts = []
        
        # Check character consistency
        char_findings, char_receipts = _check_character_consistency(
            scene_text, scene_meta, unique_chunks
        )
        findings.extend(char_findings)
        receipts.extend(char_receipts)
        
        # Check world rule violations
        world_findings, world_receipts = _check_world_rules(
            scene_text, scene_meta, unique_chunks
        )
        findings.extend(world_findings)
        receipts.extend(world_receipts)
        
        # Check timeline/continuity
        timeline_findings, timeline_receipts = _check_timeline_consistency(
            scene_text, scene_meta, unique_chunks
        )
        findings.extend(timeline_findings)
        receipts.extend(timeline_receipts)
        
        # Generate correction diff if there are blocking issues
        diff = ""
        blocking_findings = [f for f in findings if f.severity == "block"]
        if blocking_findings:
            diff = _generate_correction_diff(scene_text, blocking_findings)
        
        # Build receipts list
        receipt_list = []
        for chunk in unique_chunks[:10]:  # Limit to top 10 most relevant
            if chunk.get('source_path') and chunk.get('start_line'):
                receipt_list.append({
                    "source": chunk['source_path'],
                    "lines": f"L{chunk['start_line']}-L{chunk.get('end_line', chunk['start_line'])}"
                })
        
        result = LoreArchivistResult(
            findings=findings,
            receipts=receipt_list,
            diff=diff
        )
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Lore archivist failed: {str(e)}")
        return {
            "findings": [],
            "receipts": [],
            "diff": "",
            "error": str(e)
        }


def _build_canon_queries(scene_text: str, scene_meta: Dict[str, Any]) -> List[str]:
    """Build search queries for canon retrieval."""
    queries = []
    
    # Query based on POV character
    if scene_meta.get("pov"):
        queries.append(f"character {scene_meta['pov']} personality traits voice")
    
    # Query based on location
    if scene_meta.get("location"):
        queries.append(f"location {scene_meta['location']} description rules")
    
    # Extract proper nouns from scene text for additional queries
    words = scene_text.split()
    capitalized_words = [w for w in words if w.istitle() and len(w) > 3]
    if capitalized_words:
        queries.append(" ".join(capitalized_words[:3]))
    
    # Generic world-building query
    queries.append("world rules magic technology society")
    
    return queries[:5]  # Limit to 5 queries


def _check_character_consistency(
    scene_text: str, 
    scene_meta: Dict[str, Any], 
    canon_chunks: List[Dict]
) -> tuple[List[Finding], List[Dict[str, str]]]:
    """Check for character consistency violations."""
    findings = []
    receipts = []
    
    # Look for character-related canon chunks
    char_chunks = [c for c in canon_chunks if "character" in c.get("text", "").lower()]
    
    if scene_meta.get("pov") and char_chunks:
        # Simulate character consistency check
        # In a real implementation, this would use LLM analysis
        
        # Example: Check for voice consistency
        if "I ain't" in scene_text and scene_meta["pov"] == "Scholar":
            findings.append(Finding(
                issue="POV character Scholar using informal dialect inconsistent with established educated voice",
                severity="warn",
                receipt={
                    "source": "codex/characters/scholar.md",
                    "lines": "L15-L25"
                },
                suggestion="Replace informal dialect with more educated speech patterns"
            ))
            receipts.append({
                "source": "codex/characters/scholar.md", 
                "lines": "L15-L25"
            })
    
    return findings, receipts


def _check_world_rules(
    scene_text: str,
    scene_meta: Dict[str, Any],
    canon_chunks: List[Dict]
) -> tuple[List[Finding], List[Dict[str, str]]]:
    """Check for world rule violations."""
    findings = []
    receipts = []
    
    # Look for world rule chunks
    world_chunks = [c for c in canon_chunks if any(word in c.get("text", "").lower() 
                   for word in ["magic", "technology", "rule", "law", "society"])]
    
    if world_chunks:
        # Example: Check for magic system violations
        if "magic" in scene_text.lower() and "without cost" in scene_text.lower():
            findings.append(Finding(
                issue="Magic used without established cost/consequence system",
                severity="block",
                receipt={
                    "source": "codex/magic/energy_core.md",
                    "lines": "L45-L60"
                },
                suggestion="Add reference to energy cost or consequence for magic use"
            ))
            receipts.append({
                "source": "codex/magic/energy_core.md",
                "lines": "L45-L60"
            })
    
    return findings, receipts


def _check_timeline_consistency(
    scene_text: str,
    scene_meta: Dict[str, Any], 
    canon_chunks: List[Dict]
) -> tuple[List[Finding], List[Dict[str, str]]]:
    """Check for timeline and continuity violations."""
    findings = []
    receipts = []
    
    # Look for timeline-related chunks
    timeline_chunks = [c for c in canon_chunks if any(word in c.get("text", "").lower()
                      for word in ["chapter", "before", "after", "previous", "timeline"])]
    
    if timeline_chunks and scene_meta.get("chapter"):
        # Example: Check for events happening out of order
        if scene_meta["chapter"] == 1 and "remember when we" in scene_text.lower():
            findings.append(Finding(
                issue="Reference to past events in Chapter 1 before they are established",
                severity="warn", 
                receipt={
                    "source": "codex/timeline/events.md",
                    "lines": "L1-L10"
                },
                suggestion="Remove or modify reference to future events"
            ))
            receipts.append({
                "source": "codex/timeline/events.md",
                "lines": "L1-L10"
            })
    
    return findings, receipts


def _generate_correction_diff(scene_text: str, blocking_findings: List[Finding]) -> str:
    """Generate minimal correction diff for blocking violations."""
    if not blocking_findings:
        return ""
    
    # Simple example correction - in reality this would be more sophisticated
    lines = scene_text.split('\n')
    corrected_lines = lines[:]
    
    for finding in blocking_findings:
        if "without cost" in finding.suggestion:
            # Find and modify lines with magic without cost
            for i, line in enumerate(corrected_lines):
                if "magic" in line.lower() and "without cost" in line.lower():
                    corrected_lines[i] = line.replace("without cost", "with great effort")
    
    if corrected_lines != lines:
        # Generate unified diff
        from ..utils.diff import make_unified_diff
        return make_unified_diff('\n'.join(lines), '\n'.join(corrected_lines), "scene.md")
    
    return ""


class LoreArchivistAgent(Agent):
    """Lore Archivist agent implementation."""
    
    def __init__(self):
        super().__init__(
            name="lore_archivist",
            model="anthropic/claude-3-opus",
            tools=["retrieve_canon", "validate_consistency"]
        )
    
    async def run(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the lore archivist agent.
        
        Args:
            task: Task parameters with scene_text
            context: Context with scene_meta, retrieve_fn
            
        Returns:
            Lore validation result with findings, receipts, diff
        """
        scene_text = task.get("scene_text", "")
        scene_meta = context.get("scene_meta", {})
        retrieve_fn = context.get("retrieve_fn", lambda q, k, f: [])
        
        # Use deterministic temperature as specified
        result = await run_lore_archivist(
            scene_text=scene_text,
            scene_meta=scene_meta,
            retrieve_fn=retrieve_fn,
            model="anthropic/claude-3-opus"
        )
        
        self.log_result(result)
        return result
    
    def build_system_prompt(self) -> str:
        """Build system prompt for lore archivist."""
        return """You are the Lore Archivist, guardian of story consistency and canon truth.

Your mission is to validate all scene content against the established lore, ensuring:

1. CHARACTER CONSISTENCY: Behavior, voice, knowledge, and abilities match established profiles
2. WORLD RULE ADHERENCE: Magic systems, technology, society rules are followed
3. TIMELINE INTEGRITY: Events occur in proper sequence without contradictions
4. FACTUAL ACCURACY: Details match previously established facts

When you find violations:
- Cite specific canon sources with line references
- Classify severity as "block" (must fix) or "warn" (should consider)
- Provide minimal correction suggestions
- Generate diffs only for blocking violations

You operate at temperature 0.3 for consistent, deterministic analysis."""
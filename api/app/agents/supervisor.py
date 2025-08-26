"""Supervisor agent for planning and orchestrating sub-tasks as specified in Prompt 12."""
import json
from typing import Dict, Any, List, Optional
import logging

from .base import Agent, AgentOutput
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TaskPlan(BaseModel):
    """Schema for supervisor task planning."""
    tasks: List[Dict[str, str]]
    success_criteria: List[str]


class SupervisorResult(BaseModel):
    """Schema for supervisor agent output."""
    plan: TaskPlan
    variants: Dict[str, Dict[str, Any]]
    receipts: List[Dict[str, str]]
    rationales: Dict[str, str]


async def run_supervisor(
    scene_text: str,
    scene_meta: Dict[str, Any],
    metrics_config: Dict[str, Any],
    edge_intensity: int,
    requested_agents: List[str]
) -> Dict[str, Any]:
    """
    Run supervisor agent to plan sub-tasks, call agents, and compose variants.
    
    Args:
        scene_text: The scene text to process
        scene_meta: Scene metadata (chapter, POV, location, etc.)
        metrics_config: Metrics configuration targets
        edge_intensity: Risk/edge level (0-3)
        requested_agents: List of agent names to run
        
    Returns:
        Dictionary with plan, variants, receipts, and rationales
    """
    try:
        # Create task plan based on requested agents
        tasks = []
        success_criteria = []
        
        if "lore_archivist" in requested_agents:
            tasks.append({"agent": "lore_archivist"})
            success_criteria.append("no_canon_violations")
        
        if "grim_editor" in requested_agents:
            tasks.append({"agent": "grim_editor"})
            success_criteria.append("metrics_within_targets")
        
        if "tone_metrics" in requested_agents:
            tasks.append({"agent": "tone_metrics"})
            success_criteria.append("diffs_valid")
        
        plan = TaskPlan(
            tasks=tasks,
            success_criteria=success_criteria
        )
        
        # Initialize variants based on edge intensity
        variants = {
            "safe": {
                "agents": ["grim_editor"],
                "temperature": 0.3,
                "diff": "",
                "rationale": "Conservative edits focusing on clarity and grammar",
                "risk_level": "low"
            },
            "bold": {
                "agents": ["lore_archivist", "grim_editor", "tone_metrics"],
                "temperature": 0.7,
                "diff": "",
                "rationale": "Significant improvements with lore consistency checking",
                "risk_level": "medium"
            }
        }
        
        # Add red_team variant only if edge_intensity >= 1
        if edge_intensity >= 1:
            variants["red_team"] = {
                "agents": ["red_team"],
                "temperature": 0.9,
                "diff": "",
                "rationale": "Experimental edge variant with creative risks",
                "risk_level": "high",
                "edge_intensity": edge_intensity
            }
        
        # Initialize receipts and rationales
        receipts = []
        rationales = {}
        
        # Add basic rationale for each requested agent
        if "lore_archivist" in requested_agents:
            rationales["lore_archivist"] = "Validates changes against canon and world consistency"
        
        if "grim_editor" in requested_agents:
            rationales["grim_editor"] = "Improves prose clarity, rhythm, and style while preserving meaning"
        
        if "tone_metrics" in requested_agents:
            rationales["tone_metrics"] = "Analyzes and optimizes text metrics against editorial targets"
        
        # Add sample receipts based on scene metadata
        if scene_meta.get("chapter"):
            receipts.append({
                "source": f"codex/chapters/ch{scene_meta['chapter']:02d}.md",
                "lines": "L1-L20"
            })
        
        if scene_meta.get("location"):
            receipts.append({
                "source": f"codex/locations/{scene_meta['location'].lower().replace(' ', '_')}.md",
                "lines": "L5-L15"
            })
        
        result = SupervisorResult(
            plan=plan,
            variants=variants,
            receipts=receipts,
            rationales=rationales
        )
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Supervisor agent failed: {str(e)}")
        return {
            "error": str(e),
            "plan": {"tasks": [], "success_criteria": []},
            "variants": {},
            "receipts": [],
            "rationales": {}
        }


class SupervisorAgent(Agent):
    """Supervisor agent implementation using the base Agent class."""
    
    def __init__(self):
        super().__init__(
            name="supervisor",
            model="anthropic/claude-3-opus",
            tools=["plan_edits", "coordinate_agents", "compose_variants"]
        )
    
    async def run(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the supervisor agent.
        
        Args:
            task: Task parameters with scene_text, edge_intensity, etc.
            context: Context with scene_meta, metrics_config
            
        Returns:
            Supervisor result with plan, variants, receipts, rationales
        """
        scene_text = task.get("scene_text", "")
        edge_intensity = task.get("edge_intensity", 0)
        requested_agents = task.get("agents", ["grim_editor"])
        
        scene_meta = context.get("scene_meta", {})
        metrics_config = context.get("metrics_config", {})
        
        # Use the function implementation
        result = await run_supervisor(
            scene_text=scene_text,
            scene_meta=scene_meta,
            metrics_config=metrics_config,
            edge_intensity=edge_intensity,
            requested_agents=requested_agents
        )
        
        self.log_result(result)
        return result
    
    def build_system_prompt(self) -> str:
        """Build system prompt for supervisor agent."""
        return """You are the Supervisor Agent, responsible for strategic planning and coordination of manuscript editing tasks.

Your role is to:
1. Analyze the scene and plan appropriate sub-tasks
2. Coordinate multiple agents (Lore Archivist, Grim Editor, Tone Metrics)
3. Compose different editing variants (safe, bold, red-team)
4. Ensure all changes maintain story coherence and author voice

You provide strategic oversight and make high-level decisions about the editing approach while delegating specific tasks to specialized agents."""
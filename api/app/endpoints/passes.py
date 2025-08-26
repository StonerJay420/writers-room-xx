"""Pass orchestrator endpoint as specified in Prompt 16."""
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import logging

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..agents.supervisor import run_supervisor, SupervisorAgent
from ..agents.lore_archivist import run_lore_archivist, LoreArchivistAgent
from ..agents.grim_editor import run_grim_editor, GrimEditorAgent 
from ..agents.tone_metrics import run_tone_metrics, ToneMetricsAgent
from ..services.llm_client import LLMClient
from ..utils.diff import make_unified_diff

logger = logging.getLogger(__name__)

router = APIRouter()


class PassRequest(BaseModel):
    """Request model for new pass."""
    scene_text: str
    scene_meta: Dict[str, Any]
    agents: List[str]  # List of agent names to run
    edge_intensity: int = 0  # 0-3 risk level
    targets: Dict[str, Any] = {}  # Metrics targets


class PassResult(BaseModel):
    """Result model for completed pass."""
    pass_id: str
    status: str  # "completed", "failed", "running"
    variants: Dict[str, Dict[str, Any]]
    agent_results: Dict[str, Dict[str, Any]]
    overall_assessment: str
    processing_time: float
    cost_usd: float
    created_at: str


# In-memory storage for pass results (in production, use database)
pass_results: Dict[str, Dict[str, Any]] = {}


@router.post("/passes/new")
async def create_new_pass(
    request: PassRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Create new pass with agent orchestration.
    
    Returns job ID for tracking progress.
    """
    try:
        pass_id = str(uuid.uuid4())
        
        # Initialize pass result
        pass_results[pass_id] = {
            "pass_id": pass_id,
            "status": "running",
            "variants": {},
            "agent_results": {},
            "overall_assessment": "Processing...",
            "processing_time": 0.0,
            "cost_usd": 0.0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Start background processing
        background_tasks.add_task(
            process_pass,
            pass_id=pass_id,
            request=request
        )
        
        return {"pass_id": pass_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Failed to create pass: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/passes/{pass_id}")
async def get_pass_result(pass_id: str) -> Dict[str, Any]:
    """Get pass result by ID."""
    if pass_id not in pass_results:
        raise HTTPException(status_code=404, detail="Pass not found")
    
    return pass_results[pass_id]


@router.get("/passes/{pass_id}/status")
async def get_pass_status(pass_id: str) -> Dict[str, str]:
    """Get pass status by ID."""
    if pass_id not in pass_results:
        raise HTTPException(status_code=404, detail="Pass not found")
    
    result = pass_results[pass_id]
    return {
        "pass_id": pass_id,
        "status": result["status"],
        "progress": _calculate_progress(result)
    }


async def process_pass(pass_id: str, request: PassRequest):
    """Background task to process the pass through all agents."""
    start_time = datetime.utcnow()
    total_cost = 0.0
    
    try:
        # Initialize LLM client (in production, get from config/environment)
        llm_client = LLMClient(
            api_key="dummy_key",  # Replace with actual API key
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Run supervisor agent first to plan the pass
        logger.info(f"Pass {pass_id}: Running supervisor agent")
        supervisor_result = await run_supervisor(
            scene_text=request.scene_text,
            scene_meta=request.scene_meta,
            metrics_config=request.targets,
            edge_intensity=request.edge_intensity,
            requested_agents=request.agents
        )
        
        pass_results[pass_id]["agent_results"]["supervisor"] = supervisor_result
        total_cost += supervisor_result.get("cost_usd", 0.0)
        
        # Initialize variants from supervisor
        variants = supervisor_result.get("variants", {})
        
        # Run requested agents
        agent_tasks = []
        
        if "lore_archivist" in request.agents:
            agent_tasks.append(("lore_archivist", _run_lore_archivist_task(request, llm_client)))
        
        if "grim_editor" in request.agents:
            agent_tasks.append(("grim_editor", _run_grim_editor_task(request, llm_client)))
            
        if "tone_metrics" in request.agents:
            agent_tasks.append(("tone_metrics", _run_tone_metrics_task(request, llm_client)))
        
        # Run agents concurrently
        if agent_tasks:
            logger.info(f"Pass {pass_id}: Running {len(agent_tasks)} agents concurrently")
            agent_names, agent_coroutines = zip(*agent_tasks)
            agent_results = await asyncio.gather(*agent_coroutines, return_exceptions=True)
            
            # Process agent results
            for agent_name, result in zip(agent_names, agent_results):
                if isinstance(result, Exception):
                    logger.error(f"Agent {agent_name} failed: {str(result)}")
                    pass_results[pass_id]["agent_results"][agent_name] = {"error": str(result)}
                else:
                    pass_results[pass_id]["agent_results"][agent_name] = result
                    total_cost += result.get("cost_usd", 0.0)
        
        # Compose final variants with agent results
        final_variants = _compose_variants(variants, pass_results[pass_id]["agent_results"], request)
        
        # Generate overall assessment
        overall_assessment = _generate_overall_assessment(pass_results[pass_id]["agent_results"], request)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Update final result
        pass_results[pass_id].update({
            "status": "completed",
            "variants": final_variants,
            "overall_assessment": overall_assessment,
            "processing_time": processing_time,
            "cost_usd": total_cost
        })
        
        logger.info(f"Pass {pass_id}: Completed successfully in {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Pass {pass_id}: Failed with error: {str(e)}")
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        pass_results[pass_id].update({
            "status": "failed",
            "overall_assessment": f"Pass failed: {str(e)}",
            "processing_time": processing_time,
            "cost_usd": total_cost,
            "error": str(e)
        })


async def _run_lore_archivist_task(request: PassRequest, llm_client: LLMClient) -> Dict[str, Any]:
    """Run lore archivist agent task."""
    # Mock retrieve function for demo (in production, use actual vector search)
    def mock_retrieve(query: str, k: int = 5, filters: Optional[Dict] = None):
        return [
            {
                "source_path": "codex/characters/protagonist.md",
                "start_line": 10,
                "end_line": 20,
                "text": f"Character information related to: {query}"
            }
        ]
    
    return await run_lore_archivist(
        scene_text=request.scene_text,
        scene_meta=request.scene_meta,
        retrieve_fn=mock_retrieve
    )


async def _run_grim_editor_task(request: PassRequest, llm_client: LLMClient) -> Dict[str, Any]:
    """Run grim editor agent task."""
    return await run_grim_editor(
        scene_text=request.scene_text,
        style_targets=request.targets
    )


async def _run_tone_metrics_task(request: PassRequest, llm_client: LLMClient) -> Dict[str, Any]:
    """Run tone & metrics agent task."""
    return await run_tone_metrics(
        scene_text=request.scene_text,
        targets=request.targets
    )


def _compose_variants(
    base_variants: Dict[str, Any], 
    agent_results: Dict[str, Dict[str, Any]], 
    request: PassRequest
) -> Dict[str, Dict[str, Any]]:
    """Compose final variants with agent results."""
    variants = dict(base_variants)
    
    # Add diffs from grim editor to appropriate variants
    grim_result = agent_results.get("grim_editor", {})
    grim_diff = grim_result.get("diff", "")
    
    if grim_diff:
        # Apply grim editor diff to safe and bold variants
        if "safe" in variants:
            variants["safe"]["diff"] = grim_diff
            variants["safe"]["rationale"] = grim_result.get("rationale", [])
        
        if "bold" in variants:
            variants["bold"]["diff"] = grim_diff
            variants["bold"]["rationale"] = grim_result.get("rationale", [])
    
    # Add lore findings to bold and red_team variants
    lore_result = agent_results.get("lore_archivist", {})
    if lore_result.get("findings"):
        blocking_findings = [f for f in lore_result.get("findings", []) if f.get("severity") == "block"]
        
        if blocking_findings and "bold" in variants:
            variants["bold"]["lore_blocks"] = len(blocking_findings)
            variants["bold"]["lore_diff"] = lore_result.get("diff", "")
        
        if "red_team" in variants:
            variants["red_team"]["lore_findings"] = len(lore_result.get("findings", []))
    
    # Add metrics analysis
    metrics_result = agent_results.get("tone_metrics", {})
    if metrics_result:
        for variant_name in variants:
            variants[variant_name]["metrics_assessment"] = metrics_result.get("overall_assessment", "")
            variants[variant_name]["readability_grade"] = metrics_result.get("readability_grade", "")
    
    return variants


def _generate_overall_assessment(agent_results: Dict[str, Dict[str, Any]], request: PassRequest) -> str:
    """Generate overall pass assessment."""
    assessments = []
    
    # Check supervisor planning
    supervisor_result = agent_results.get("supervisor", {})
    if supervisor_result and not supervisor_result.get("error"):
        variant_count = len(supervisor_result.get("variants", {}))
        assessments.append(f"Generated {variant_count} editing variants")
    
    # Check lore consistency
    lore_result = agent_results.get("lore_archivist", {})
    if lore_result and not lore_result.get("error"):
        findings = lore_result.get("findings", [])
        blocking = len([f for f in findings if f.get("severity") == "block"])
        if blocking > 0:
            assessments.append(f"Found {blocking} blocking lore violations")
        else:
            assessments.append("No blocking lore violations detected")
    
    # Check prose improvements
    grim_result = agent_results.get("grim_editor", {})
    if grim_result and not grim_result.get("error"):
        if grim_result.get("diff"):
            assessments.append("Generated prose improvements")
        else:
            assessments.append("No prose changes recommended")
    
    # Check metrics compliance
    metrics_result = agent_results.get("tone_metrics", {})
    if metrics_result and not metrics_result.get("error"):
        metrics_before = metrics_result.get("metrics_before", {})
        within_target = sum(1 for m in metrics_before.values() if m.get("status") == "within_target")
        total = len(metrics_before)
        assessments.append(f"Metrics compliance: {within_target}/{total} targets met")
    
    if not assessments:
        return "Pass completed with limited results"
    
    return ". ".join(assessments) + "."


def _calculate_progress(result: Dict[str, Any]) -> str:
    """Calculate progress percentage for a running pass."""
    if result["status"] == "completed":
        return "100%"
    elif result["status"] == "failed":
        return "failed"
    
    # Count completed agents
    agent_results = result.get("agent_results", {})
    completed_agents = len([r for r in agent_results.values() if r])
    
    # Estimate total agents (supervisor + requested)
    total_agents = 1  # supervisor always runs
    if isinstance(agent_results, dict):
        total_agents += len([k for k in agent_results.keys() if k != "supervisor"])
    
    if total_agents == 0:
        return "0%"
    
    progress = (completed_agents / total_agents) * 100
    return f"{progress:.0f}%"
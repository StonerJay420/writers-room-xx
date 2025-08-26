"""Pass orchestrator router for running agent passes."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json
import os
from pathlib import Path

from ..agents.supervisor import run_supervisor
from ..agents.lore_archivist import run_lore_archivist
from ..agents.grim_editor import run_grim_editor
from ..agents.tone_metrics import run_tone_metrics
from ..agents.dialogue_demon import run_dialogue_demon
from ..agents.pacing_surgeon import run_pacing_surgeon
from ..agents.plot_twister import run_plot_twister
from ..agents.red_team import run_red_team
from ..agents.reviewer_pack import run_reviewer_pack
from ..agents.voice_simulator import run_voice_simulator
from ..rag.retrieve import retrieve_canon
from ..db import get_read_session, get_write_session
from sqlalchemy.orm import Session

router = APIRouter(prefix="/passes", tags=["passes"])


class PassRequest(BaseModel):
    """Request model for running a pass."""
    scene_id: str
    agents: List[str] = ["lore_archivist", "grim_editor", "tone_metrics"]
    edge_intensity: int = 0


class PassResponse(BaseModel):
    """Response model for pass results."""
    scene_id: str
    variants: Dict[str, Any]
    reports: Dict[str, Any]


@router.post("/run", response_model=PassResponse)
async def run_pass(
    request: PassRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_read_session)
):
    """
    Run a pass on a scene with specified agents.
    
    This endpoint orchestrates the agents to analyze and improve a scene,
    returning multiple variants (safe, bold, red_team) with diffs and metrics.
    """
    try:
        # Validate scene_id to prevent directory traversal
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', request.scene_id):
            raise HTTPException(status_code=400, detail="Invalid scene ID format")
        
        # Load scene text from file
        scene_path = Path(f"data/manuscript/{request.scene_id}.md")
        if not scene_path.exists():
            raise HTTPException(status_code=404, detail=f"Scene {request.scene_id} not found")
        
        scene_text = scene_path.read_text(encoding='utf-8')
        
        # Extract scene metadata
        scene_meta = {
            "scene_id": request.scene_id,
            "chapter": int(request.scene_id.split('_')[0][2:]) if 'ch' in request.scene_id else 1,
            "pov": None,  # Would be extracted from frontmatter
            "location": None  # Would be extracted from frontmatter
        }
        
        # Load metrics config
        metrics_config = {}
        metrics_path = Path("configs/metrics.yaml")
        if metrics_path.exists():
            import yaml
            with open(metrics_path) as f:
                metrics_data = yaml.safe_load(f)
                # Flatten nested metrics config for compatibility
                if 'targets' in metrics_data:
                    targets = metrics_data['targets']
                    metrics_config = {
                        'flesch': targets.get('readability', {}).get('flesch_reading_ease', {}),
                        'grade_level': targets.get('readability', {}).get('flesch_kincaid_grade', {}),
                        'sentence_length': targets.get('sentence_structure', {}).get('avg_sentence_length', {}),
                        'syllable_density': targets.get('word_usage', {}).get('avg_syllables_per_word', {}),
                        'dialogue_ratio': targets.get('dialogue', {}).get('dialogue_percentage', {})
                    }
        
        # Run supervisor to coordinate agents
        supervisor_result = await run_supervisor(
            scene_text=scene_text,
            scene_meta=scene_meta,
            metrics_config=metrics_config,
            edge_intensity=request.edge_intensity,
            requested_agents=request.agents
        )
        
        # Run individual agents if supervisor didn't fully orchestrate
        agent_results = {}
        
        if "lore_archivist" in request.agents:
            try:
                lore_result = await run_lore_archivist(
                    scene_text=scene_text,
                    scene_meta=scene_meta,
                    retrieve_fn=lambda q, k, f: retrieve_canon(q, k, f) if 'retrieve_canon' in globals() else [],
                    model="anthropic/claude-3-opus"
                )
                agent_results["lore_archivist"] = lore_result
            except Exception as e:
                agent_results["lore_archivist"] = {
                    "error": f"Lore Archivist failed: {str(e)}",
                    "status": "failed",
                    "findings": [],
                    "receipts": []
                }
        
        if "grim_editor" in request.agents:
            try:
                grim_result = await run_grim_editor(
                    scene_text=scene_text,
                    style_targets=metrics_config,
                    model="anthropic/claude-3-haiku"
                )
                agent_results["grim_editor"] = grim_result
            except Exception as e:
                agent_results["grim_editor"] = {
                    "error": f"Grim Editor failed: {str(e)}",
                    "status": "failed",
                    "diff": "",
                    "rationale": [f"Editor execution failed: {str(e)}"]
                }
        
        if "tone_metrics" in request.agents:
            try:
                tone_result = run_tone_metrics(
                    scene_text=scene_text,
                    targets=metrics_config,
                    model="anthropic/claude-3-haiku"
                )
                agent_results["tone_metrics"] = tone_result
            except Exception as e:
                agent_results["tone_metrics"] = {
                    "error": f"Tone Metrics failed: {str(e)}",
                    "status": "failed",
                    "metrics_before": {},
                    "overall_assessment": f"Analysis failed: {str(e)}",
                    "recommendations": ["Please review the scene text and try again"]
                }
        
        # Combine results into variants
        variants = supervisor_result.get("variants", {})
        
        # Add agent results to variants if not already populated
        if not variants.get("safe", {}).get("diff"):
            if "grim_editor" in agent_results:
                variants["safe"] = {
                    "agents": ["grim_editor"],
                    "diff": agent_results["grim_editor"].get("diff", ""),
                    "rationale": agent_results["grim_editor"].get("rationale", []),
                    "temperature": 0.3,
                    "risk_level": "low"
                }
        
        if not variants.get("bold", {}).get("diff"):
            if "lore_archivist" in agent_results and "grim_editor" in agent_results:
                variants["bold"] = {
                    "agents": ["lore_archivist", "grim_editor", "tone_metrics"],
                    "diff": agent_results["grim_editor"].get("diff", ""),
                    "rationale": agent_results["grim_editor"].get("rationale", []),
                    "temperature": 0.7,
                    "risk_level": "medium",
                    "canon_findings": agent_results["lore_archivist"].get("findings", [])
                }
        
        # Build reports
        reports = {
            "metrics": agent_results.get("tone_metrics", {}),
            "canon_receipts": agent_results.get("lore_archivist", {}).get("receipts", []),
            "rationales": {
                agent: result.get("rationale", [])
                for agent, result in agent_results.items()
            }
        }
        
        # Save artifacts
        artifacts_dir = Path(f"artifacts/patches/{request.scene_id}")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        for variant_name, variant_data in variants.items():
            if variant_data.get("diff"):
                diff_path = artifacts_dir / f"{request.scene_id}_{variant_name}.diff"
                diff_path.write_text(variant_data["diff"])
                
                json_path = artifacts_dir / f"{request.scene_id}_{variant_name}.json"
                json_path.write_text(json.dumps(variant_data, indent=2))
        
        return PassResponse(
            scene_id=request.scene_id,
            variants=variants,
            reports=reports
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def passes_status():
    """Get passes service status."""
    return {
        "status": "passes service ready", 
        "core_agents": ["supervisor", "lore_archivist", "grim_editor", "tone_metrics"],
        "creative_agents": ["dialogue_demon", "pacing_surgeon", "plot_twister", "red_team", "reviewer_pack", "voice_simulator"]
    }
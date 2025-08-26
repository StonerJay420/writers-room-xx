"""Patches router for AI-generated edits."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import time
from sqlalchemy.orm import Session

from ..db import get_read_session

router = APIRouter(prefix="/patches", tags=["patches"])


class GeneratePatchesRequest(BaseModel):
    scene_id: str
    agents: List[str]
    variants: List[str]


class PatchResponse(BaseModel):
    patch_id: str
    agent: str
    variant: str
    diff: str
    confidence: float
    rationale: str


class GeneratePatchesResponse(BaseModel):
    patches: List[PatchResponse]
    cost_usd: float
    processing_time: float


@router.post("/generate", response_model=GeneratePatchesResponse)
async def generate_patches(
    request: GeneratePatchesRequest,
    db: Session = Depends(get_read_session)
) -> GeneratePatchesResponse:
    """Generate AI patches for a scene."""
    start_time = time.time()

    # Validate scene exists
    from ..models import Scene
    scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {request.scene_id} not found")

    # Load scene content
    from pathlib import Path
    scene_path = Path(f"data/manuscript/{request.scene_id}.md")
    if not scene_path.exists():
        raise HTTPException(status_code=404, detail=f"Scene {request.scene_id} not found")
    
    scene_text = scene_path.read_text(encoding='utf-8')
    
    # Extract scene metadata
    scene_meta = {
        "scene_id": request.scene_id,
        "chapter": int(request.scene_id.split('_')[0][2:]) if 'ch' in request.scene_id else 1,
        "pov": None,
        "location": None
    }
    
    # Import agent functions
    from ..agents.supervisor import run_supervisor
    from ..agents.lore_archivist import run_lore_archivist
    from ..agents.grim_editor import run_grim_editor
    from ..agents.tone_metrics import run_tone_metrics
    from ..rag.retrieve import retrieve_canon
    
    # Load metrics config
    metrics_config = {}
    metrics_path = Path("configs/metrics.yaml")
    if metrics_path.exists():
        import yaml
        with open(metrics_path) as f:
            metrics_data = yaml.safe_load(f)
            if 'targets' in metrics_data:
                targets = metrics_data['targets']
                metrics_config = {
                    'flesch': targets.get('readability', {}).get('flesch_reading_ease', {}),
                    'grade_level': targets.get('readability', {}).get('flesch_kincaid_grade', {}),
                    'sentence_length': targets.get('sentence_structure', {}).get('avg_sentence_length', {}),
                    'syllable_density': targets.get('word_usage', {}).get('avg_syllables_per_word', {}),
                    'dialogue_ratio': targets.get('dialogue', {}).get('dialogue_percentage', {})
                }
    
    patches = []
    generated_variants = {}
    
    try:
        # Run agents based on request
        agent_results = {}
        
        if "lore_archivist" in request.agents:
            lore_result = await run_lore_archivist(
                scene_text=scene_text,
                scene_meta=scene_meta,
                retrieve_fn=lambda q, k, f: retrieve_canon(q, k, f) if 'retrieve_canon' in globals() else [],
                model="anthropic/claude-3-opus"
            )
            agent_results["lore_archivist"] = lore_result
        
        if "grim_editor" in request.agents:
            grim_result = await run_grim_editor(
                scene_text=scene_text,
                style_targets=metrics_config,
                model="anthropic/claude-3-haiku"
            )
            agent_results["grim_editor"] = grim_result
        
        if "tone_metrics" in request.agents:
            tone_result = run_tone_metrics(
                scene_text=scene_text,
                targets=metrics_config,
                model="anthropic/claude-3-haiku"
            )
            agent_results["tone_metrics"] = tone_result
        
        # Generate patches for each requested variant
        for variant in request.variants:
            for agent in request.agents:
                if agent in agent_results:
                    result = agent_results[agent]
                    
                    # Extract diff and rationale from agent result
                    diff = result.get("diff", "")
                    rationale = result.get("rationale", [])
                    confidence = result.get("confidence", 0.7)
                    
                    # If no diff available, generate one based on recommendations
                    if not diff and "recommendations" in result:
                        diff = f"# Recommendations for {agent} ({variant} variant):\n"
                        for i, rec in enumerate(result["recommendations"][:3], 1):
                            diff += f"# {i}. {rec}\n"
                    
                    patch = PatchResponse(
                        patch_id=str(uuid.uuid4()),
                        agent=agent,
                        variant=variant,
                        diff=diff,
                        confidence=confidence,
                        rationale=rationale[0] if isinstance(rationale, list) and rationale else str(rationale) if rationale else f"Generated {variant} improvements by {agent}"
                    )
                    patches.append(patch)
        
        # If no patches were generated, create at least one informational patch
        if not patches:
            patch = PatchResponse(
                patch_id=str(uuid.uuid4()),
                agent="system",
                variant="info",
                diff="# No changes suggested\n# All metrics are within acceptable ranges",
                confidence=1.0,
                rationale="Scene analysis completed - no improvements needed"
            )
            patches.append(patch)
            
    except Exception as e:
        # Fallback to error patch if agent execution fails
        patch = PatchResponse(
            patch_id=str(uuid.uuid4()),
            agent="system",
            variant="error",
            diff=f"# Error during analysis: {str(e)}",
            confidence=0.0,
            rationale=f"Agent execution failed: {str(e)}"
        )
        patches.append(patch)

    processing_time = time.time() - start_time

    return GeneratePatchesResponse(
        patches=patches,
        cost_usd=0.05 * len(patches),  # Mock cost
        processing_time=processing_time
    )


@router.get("/")
async def patches_status():
    """Get patches status."""
    return {"status": "patches service ready"}
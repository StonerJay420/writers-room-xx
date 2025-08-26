"""Agent orchestration and processing service."""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import time
from datetime import datetime

from .ai_service import ai_service
from .metrics_service import metrics_service, TextMetrics
from .diff_service import diff_service, DiffResult
from ..models import Scene, Job, Artifact
from ..db import get_write_session


@dataclass
class AgentResult:
    """Result from a single agent pass."""
    agent_name: str
    model_id: str
    original_text: str
    revised_text: str
    reasoning: str
    metrics_before: Optional[TextMetrics]
    metrics_after: Optional[TextMetrics]
    diff: Optional[DiffResult]
    cost_usd: float
    processing_time: float
    confidence_score: float
    suggestions: List[str]


@dataclass
class PatchVariant:
    """A patch variant with different risk/reward profiles."""
    name: str
    description: str
    agents: List[str]
    model_overrides: Dict[str, str]
    risk_level: str  # safe, bold, experimental
    expected_improvements: List[str]


class AgentService:
    """Service for orchestrating AI agents and generating patches."""
    
    def __init__(self):
        self.variants = {
            "safe": PatchVariant(
                name="Safe Edits",
                description="Conservative improvements focusing on clarity and readability",
                agents=["grim_editor", "tone_metrics"],
                model_overrides={},
                risk_level="safe",
                expected_improvements=["Grammar", "Clarity", "Flow"]
            ),
            "bold": PatchVariant(
                name="Bold Revisions", 
                description="Significant structural and stylistic improvements",
                agents=["lore_archivist", "grim_editor", "tone_metrics"],
                model_overrides={},
                risk_level="bold",
                expected_improvements=["Structure", "Voice", "Impact", "Canon consistency"]
            ),
            "experimental": PatchVariant(
                name="Experimental",
                description="Radical reimagining with creative risks",
                agents=["grim_editor", "tone_metrics", "supervisor"],
                model_overrides={"supervisor": "anthropic/claude-3-opus"},
                risk_level="experimental", 
                expected_improvements=["Creativity", "Dramatic impact", "Unique voice"]
            )
        }
    
    async def process_scene(
        self,
        scene_id: str,
        variant_names: List[str] = ["safe", "bold"],
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a scene with multiple agent passes and variants."""
        
        start_time = time.time()
        
        with get_write_session() as db:
            # Get scene
            scene = db.query(Scene).filter(Scene.id == scene_id).first()
            if not scene:
                raise ValueError(f"Scene {scene_id} not found")
            
            # Read scene content
            with open(scene.text_path, 'r') as f:
                original_text = f.read()
            
            # Create job record
            job = Job(
                scene_id=scene_id,
                job_type="agent_processing",
                status="running",
                request_data=json.dumps({
                    "variants": variant_names,
                    "custom_instructions": custom_instructions
                })
            )
            db.add(job)
            db.commit()
            
            results = []
            total_cost = 0.0
            
            try:
                # Process each variant
                for variant_name in variant_names:
                    if variant_name not in self.variants:
                        continue
                    
                    variant = self.variants[variant_name]
                    variant_result = await self._process_variant(
                        scene, original_text, variant, custom_instructions
                    )
                    
                    results.append(variant_result)
                    total_cost += sum(r.cost_usd for r in variant_result["agent_results"])
                    
                    # Store artifacts
                    for agent_result in variant_result["agent_results"]:
                        artifact = Artifact(
                            job_id=job.id,
                            artifact_type="agent_result",
                            name=f"{variant_name}_{agent_result.agent_name}",
                            content=json.dumps(asdict(agent_result)),
                            metadata=json.dumps({
                                "variant": variant_name,
                                "agent": agent_result.agent_name,
                                "model": agent_result.model_id,
                                "cost": agent_result.cost_usd
                            })
                        )
                        db.add(artifact)
                
                # Update job status
                processing_time = time.time() - start_time
                job.status = "completed"
                job.cost_usd = total_cost
                job.processing_time = processing_time
                job.result_data = json.dumps({
                    "variants": len(results),
                    "total_agents": sum(len(r["agent_results"]) for r in results),
                    "best_variant": self._select_best_variant(results)
                })
                db.commit()
                
                return {
                    "job_id": job.id,
                    "scene_id": scene_id,
                    "variants": results,
                    "total_cost": total_cost,
                    "processing_time": processing_time,
                    "best_variant": self._select_best_variant(results)
                }
                
            except Exception as e:
                job.status = "failed"
                job.error_message = str(e)
                db.commit()
                raise
    
    async def _process_variant(
        self,
        scene: Scene,
        original_text: str,
        variant: PatchVariant,
        custom_instructions: Optional[str]
    ) -> Dict[str, Any]:
        """Process a single variant with its agent chain."""
        
        agent_results = []
        current_text = original_text
        
        # Calculate initial metrics
        initial_metrics = metrics_service.calculate_metrics(original_text)
        
        # Process each agent in sequence
        for agent_name in variant.agents:
            agent_result = await self._process_with_agent(
                agent_name,
                scene,
                current_text,
                original_text,
                variant.model_overrides.get(agent_name),
                custom_instructions,
                variant.risk_level
            )
            
            agent_results.append(agent_result)
            current_text = agent_result.revised_text
        
        # Calculate final metrics and diff
        final_metrics = metrics_service.calculate_metrics(current_text)
        final_diff = diff_service.generate_unified_diff(
            original_text, 
            current_text, 
            filename=f"{scene.id}.md"
        )
        
        # Calculate improvement score
        improvement_score = self._calculate_improvement_score(
            initial_metrics, final_metrics, variant.expected_improvements
        )
        
        return {
            "variant_name": variant.name,
            "risk_level": variant.risk_level,
            "agent_results": agent_results,
            "final_text": current_text,
            "initial_metrics": initial_metrics,
            "final_metrics": final_metrics,
            "final_diff": final_diff,
            "improvement_score": improvement_score,
            "total_changes": final_diff.changes,
            "suggestions": self._extract_suggestions(agent_results)
        }
    
    async def _process_with_agent(
        self,
        agent_name: str,
        scene: Scene,
        current_text: str,
        original_text: str,
        model_override: Optional[str],
        custom_instructions: Optional[str],
        risk_level: str
    ) -> AgentResult:
        """Process text with a specific agent."""
        
        start_time = time.time()
        
        # Get agent configuration
        agent_config = self._get_agent_config(agent_name, risk_level)
        model_id = model_override or agent_config.get("default_model", "anthropic/claude-3-haiku")
        
        # Build prompt
        prompt = self._build_agent_prompt(
            agent_name, current_text, scene, agent_config, custom_instructions, risk_level
        )
        
        # Call AI service
        response, cost = await ai_service.generate_completion(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=agent_config.get("max_tokens", 2000)
        )
        
        # Parse response
        try:
            response_data = json.loads(response)
            revised_text = response_data.get("revised_text", current_text)
            reasoning = response_data.get("reasoning", "No reasoning provided")
            confidence = response_data.get("confidence", 0.5)
            suggestions = response_data.get("suggestions", [])
        except json.JSONDecodeError:
            # Fallback parsing
            revised_text = current_text
            reasoning = "Failed to parse agent response"
            confidence = 0.0
            suggestions = []
        
        # Calculate metrics and diff
        metrics_before = metrics_service.calculate_metrics(current_text)
        metrics_after = metrics_service.calculate_metrics(revised_text)
        diff = diff_service.generate_unified_diff(
            current_text, revised_text, filename=f"{scene.id}_{agent_name}.md"
        )
        
        processing_time = time.time() - start_time
        
        return AgentResult(
            agent_name=agent_name,
            model_id=model_id,
            original_text=current_text,
            revised_text=revised_text,
            reasoning=reasoning,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            diff=diff,
            cost_usd=cost,
            processing_time=processing_time,
            confidence_score=confidence,
            suggestions=suggestions
        )
    
    def _get_agent_config(self, agent_name: str, risk_level: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        
        base_configs = {
            "lore_archivist": {
                "role": "Canon consistency checker and lore expert",
                "default_model": "anthropic/claude-3-sonnet", 
                "max_tokens": 2000,
                "focus": "character consistency, world-building, canon adherence"
            },
            "grim_editor": {
                "role": "Line editor focused on prose improvement",
                "default_model": "anthropic/claude-3-haiku",
                "max_tokens": 2500,
                "focus": "grammar, style, flow, clarity, word choice"
            },
            "tone_metrics": {
                "role": "Writing quality and tone analyzer",
                "default_model": "openai/gpt-4-turbo-preview", 
                "max_tokens": 1500,
                "focus": "readability, tone consistency, pacing, voice"
            },
            "supervisor": {
                "role": "Senior editor providing strategic guidance",
                "default_model": "anthropic/claude-3-opus",
                "max_tokens": 3000,
                "focus": "story structure, character development, thematic coherence"
            }
        }
        
        config = base_configs.get(agent_name, {})
        
        # Adjust for risk level
        if risk_level == "experimental":
            config["max_tokens"] = config.get("max_tokens", 2000) + 500
        elif risk_level == "safe":
            config["max_tokens"] = config.get("max_tokens", 2000) - 200
            
        return config
    
    def _build_agent_prompt(
        self,
        agent_name: str,
        text: str,
        scene: Scene,
        config: Dict[str, Any],
        custom_instructions: Optional[str],
        risk_level: str
    ) -> str:
        """Build prompt for a specific agent."""
        
        role = config.get("role", "AI assistant")
        focus = config.get("focus", "general improvements")
        
        prompt = f"""You are a {role} working on manuscript editing. Your focus is {focus}.

RISK LEVEL: {risk_level.upper()}
{"- Make conservative, safe improvements only" if risk_level == "safe" else ""}
{"- Make bold but justified improvements" if risk_level == "bold" else ""}
{"- Feel free to make experimental, creative changes" if risk_level == "experimental" else ""}

SCENE CONTEXT:
- Scene ID: {scene.id}
- Chapter: {scene.chapter}
- POV: {scene.pov or 'Unknown'}
- Location: {scene.location or 'Unknown'}

CURRENT TEXT:
{text}

INSTRUCTIONS:
{custom_instructions or f"Apply your expertise to improve this text focusing on {focus}."}

Please analyze the text and provide improvements. Respond in JSON format:
{{
  "revised_text": "your improved version of the text",
  "reasoning": "explanation of changes made and why",
  "confidence": 0.8,
  "suggestions": ["specific actionable suggestions for further improvement"]
}}"""
        
        return prompt
    
    def _calculate_improvement_score(
        self,
        before: TextMetrics,
        after: TextMetrics,
        expected_improvements: List[str]
    ) -> float:
        """Calculate improvement score based on metrics."""
        
        comparison = metrics_service.compare_metrics(before, after)
        improvements = comparison.get("improvements", 0)
        regressions = comparison.get("regressions", 0)
        
        # Base score from metrics
        base_score = (improvements - regressions) / max(improvements + regressions, 1)
        
        # Bonus for meeting expected improvements
        bonus = 0
        for improvement in expected_improvements:
            if improvement.lower() in ["grammar", "clarity"]:
                if after.flesch_reading_ease > before.flesch_reading_ease:
                    bonus += 0.1
            elif improvement.lower() == "flow":
                if after.avg_words_per_sentence < before.avg_words_per_sentence:
                    bonus += 0.1
        
        return min(max(base_score + bonus, 0), 1)
    
    def _extract_suggestions(self, agent_results: List[AgentResult]) -> List[str]:
        """Extract all suggestions from agent results."""
        
        all_suggestions = []
        for result in agent_results:
            all_suggestions.extend(result.suggestions)
        
        # Deduplicate while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in all_suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:10]  # Limit to top 10
    
    def _select_best_variant(self, variants: List[Dict[str, Any]]) -> Optional[str]:
        """Select the best variant based on improvement scores."""
        
        if not variants:
            return None
        
        best_variant = max(variants, key=lambda v: v.get("improvement_score", 0))
        return best_variant.get("variant_name")


# Global agent service instance
agent_service = AgentService()
"""AI router for text analysis and recommendations."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import time
from sqlalchemy.orm import Session
from pathlib import Path
import yaml

from ..db import get_read_session
from ..auth import get_current_user, get_user_llm_client
from ..services.llm_client import LLMClient

router = APIRouter(prefix="/ai", tags=["ai"])


class RecommendationRequest(BaseModel):
    """Request for AI text recommendations."""
    text: str
    context: str = "manuscript_editing"
    max_recommendations: int = 5


class AIRecommendation(BaseModel):
    """AI recommendation model."""
    id: str
    original_text: str
    suggested_text: str
    reason: str
    confidence: float
    type: str  # 'grammar', 'style', 'clarity', 'tone', 'consistency'
    codex_references: List[str] = []


class RecommendationsResponse(BaseModel):
    """Response containing AI recommendations."""
    recommendations: List[AIRecommendation]
    total: int
    processing_time: float
    codex_context: List[Dict[str, Any]] = []


@router.post("/recommendations", response_model=RecommendationsResponse)
async def get_text_recommendations(
    request: RecommendationRequest,
    user: dict = Depends(get_current_user),
    llm_client: LLMClient = Depends(get_user_llm_client),
    db: Session = Depends(get_read_session)
):
    """Get AI recommendations for text improvement using OpenRouter BYOK."""
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    start_time = time.time()
    
    try:
        # Check if user has configured their OpenRouter API key
        if not llm_client.api_key:
            # Return mock recommendations if no API key
            mock_recommendations = generate_mock_recommendations(request.text)
            processing_time = time.time() - start_time
            
            return RecommendationsResponse(
                recommendations=mock_recommendations,
                total=len(mock_recommendations),
                processing_time=processing_time,
                codex_context=[]
            )
        
        # Get relevant codex entries for context
        codex_context = await get_relevant_codex_entries(request.text)
        
        # Build codex context string
        codex_info = ""
        if codex_context:
            codex_info = "\n\nRELEVANT WORLD/CHARACTER INFORMATION:\n"
            for entry in codex_context:
                codex_info += f"- {entry['name']} ({entry['type']}): {entry.get('description', 'No description')}\n"
                if entry.get('metadata'):
                    for key, value in entry['metadata'].items():
                        if key not in ['name', 'type', 'description'] and value:
                            codex_info += f"  {key}: {value}\n"
            codex_info += "\nEnsure any suggestions maintain consistency with this established world and character information."

        # Use OpenRouter with user's API key for recommendations
        system_prompt = f"You are an expert writing assistant with deep knowledge of this story's world and characters. You provide specific, actionable recommendations for improving manuscript text while maintaining consistency with established lore.{codex_info}"
        
        user_prompt = f"""
        Analyze the following text for writing improvements and provide specific recommendations.
        Focus on {request.context}.
        
        Text to analyze:
        "{request.text}"
        
        Please provide up to {request.max_recommendations} recommendations in JSON format:
        [
          {{
            "id": "unique_id",
            "original_text": "exact text to be replaced",
            "suggested_text": "improved version",
            "reason": "explanation of why this improves the text",
            "confidence": 0.85,
            "type": "grammar|style|clarity|tone|consistency",
            "codex_references": ["character_name", "location_name"]
          }}
        ]
        
        Only suggest changes that significantly improve the text. Focus on:
        - Grammar and syntax errors
        - Style and flow improvements
        - Clarity and readability
        - Tone and voice consistency
        - Consistency with established characters, locations, and world rules
        
        Include "codex_references" array with names of any codex entries relevant to each recommendation.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Use Claude Sonnet for writing recommendations
        llm_response = await llm_client.complete(
            messages=messages,
            model="anthropic/claude-3-sonnet",
            temperature=0.3,
            max_tokens=1500,
            json_mode=True
        )
        
        recommendations_data = json.loads(llm_response.content)
        
        # Parse recommendations
        recommendations = []
        if isinstance(recommendations_data, list):
            recs_list = recommendations_data
        else:
            recs_list = recommendations_data.get("recommendations", [])
        
        for i, rec in enumerate(recs_list[:request.max_recommendations]):
            recommendations.append(AIRecommendation(
                id=rec.get("id", f"rec_{i}"),
                original_text=rec.get("original_text", ""),
                suggested_text=rec.get("suggested_text", ""),
                reason=rec.get("reason", ""),
                confidence=float(rec.get("confidence", 0.5)),
                type=rec.get("type", "style"),
                codex_references=rec.get("codex_references", [])
            ))
        
        processing_time = time.time() - start_time
        
        return RecommendationsResponse(
            recommendations=recommendations,
            total=len(recommendations),
            processing_time=processing_time,
            codex_context=codex_context
        )
        
    except Exception as e:
        # Fall back to mock recommendations if OpenAI fails
        mock_recommendations = generate_mock_recommendations(request.text)
        processing_time = time.time() - start_time
        
        return RecommendationsResponse(
            recommendations=mock_recommendations,
            total=len(mock_recommendations),
            processing_time=processing_time,
            codex_context=[]
        )


def generate_mock_recommendations(text: str) -> List[AIRecommendation]:
    """Generate mock recommendations for demo purposes."""
    recommendations = []
    sentences = text.split('.')[:3]  # Analyze first 3 sentences
    
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            recommendations.append(AIRecommendation(
                id=f"mock_{i}",
                original_text=sentence.strip() + '.',
                suggested_text=sentence.strip() + ', enhancing the narrative flow.',
                reason="Adding descriptive elements improves reader engagement",
                confidence=0.75 + (i * 0.05),
                type=["style", "clarity", "tone"][i % 3]
            ))
    
    return recommendations


@router.get("/status")
async def ai_status(
    user: dict = Depends(get_current_user),
    llm_client: LLMClient = Depends(get_user_llm_client)
):
    """Get AI service status for the authenticated user."""
    has_api_key = bool(llm_client.api_key)
    
    return {
        "status": "ai service ready",
        "openrouter_configured": has_api_key,
        "byok_enabled": True,
        "user": user["name"],
        "models_available": [
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet", 
            "anthropic/claude-3-haiku",
            "openai/gpt-4-turbo-preview",
            "openai/gpt-3.5-turbo"
        ] if has_api_key else ["mock"],
        "recommended_model": "anthropic/claude-3-sonnet"
    }


async def get_relevant_codex_entries(text: str) -> List[Dict]:
    """Get codex entries relevant to the provided text."""
    try:
        codex_dir = Path("data/codex")
        if not codex_dir.exists():
            return []
        
        relevant_entries = []
        text_lower = text.lower()
        
        # Simple keyword matching - could be enhanced with semantic search
        for md_file in codex_dir.glob("*.md"):
            if md_file.name.startswith('.'):
                continue
                
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Parse frontmatter if present
                metadata = {}
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1]
                        metadata = yaml.safe_load(yaml_content) or {}
                
                item_name = metadata.get('name', md_file.stem)
                item_description = metadata.get('description', '')
                
                # Check if any part of the codex entry is mentioned in the text
                is_relevant = False
                
                # Check name
                if item_name.lower() in text_lower:
                    is_relevant = True
                
                # Check aliases/tags
                tags = metadata.get('tags', [])
                for tag in tags:
                    if tag.lower() in text_lower:
                        is_relevant = True
                        break
                
                # Check character-specific attributes
                if metadata.get('type') == 'character':
                    # Check occupation, personality keywords, etc.
                    for key in ['occupation', 'personality', 'voice']:
                        value = metadata.get(key, '')
                        if value and any(word.lower() in text_lower for word in value.split() if len(word) > 3):
                            is_relevant = True
                            break
                
                # Check location-specific attributes
                if metadata.get('type') == 'location':
                    location_type = metadata.get('location_type', '')
                    if location_type and location_type.lower() in text_lower:
                        is_relevant = True
                
                if is_relevant:
                    relevant_entries.append({
                        'id': md_file.stem,
                        'name': item_name,
                        'type': metadata.get('type', 'general'),
                        'description': item_description,
                        'metadata': metadata
                    })
                    
            except Exception as e:
                print(f"Error processing codex file {md_file}: {e}")
                continue
        
        return relevant_entries[:10]  # Limit to most relevant
        
    except Exception as e:
        print(f"Error getting relevant codex entries: {e}")
        return []


class CodexImprovementRequest(BaseModel):
    """Request for codex improvement recommendations."""
    codex_type: str = "all"  # 'characters', 'locations', 'world_rules', 'all'
    focus: str = "completeness"  # 'completeness', 'consistency', 'clarity'


class CodexImprovementResponse(BaseModel):
    """Response with codex improvement recommendations."""
    improvements: List[Dict[str, Any]]
    total: int
    codex_analyzed: int


@router.post("/codex-improvements", response_model=CodexImprovementResponse)
async def get_codex_improvements(
    request: CodexImprovementRequest,
    user: dict = Depends(get_current_user),
    llm_client: LLMClient = Depends(get_user_llm_client),
    db: Session = Depends(get_read_session)
):
    """Get AI recommendations for improving codex entries."""
    
    try:
        codex_dir = Path("data/codex")
        if not codex_dir.exists():
            return CodexImprovementResponse(
                improvements=[],
                total=0,
                codex_analyzed=0
            )
        
        # Check if user has configured their API key
        if not llm_client.api_key:
            # Return mock improvements if no API key
            return CodexImprovementResponse(
                improvements=[{
                    "codex_entry": "Sample Character",
                    "type": "character",
                    "improvement": "Add more detailed background information",
                    "priority": "medium",
                    "reason": "Character development would benefit from expanded history"
                }],
                total=1,
                codex_analyzed=1
            )
        
        # Analyze codex entries
        improvements = []
        codex_analyzed = 0
        
        for md_file in codex_dir.glob("*.md"):
            if md_file.name.startswith('.'):
                continue
                
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Parse frontmatter if present
                metadata = {}
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1]
                        metadata = yaml.safe_load(yaml_content) or {}
                
                item_name = metadata.get('name', md_file.stem)
                item_type = metadata.get('type', 'general')
                
                # Filter by type if specified
                if request.codex_type != "all" and item_type != request.codex_type:
                    continue
                
                codex_analyzed += 1
                
                # Use AI to analyze the codex entry
                system_prompt = f"""You are an expert story development assistant analyzing codex entries for improvement opportunities.
                Focus on {request.focus} improvements for {item_type} entries."""
                
                user_prompt = f"""
                Analyze this codex entry and suggest specific improvements:
                
                Name: {item_name}
                Type: {item_type}
                Content: {content}
                
                Provide improvement suggestions in JSON format:
                {{
                  "improvements": [
                    {{
                      "category": "description|details|consistency|relationships",
                      "suggestion": "specific improvement suggestion",
                      "priority": "high|medium|low",
                      "reason": "explanation of why this improvement is valuable"
                    }}
                  ]
                }}
                
                Focus on making the entry more complete, consistent, and useful for story development.
                """
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                # Get AI analysis
                llm_response = await llm_client.complete(
                    messages=messages,
                    model="anthropic/claude-3-sonnet",
                    temperature=0.3,
                    max_tokens=1000,
                    json_mode=True
                )
                
                analysis_data = json.loads(llm_response.content)
                entry_improvements = analysis_data.get("improvements", [])
                
                for improvement in entry_improvements:
                    improvements.append({
                        "codex_entry": item_name,
                        "type": item_type,
                        "file": md_file.name,
                        "category": improvement.get("category", "general"),
                        "suggestion": improvement.get("suggestion", ""),
                        "priority": improvement.get("priority", "medium"),
                        "reason": improvement.get("reason", "")
                    })
                    
            except Exception as e:
                print(f"Error analyzing codex file {md_file}: {e}")
                continue
        
        return CodexImprovementResponse(
            improvements=improvements,
            total=len(improvements),
            codex_analyzed=codex_analyzed
        )
        
    except Exception as e:
        return CodexImprovementResponse(
            improvements=[],
            total=0,
            codex_analyzed=0
        )
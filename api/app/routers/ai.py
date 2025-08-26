"""AI router for text analysis and recommendations."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import time
from sqlalchemy.orm import Session

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
    type: str  # 'grammar', 'style', 'clarity', 'tone'


class RecommendationsResponse(BaseModel):
    """Response containing AI recommendations."""
    recommendations: List[AIRecommendation]
    total: int
    processing_time: float


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
                processing_time=processing_time
            )
        
        # Use OpenRouter with user's API key for recommendations
        system_prompt = "You are an expert writing assistant that provides specific, actionable recommendations for improving manuscript text."
        
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
            "type": "grammar|style|clarity|tone"
          }}
        ]
        
        Only suggest changes that significantly improve the text. Focus on:
        - Grammar and syntax errors
        - Style and flow improvements
        - Clarity and readability
        - Tone and voice consistency
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
                type=rec.get("type", "style")
            ))
        
        processing_time = time.time() - start_time
        
        return RecommendationsResponse(
            recommendations=recommendations,
            total=len(recommendations),
            processing_time=processing_time
        )
        
    except Exception as e:
        # Fall back to mock recommendations if OpenAI fails
        mock_recommendations = generate_mock_recommendations(request.text)
        processing_time = time.time() - start_time
        
        return RecommendationsResponse(
            recommendations=mock_recommendations,
            total=len(mock_recommendations),
            processing_time=processing_time
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
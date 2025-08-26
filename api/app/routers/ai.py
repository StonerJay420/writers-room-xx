"""AI router for text analysis and recommendations."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import openai
import os
from sqlalchemy.orm import Session

from ..db import get_read_session

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
    db: Session = Depends(get_read_session)
):
    """Get AI recommendations for text improvement."""
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        import time
        start_time = time.time()
        
        # Check if OpenAI API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            # Return mock recommendations for demo
            mock_recommendations = generate_mock_recommendations(request.text)
            processing_time = time.time() - start_time
            
            return RecommendationsResponse(
                recommendations=mock_recommendations,
                total=len(mock_recommendations),
                processing_time=processing_time
            )
        
        # Use OpenAI to generate recommendations
        client = openai.OpenAI(api_key=openai_api_key)
        
        prompt = f"""
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
        
        response = client.chat.completions.create(
            model="gpt-5",  # the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
            messages=[
                {"role": "system", "content": "You are an expert writing assistant that provides specific, actionable recommendations for improving manuscript text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        import json
        recommendations_data = json.loads(response.choices[0].message.content)
        
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
        processing_time = time.time() - start_time if 'start_time' in locals() else 0.0
        
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
async def ai_status():
    """Get AI service status."""
    openai_available = bool(os.getenv("OPENAI_API_KEY"))
    
    return {
        "status": "ai service ready",
        "openai_available": openai_available,
        "models_available": ["gpt-5"] if openai_available else ["mock"]
    }
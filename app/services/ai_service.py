import json
import os
import httpx
from app.config import settings
from typing import Dict, Any, List

class AIService:
    def __init__(self):
        self.base_url = settings.openrouter_base_url
        self.api_key = settings.openrouter_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://replit.com",
            "X-Title": "Writers Room X",
            "Content-Type": "application/json"
        }
    
    async def generate_line_edits(self, text: str, style_guidelines: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Generate line editing suggestions for a scene"""
        
        system_prompt = """You are a professional line editor specializing in science fiction manuscripts. 
        Your task is to improve clarity, rhythm, and specificity while preserving the author's voice and all plot elements.
        
        Focus on:
        - Reducing redundancy
        - Improving sentence flow
        - Enhancing specificity
        - Maintaining consistent tone
        - Preserving all canon facts and character details
        
        Return your response as JSON with this structure:
        {
            "suggestions": [
                {
                    "line_number": 5,
                    "original": "original text",
                    "suggested": "improved text",
                    "rationale": "explanation for change"
                }
            ],
            "overall_rationale": "summary of editing approach",
            "style_notes": ["note1", "note2"]
        }"""
        
        user_prompt = f"""Please provide line editing suggestions for this scene:

{text}

Provide specific line-by-line suggestions that improve the prose quality while maintaining the author's voice."""

        try:
            response = await self._call_openrouter(system_prompt, user_prompt, settings.grim_editor_model)
            return json.loads(response)
        except Exception as e:
            return {"error": str(e), "suggestions": []}
    
    async def check_lore_consistency(self, text: str, codex_content: List[str]) -> Dict[str, Any]:
        """Check scene against codex for lore consistency"""
        
        codex_summary = "\n\n".join(codex_content[:5])  # Limit context
        
        system_prompt = """You are a lore archivist responsible for maintaining consistency in a science fiction universe.
        Review the scene text against the provided codex and identify any potential inconsistencies.
        
        Return your response as JSON:
        {
            "inconsistencies": [
                {
                    "issue": "description of problem",
                    "scene_reference": "relevant text from scene",
                    "codex_reference": "conflicting information from codex",
                    "severity": "low|medium|high",
                    "suggested_fix": "how to resolve"
                }
            ],
            "canon_references": [
                {
                    "scene_element": "element referenced",
                    "codex_source": "supporting codex information"
                }
            ]
        }"""
        
        user_prompt = f"""CODEX INFORMATION:
{codex_summary}

SCENE TO REVIEW:
{text}

Check for any lore inconsistencies and provide canon references for key elements."""

        try:
            response = await self._call_openrouter(system_prompt, user_prompt, settings.lore_archivist_model)
            return json.loads(response)
        except Exception as e:
            return {"error": str(e), "inconsistencies": [], "canon_references": []}
    
    async def _call_openrouter(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """Make OpenRouter API call with proper error handling"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                if not content:
                    raise Exception("Empty response from OpenRouter")
                return content
        except Exception as e:
            raise Exception(f"OpenRouter API error: {str(e)}")

ai_service = AIService()

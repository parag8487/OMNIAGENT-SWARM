"""
LLM Client Wrapper
Unifies calls using the OpenAI-compatible format.
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config


class LLMClient:
    """LLM Client"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.demo_mode = Config.DEMO_MODE
        
        # Provider priority: Gemini (if configured) > Generic LLM (DashScope/OpenAI)
        gemini_key = Config.GEMINI_API_KEY
        has_gemini = gemini_key and gemini_key != 'your_gemini_api_key_here'
        
        if api_key:
            # Explicit override — use exactly what was passed
            self.api_key = api_key
            self.base_url = base_url or Config.LLM_BASE_URL
            self.model = model or Config.LLM_MODEL_NAME
        elif has_gemini:
            # Gemini is configured — use it as primary
            self.api_key = gemini_key
            self.base_url = Config.GEMINI_BASE_URL
            self.model = model or Config.GEMINI_MODEL_NAME
            print(f"[LLMClient] Using Google Gemini: {self.model}")
        else:
            # Fallback to generic LLM config (DashScope, OpenAI, etc.)
            self.api_key = Config.LLM_API_KEY
            self.base_url = base_url or Config.LLM_BASE_URL
            self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key and not self.demo_mode:
            raise ValueError("No LLM API key configured. Set GEMINI_API_KEY or LLM_API_KEY in .env")
        
        if self.demo_mode:
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Send a chat request
        
        Args:
            messages: List of messages
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            response_format: Response format (e.g., JSON mode)
            
        Returns:
            Model response text
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        if self.demo_mode:
            # Mock reasoning if requested
            return "This is a simulated AI response for the OmniAgent Swarm. The swarm is coordinating based on simulated trends."

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        # Remove <think> content for models like MiniMax M2.5
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Send a chat request and return JSON
        
        Args:
            messages: List of messages
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            
        Returns:
            Parsed JSON object
        """
        if self.demo_mode:
            # Generic mock JSON for ontology/simulation
            return {
                "entity_types": [
                    {"name": "TechInfluencer", "description": "Key opinion leaders in the AI and technology space."},
                    {"name": "VentureCapitalist", "description": "High-net-worth individuals and firms shaping market trends."},
                    {"name": "PublicOfficial", "description": "Government representatives and policy makers."},
                    {"name": "NewsOutlet", "description": "Media organizations broadcasting narrative updates."},
                    {"name": "ConsumerSegment", "description": "Aggregated groups of end-users with specific behaviors."}
                ],
                "edge_types": [
                    {"name": "ENDORSES", "description": "Expressing formal support or valid adoption."},
                    {"name": "CRITICIZES", "description": "Highlighting risks, failures, or ethical concerns."},
                    {"name": "INVESTS_IN", "description": "Allocating capital or resources to a specific entity."},
                    {"name": "INFLUENCES", "description": "Shaping the public perception or behavior of another node."},
                    {"name": "REPORTS_ON", "description": "Providing factual coverage of events or node activities."}
                ],
                "analysis_summary": "Simulation scenario initialized: OmniAgent Swarm scaling across global tech markets. High-fidelity narrative tracking active."
            }

        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        # Clean markdown code block markers
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format returned by LLM: {cleaned_response}")

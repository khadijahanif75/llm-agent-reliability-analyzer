import json
import os
from typing import Any, Dict, List, Optional
from agent.llm_client import BaseLLMProvider
from tracing.models import LLMAction

class RealLLMProvider(BaseLLMProvider):
    """
    Real LLM Provider supporting OpenAI structured function calling API.
    Can be easily extended for Gemini or Claude.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o-mini"):
        super().__init__(model_name=model_name)
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        
    def decide(
        self,
        user_prompt: str,
        history: List[Dict[str, Any]]
    ) -> LLMAction:
        if not self.api_key:
            raise ValueError("API Key missing! Pass LLM_API_KEY env variable or use MockLLMProvider.")

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            messages = [
                {"role": "system", "content": (
                    "You are a helpful AI agent with access to tools: 'calculator', 'search', and 'database'. "
                    "Decide whether to call a tool or return the final answer. "
                    "Respond ONLY with a JSON object matching this schema: "
                    '{"action": "calculator|search|database|final_answer", "arguments": {...}, "final_answer": "..."}'
                )},
                {"role": "user", "content": user_prompt}
            ]
            
            # Append observation history
            for item in history:
                if item.get("event") == "OBSERVATION":
                    messages.append({
                        "role": "function",
                        "name": item.get("tool_name", "tool"),
                        "content": json.dumps(item.get("output"))
                    })

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            return LLMAction(
                action=parsed.get("action", "final_answer"),
                arguments=parsed.get("arguments", {}),
                final_answer=parsed.get("final_answer")
            )
            
        except Exception as e:
            # Fallback safe error response
            return LLMAction(
                action="final_answer",
                arguments={},
                final_answer=f"Error interacting with LLM API: {str(e)}"
            )
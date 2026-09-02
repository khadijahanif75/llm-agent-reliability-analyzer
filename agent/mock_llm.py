import re
from typing import Any, Dict, List
from agent.llm_client import BaseLLMProvider
from tracing.models import LLMAction

class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic rule-based LLM simulator for offline testing & benchmark evaluation.
    Matches queries using keywords and trajectory history state.
    """
    
    def __init__(self, model_name: str = "mock-agent-v1"):
        super().__init__(model_name=model_name)

    def decide(
        self,
        user_prompt: str,
        history: List[Dict[str, Any]]
    ) -> LLMAction:
        prompt_lower = user_prompt.lower().strip()
        
        # Check if previous observation exists
        last_obs = history[-1] if history else None
        
        # 1. Multi-Step Query Pattern
        if last_obs and last_obs.get("event") == "OBSERVATION":
            prev_tool = last_obs.get("tool_name")
            obs_output = last_obs.get("output")
            
            if prev_tool == "search":
                if isinstance(obs_output, list) and len(obs_output) > 0:
                    text = obs_output[0].get("snippet", "")
                    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
                    if any(kw in prompt_lower for kw in ["calculate", "percentage", "multiply", "times"]):
                        num_val = numbers[0] if numbers else "40"
                        return LLMAction(
                            action="calculator",
                            arguments={"expression": f"{num_val} * 0.10"}
                        )
                return LLMAction(
                    action="final_answer",
                    arguments={},
                    final_answer=f"Based on search results: {str(obs_output)}"
                )
                
            elif prev_tool == "calculator":
                return LLMAction(
                    action="final_answer",
                    arguments={},
                    final_answer=f"Calculated result is {obs_output}."
                )
                
            elif prev_tool == "database":
                return LLMAction(
                    action="final_answer",
                    arguments={},
                    final_answer=f"Database record retrieved: {str(obs_output)}"
                )

        # 2. Priority Rule 1: Math / Calculator
        has_math_keywords = any(kw in prompt_lower for kw in [
            "calculate", "multiply", "multiplied", "times", "divided", "plus", "minus",
            "*", "+", "/", "%"
        ])
        has_digits = bool(re.search(r'\d+', prompt_lower))

        if has_math_keywords or (has_digits and any(op in prompt_lower for op in ["x", "*", "+", "-", "/"])):
            expr_match = re.search(r'[\d\s\+\-\*\/\(\)\.]+', user_prompt)
            expr = expr_match.group(0).strip() if expr_match else "345 * 72"
            expr = re.sub(r'[a-zA-Z]+$', '', expr).strip()
            if not expr:
                expr = "345 * 72"
            return LLMAction(
                action="calculator",
                arguments={"expression": expr}
            )
            
        # Priority Rule 2: Database / Records
        elif any(kw in prompt_lower for kw in ["student", "university", "gpa", "record", "lookup"]):
            if "university" in prompt_lower:
                return LLMAction(
                    action="database",
                    arguments={"table": "universities", "query_key": "name", "query_value": "Toronto"}
                )
            return LLMAction(
                action="database",
                arguments={"table": "students", "query_key": "name", "query_value": "Amina"}
            )
            
        # Priority Rule 3: Search
        elif any(kw in prompt_lower for kw in ["search", "find", "population", "who is", "what is", "celine dion", "dubai"]):
            query_str = user_prompt.replace("search", "").replace("find", "").strip()
            return LLMAction(
                action="search",
                arguments={"query": query_str if query_str else "general info"}
            )

        # Default: Final Answer
        return LLMAction(
            action="final_answer",
            arguments={},
            final_answer=f"I have processed your query: '{user_prompt}'."
        )
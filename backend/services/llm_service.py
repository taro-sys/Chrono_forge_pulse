"""LLM Service - Routes requests between Ollama (primary) and Claude (secondary)"""
import os
import json
import anthropic
from typing import Dict, Any, Optional
from datetime import datetime


class LLMService:
    """Manages LLM inference with intelligent routing"""
    
    def __init__(self):
        # Claude setup
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = None
        if self.anthropic_key:
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.anthropic_key)
                print("✓ Claude (Anthropic) client initialized")
            except Exception as e:
                print(f"⚠ Claude initialization failed: {e}")
        
        # Ollama setup
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.ollama_available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available"""
        try:
            import requests
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                print(f"✓ Ollama is available at {self.ollama_base_url}")
                return True
        except:
            print(f"⚠ Ollama not available at {self.ollama_base_url}")
        return False
    
    def calculate_complexity_score(self, task_type: str, context_length: int = 0) -> float:
        """Calculate task complexity score (0-1)"""
        complexity_map = {
            "simple_query": 0.2,
            "summary": 0.3,
            "data_description": 0.3,
            "forecast_explanation": 0.8,
            "risk_assessment": 0.8,
            "pattern_analysis": 0.7,
            "recommendation": 0.6
        }
        
        base_score = complexity_map.get(task_type, 0.5)
        
        # Adjust for context length
        if context_length > 2000:
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def select_llm(self, task_type: str, use_claude: bool = False, context_length: int = 0) -> str:
        """Select appropriate LLM based on task complexity"""
        # Force Claude if requested and available
        if use_claude and self.claude_client:
            return "claude"
        
        # Calculate complexity
        complexity = self.calculate_complexity_score(task_type, context_length)
        
        # Complex tasks -> Claude (if available)
        if complexity > 0.7 and self.claude_client:
            return "claude"
        
        # Simple tasks -> Ollama (if available)
        if self.ollama_available:
            return "ollama"
        
        # Fallback to Claude if Ollama not available
        if self.claude_client:
            return "claude"
        
        # No LLM available
        return "none"
    
    def generate_with_ollama(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generate response using Ollama"""
        try:
            import requests
            
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result.get("response", ""),
                    "model": f"ollama-{self.ollama_model}",
                    "tokens": result.get("eval_count", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"Ollama returned status {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Ollama error: {str(e)}"
            }
    
    def generate_with_claude(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generate response using Claude"""
        try:
            if not self.claude_client:
                return {
                    "success": False,
                    "error": "Claude client not initialized"
                }
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                temperature=0.7,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return {
                "success": True,
                "text": response.content[0].text,
                "model": "claude-3-5-sonnet",
                "tokens": response.usage.output_tokens
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Claude error: {str(e)}"
            }
    
    def generate(self, prompt: str, task_type: str = "simple_query", 
                 system_prompt: str = "", use_claude: bool = False) -> Dict[str, Any]:
        """Generate response with automatic LLM routing"""
        context_length = len(prompt)
        selected_llm = self.select_llm(task_type, use_claude, context_length)
        
        if selected_llm == "ollama":
            result = self.generate_with_ollama(prompt, system_prompt)
        elif selected_llm == "claude":
            result = self.generate_with_claude(prompt, system_prompt)
        else:
            result = {
                "success": False,
                "error": "No LLM available",
                "text": "LLM service unavailable. Please configure Ollama or Claude."
            }
        
        result["selected_llm"] = selected_llm
        return result
    
    def explain_forecast(self, forecast_data: Dict[str, Any], use_claude: bool = False) -> str:
        """Generate forecast explanation"""
        prompt = f"""Analyze this demand forecast:

Predictions: {forecast_data.get('predictions', [])}
Model Used: {forecast_data.get('model_used', 'unknown')}
Metrics: {json.dumps(forecast_data.get('metrics', {}), indent=2)}
Confidence Intervals: {json.dumps(forecast_data.get('confidence_intervals', {}), indent=2)}

Provide a concise explanation of:
1. What the forecast indicates
2. Confidence level and reliability
3. Key insights for decision-making
"""
        
        system_prompt = """You are a sales forecasting expert. Provide clear, actionable insights 
from forecast data. Be concise and focus on business implications."""
        
        result = self.generate(prompt, "forecast_explanation", system_prompt, use_claude)
        
        if result["success"]:
            return result["text"]
        else:
            return f"Explanation unavailable: {result.get('error', 'Unknown error')}"
    
    def assess_risk(self, forecast_data: Dict[str, Any], historical_context: str = "", 
                    use_claude: bool = False) -> str:
        """Generate risk assessment"""
        prompt = f"""Assess risks for this demand forecast:

Predictions: {forecast_data.get('predictions', [])}
Model: {forecast_data.get('model_used', 'unknown')}
Metrics: {json.dumps(forecast_data.get('metrics', {}))}

{f'Historical Context: {historical_context}' if historical_context else ''}

Identify:
1. Potential risks (supply, demand, external factors)
2. Confidence level concerns
3. Mitigation strategies
"""
        
        system_prompt = """You are a risk analyst specializing in supply chain and demand forecasting. 
Provide practical risk assessments and mitigation strategies."""
        
        result = self.generate(prompt, "risk_assessment", system_prompt, use_claude)
        
        if result["success"]:
            return result["text"]
        else:
            return f"Risk assessment unavailable: {result.get('error', 'Unknown error')}"

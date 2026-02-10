"""RAG Service - Integrates with existing ChronoForge RAG system"""
import sys
import os
from typing import List, Dict, Any
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import LLMService
from services.llm_service import LLMService

# Try to import RAG components (optional)
RAGQuery = None
RAGConfig = None
LLMConfig = None
RAGPipelineBuilder = None

try:
    from chronoforge_rag import RAGQuery, RAGConfig, LLMConfig
    from rag_pipeline import RAGPipelineBuilder
except ImportError as e:
    print(f"Warning: RAG imports failed: {e}")
    print("RAG features will be limited. Build knowledge base to enable full RAG.")


class RAGService:
    """RAG query service integrating existing ChronoForge RAG"""
    
    def __init__(self, kb_path: str = "../kb"):
        self.kb_path = kb_path
        self.pipeline = None
        self.llm_service = LLMService()
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize RAG pipeline if knowledge base exists"""
        try:
            if not RAGPipelineBuilder:
                print(f"⚠ RAG modules not available. Install dependencies and build knowledge base.")
                return
                
            if os.path.exists(self.kb_path):
                # Build pipeline with mock LLM (we'll use our LLM service instead)
                builder = RAGPipelineBuilder()
                builder.with_llm_config(LLMConfig(provider="mock"))
                self.pipeline = builder.build_with_knowledge_base(self.kb_path)
                print(f"✓ RAG pipeline initialized with knowledge base: {self.kb_path}")
            else:
                print(f"⚠ Knowledge base not found at {self.kb_path}")
        except Exception as e:
            print(f"⚠ Failed to initialize RAG pipeline: {e}")
    
    def query(self, question: str, use_claude: bool = False, 
              top_k: int = 5, region_filter: str = None, 
              category_filter: str = None) -> Dict[str, Any]:
        """Query the knowledge base with RAG"""
        try:
            if not self.pipeline or not RAGQuery:
                # Fallback: use LLM directly without RAG
                prompt = f"Answer this question about sales forecasting: {question}"
                system_prompt = "You are a sales forecasting analyst."
                result = self.llm_service.generate(prompt, "simple_query", system_prompt, use_claude)
                
                return {
                    "success": True,
                    "query_id": str(uuid.uuid4()),
                    "question": question,
                    "answer": result["text"] if result["success"] else "RAG not available. Build knowledge base to enable full RAG features.",
                    "sources": [],
                    "llm_used": result.get("model", "none"),
                    "created_at": datetime.utcnow().isoformat(),
                    "note": "RAG pipeline not initialized"
                }
            
            # Create RAG query
            rag_query = RAGQuery(
                query_text=question,
                top_k=top_k,
                region_filter=region_filter,
                category_filter=category_filter
            )
            
            # Search knowledge base
            kb = self.pipeline.get_knowledge_base()
            search_results = kb.search(rag_query)
            
            # Format sources
            sources = []
            context_docs = []
            
            for result in search_results:
                s = result.scenario
                source = {
                    "date": s.date,
                    "description": s.description,
                    "sales_value": s.sales_value,
                    "region": s.region,
                    "category": s.category,
                    "similarity_score": result.similarity_score
                }
                sources.append(source)
                context_docs.append(
                    f"{s.date}: {s.description} [Sales: ${s.sales_value:,.2f}, Region: {s.region}]"
                )
            
            # Generate answer using LLM
            if context_docs:
                prompt = f"""Based on the following historical sales scenarios, answer this question:

Question: {question}

Historical Context:
{chr(10).join(['- ' + doc for doc in context_docs])}

Provide a clear, concise answer based on the historical patterns."""
                
                system_prompt = """You are a sales forecasting analyst. Use historical data to provide 
insightful answers about sales patterns, trends, and forecasting."""
                
                task_type = "simple_query" if len(question) < 50 else "pattern_analysis"
                result = self.llm_service.generate(prompt, task_type, system_prompt, use_claude)
                
                if result["success"]:
                    answer = result["text"]
                    llm_used = result["model"]
                else:
                    answer = "Unable to generate answer: " + result.get("error", "Unknown error")
                    llm_used = "none"
            else:
                answer = "No relevant historical data found for this query."
                llm_used = "none"
            
            return {
                "success": True,
                "query_id": str(uuid.uuid4()),
                "question": question,
                "answer": answer,
                "sources": sources,
                "llm_used": llm_used,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def explain_forecast_with_context(self, forecast_data: Dict[str, Any], 
                                     use_claude: bool = False) -> Dict[str, Any]:
        """Explain forecast using historical context from RAG"""
        try:
            if not self.pipeline:
                # Fallback to simple explanation without RAG
                explanation = self.llm_service.explain_forecast(forecast_data, use_claude)
                return {
                    "success": True,
                    "explanation": explanation,
                    "sources": [],
                    "llm_used": "claude" if use_claude else "ollama"
                }
            
            # Search for similar historical patterns
            avg_prediction = sum(forecast_data.get("predictions", [0])) / len(forecast_data.get("predictions", [1]))
            query_text = f"Sales around ${avg_prediction:.0f} with similar patterns"
            
            rag_query = RAGQuery(query_text=query_text, top_k=3)
            kb = self.pipeline.get_knowledge_base()
            search_results = kb.search(rag_query)
            
            # Format historical context
            context_docs = []
            sources = []
            for result in search_results:
                s = result.scenario
                context_docs.append(
                    f"{s.date}: {s.description} [Sales: ${s.sales_value:,.2f}]"
                )
                sources.append({
                    "date": s.date,
                    "description": s.description,
                    "sales_value": s.sales_value
                })
            
            # Generate explanation with historical context
            prompt = f"""Explain this demand forecast using historical patterns:

Forecast:
- Predictions: {forecast_data.get('predictions', [])}
- Model: {forecast_data.get('model_used', 'unknown')}
- Metrics: MAPE={forecast_data.get('metrics', {}).get('mape', 0):.2f}%, RMSE={forecast_data.get('metrics', {}).get('rmse', 0):.2f}

Similar Historical Patterns:
{chr(10).join(['- ' + doc for doc in context_docs]) if context_docs else 'No similar patterns found'}

Provide:
1. Forecast interpretation
2. Comparison with historical patterns
3. Confidence assessment
4. Actionable insights
"""
            
            system_prompt = """You are a sales forecasting expert. Explain forecasts clearly using 
historical context and provide actionable business insights."""
            
            result = self.llm_service.generate(prompt, "forecast_explanation", system_prompt, use_claude)
            
            explanation = result["text"] if result["success"] else "Unable to generate explanation"
            
            return {
                "success": True,
                "explanation": explanation,
                "sources": sources,
                "llm_used": result.get("model", "none")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            if not self.pipeline:
                return {
                    "success": False,
                    "error": "Knowledge base not initialized"
                }
            
            kb = self.pipeline.get_knowledge_base()
            stats = kb.get_statistics()
            
            return {
                "success": True,
                "total_scenarios": stats.total_scenarios,
                "unique_regions": stats.unique_regions,
                "unique_categories": stats.unique_categories,
                "min_sales_value": stats.min_sales_value,
                "max_sales_value": stats.max_sales_value,
                "avg_sales_value": stats.avg_sales_value,
                "earliest_date": stats.earliest_date,
                "latest_date": stats.latest_date
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

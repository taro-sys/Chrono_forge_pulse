"""RAG query API routes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from models.db_models import RAGQueryRequest
from services.rag_service import RAGService

router = APIRouter(prefix="/api/rag", tags=["rag"])

# Initialize service
rag_service = RAGService()


@router.post("/query")
async def query_knowledge_base(request: RAGQueryRequest) -> Dict[str, Any]:
    """
    Query the knowledge base using RAG
    
    - **question**: Natural language question
    - **use_claude**: Use Claude for answer generation (default: False, uses Ollama)
    - **top_k**: Number of similar scenarios to retrieve (default: 5)
    - **region_filter**: Optional region filter
    - **category_filter**: Optional category filter
    """
    try:
        result = rag_service.query(
            question=request.question,
            use_claude=request.use_claude,
            top_k=request.top_k,
            region_filter=request.region_filter,
            category_filter=request.category_filter
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Query failed"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain-forecast")
async def explain_forecast(forecast_data: Dict[str, Any], use_claude: bool = False) -> Dict[str, Any]:
    """
    Explain forecast using historical context from RAG
    
    - **forecast_data**: Forecast result data
    - **use_claude**: Use Claude for explanation (default: False)
    """
    try:
        result = rag_service.explain_forecast_with_context(forecast_data, use_claude)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Explanation failed"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/stats")
async def get_knowledge_base_stats() -> Dict[str, Any]:
    """
    Get statistics about the knowledge base
    """
    try:
        result = rag_service.get_knowledge_base_stats()
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get stats"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

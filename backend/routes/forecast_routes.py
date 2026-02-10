"""Forecast API routes"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import numpy as np

from models.db_models import (
    ForecastRequest, 
    LotSizingRequest, 
    ProductionScheduleRequest, 
    MaterialsRequest
)
from services.forecast_service import ForecastService

router = APIRouter(prefix="/api/forecast", tags=["forecast"])

# Initialize service
forecast_service = ForecastService()


@router.post("/demand")
async def forecast_demand(request: ForecastRequest) -> Dict[str, Any]:
    """
    Generate demand forecast using ensemble models with auto-selection
    
    - **data**: Historical sales data (list of floats)
    - **model**: Model to use (auto, lstm, arima, xgboost, lightgbm, prophet)
    - **horizon**: Number of periods to forecast (default: 7)
    - **confidence_level**: Confidence level for intervals (default: 0.95)
    - **use_claude**: Use Claude for explanation (default: False, uses Ollama)
    """
    try:
        result = forecast_service.forecast_demand(request)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Forecast failed"))
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lot-sizing")
async def calculate_lot_sizing(request: LotSizingRequest) -> Dict[str, Any]:
    """
    Calculate optimal lot sizing (STUB - v1)
    
    Uses EOQ (Economic Order Quantity) and Wagner-Whitin Algorithm
    """
    # STUB implementation
    total_demand = sum(request.demand_forecast)
    avg_demand = total_demand / len(request.demand_forecast)
    
    # Simple EOQ calculation
    eoq = np.sqrt((2 * total_demand * request.ordering_cost) / request.holding_cost)
    
    return {
        "success": True,
        "method": "EOQ",
        "economic_order_quantity": float(eoq),
        "total_demand": float(total_demand),
        "average_demand": float(avg_demand),
        "ordering_cost": request.ordering_cost,
        "holding_cost": request.holding_cost,
        "note": "STUB: Full implementation coming in v2"
    }


@router.post("/production-schedule")
async def optimize_production_schedule(request: ProductionScheduleRequest) -> Dict[str, Any]:
    """
    Optimize production schedule (STUB - v1)
    
    Uses MHP (Material Handling Planning) and Genetic Algorithm
    """
    # STUB implementation
    total_demand = sum(request.demand_forecast)
    
    # Simple schedule: distribute evenly
    schedule = [min(request.capacity, d) for d in request.demand_forecast]
    utilization = (sum(schedule) / (request.capacity * len(schedule))) * 100
    
    return {
        "success": True,
        "method": "MHP",
        "production_schedule": schedule,
        "capacity_utilization": float(utilization),
        "total_production": float(sum(schedule)),
        "capacity": request.capacity,
        "note": "STUB: Full MHP and Genetic Algorithm implementation coming in v2"
    }


@router.post("/materials-acquisition")
async def plan_materials_acquisition(request: MaterialsRequest) -> Dict[str, Any]:
    """
    Plan materials acquisition (STUB - v1)
    
    Uses Regression Analysis and MRP (Material Requirements Planning)
    """
    # STUB implementation
    total_production = sum(request.production_schedule)
    
    # Simple MRP: add safety stock and lead time buffer
    materials_needed = [p + request.safety_stock for p in request.production_schedule]
    
    # Account for lead time
    order_schedule = [0] * request.lead_time + materials_needed[:-request.lead_time]
    
    return {
        "success": True,
        "method": "MRP",
        "materials_schedule": materials_needed,
        "order_schedule": order_schedule,
        "total_materials": float(total_production + request.safety_stock * len(materials_needed)),
        "lead_time_days": request.lead_time,
        "safety_stock": request.safety_stock,
        "note": "STUB: Full MRP and Regression Analysis implementation coming in v2"
    }


@router.get("/models/status")
async def get_models_status() -> Dict[str, Any]:
    """
    Get status of all forecasting models
    """
    try:
        models_available = {
            "lstm": forecast_service.models.models_loaded,
            "arima": True,  # statsmodels always available
            "xgboost": True,
            "lightgbm": True,
            "prophet": True
        }
        
        return {
            "success": True,
            "models_available": models_available,
            "pretrained_loaded": forecast_service.models.models_loaded,
            "auto_selection_enabled": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

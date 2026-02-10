"""Database models for MongoDB collections"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ModelType(str, Enum):
    """Available forecasting models"""
    AUTO = "auto"
    LSTM = "lstm"
    ARIMA = "arima"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    PROPHET = "prophet"


class TaskStatus(str, Enum):
    """Background task status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SalesDataPoint(BaseModel):
    """Single sales data point"""
    date: str
    sales_value: float
    region: Optional[str] = None
    category: Optional[str] = None
    promotion: Optional[int] = None
    competitor_action: Optional[int] = None
    weather_condition: Optional[str] = None
    seasonality: Optional[str] = None
    epidemic_flag: Optional[int] = None
    description: Optional[str] = None


class SalesDataset(BaseModel):
    """Sales dataset stored in MongoDB"""
    id: str = Field(alias="_id")
    name: str
    data: List[SalesDataPoint]
    uploaded_at: datetime
    record_count: int
    metadata: Dict[str, Any] = {}

    class Config:
        populate_by_name = True


class ForecastRequest(BaseModel):
    """Request for demand forecasting"""
    data: Optional[List[float]] = None
    dataset_id: Optional[str] = None
    model: ModelType = ModelType.AUTO
    horizon: int = 7
    confidence_level: float = 0.95
    use_claude: bool = False


class ForecastResult(BaseModel):
    """Forecast result"""
    id: str = Field(alias="_id")
    dataset_id: Optional[str] = None
    model_used: str
    predictions: List[float]
    confidence_intervals: Dict[str, List[float]]
    metrics: Dict[str, float]
    feature_importance: List[Dict[str, Any]] = []
    llm_explanation: str = ""
    llm_used: str = ""
    created_at: datetime

    class Config:
        populate_by_name = True


class TrainingJob(BaseModel):
    """Background training job"""
    id: str = Field(alias="_id")
    dataset_id: str
    status: TaskStatus
    model_results: Dict[str, Dict[str, float]] = {}
    best_model: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class RAGQueryRequest(BaseModel):
    """RAG query request"""
    question: str
    use_claude: bool = False
    top_k: int = 5
    region_filter: Optional[str] = None
    category_filter: Optional[str] = None


class RAGQueryResult(BaseModel):
    """RAG query result"""
    id: str = Field(alias="_id")
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    llm_used: str
    created_at: datetime

    class Config:
        populate_by_name = True


# Stub models for future features
class LotSizingRequest(BaseModel):
    """Lot sizing calculation request (STUB)"""
    demand_forecast: List[float]
    holding_cost: float = 1.0
    ordering_cost: float = 100.0


class ProductionScheduleRequest(BaseModel):
    """Production schedule optimization request (STUB)"""
    demand_forecast: List[float]
    capacity: float = 1000.0
    resource_constraints: Dict[str, float] = {}


class MaterialsRequest(BaseModel):
    """Materials acquisition request (STUB)"""
    production_schedule: List[float]
    lead_time: int = 7
    safety_stock: float = 100.0

"""
ChronoForge Pulse RAG System - Core Types and Interfaces

Retrieval-Augmented Generation system for sales forecasting.
Python implementation using APIs for embeddings and LLM.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
from abc import ABC, abstractmethod
from datetime import datetime
import time

# =============================================================================
# Configuration Constants
# =============================================================================

DEFAULT_EMBEDDING_DIM = 384  # all-MiniLM-L6-v2
DEFAULT_TOP_K = 5
DEFAULT_CONTEXT_WINDOW = 4096
DEFAULT_TEMPERATURE = 0.7

# =============================================================================
# Core Data Structures
# =============================================================================

@dataclass
class SalesScenario:
    """Represents a single sales scenario/event in the knowledge base."""
    id: str
    date: str
    description: str
    
    # Sales metrics
    sales_value: float = 0.0
    sales_change_pct: float = 0.0
    predicted_value: float = 0.0
    prediction_error: float = 0.0
    
    # Context features
    region: str = ""
    category: str = ""
    had_promotion: bool = False
    had_competitor_action: bool = False
    weather_condition: str = ""
    seasonality: str = ""
    epidemic_flag: bool = False
    
    # Embedding (populated by embedding engine)
    embedding: List[float] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "date": self.date,
            "description": self.description,
            "sales_value": self.sales_value,
            "sales_change_pct": self.sales_change_pct,
            "predicted_value": self.predicted_value,
            "prediction_error": self.prediction_error,
            "region": self.region,
            "category": self.category,
            "had_promotion": self.had_promotion,
            "had_competitor_action": self.had_competitor_action,
            "weather_condition": self.weather_condition,
            "seasonality": self.seasonality,
            "epidemic_flag": self.epidemic_flag,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SalesScenario":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            date=data.get("date", ""),
            description=data.get("description", ""),
            sales_value=float(data.get("sales_value", 0)),
            sales_change_pct=float(data.get("sales_change_pct", 0)),
            predicted_value=float(data.get("predicted_value", 0)),
            prediction_error=float(data.get("prediction_error", 0)),
            region=data.get("region", ""),
            category=data.get("category", ""),
            had_promotion=bool(data.get("had_promotion", False)),
            had_competitor_action=bool(data.get("had_competitor_action", False)),
            weather_condition=data.get("weather_condition", ""),
            seasonality=data.get("seasonality", ""),
            epidemic_flag=bool(data.get("epidemic_flag", False)),
            metadata=data.get("metadata", {})
        )


@dataclass
class RetrievalResult:
    """Result from vector similarity search."""
    scenario: SalesScenario
    similarity_score: float  # cosine similarity [0, 1]
    rank: int  # position in results


@dataclass
class RAGQuery:
    """Query context for RAG pipeline."""
    query_text: str
    
    # Optional filters
    region_filter: Optional[str] = None
    category_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    
    # Current forecast context (from ChronoForge Pulse)
    current_prediction: Optional[float] = None
    current_confidence: Optional[float] = None
    feature_importance: Optional[List[Tuple[str, float]]] = None
    
    # Retrieval settings
    top_k: int = DEFAULT_TOP_K


@dataclass
class RAGResponse:
    """Complete RAG response."""
    generated_text: str
    sources: List[RetrievalResult] = field(default_factory=list)
    
    # Performance metrics
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    total_time_ms: float = 0.0
    
    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class ForecastData:
    """Forecast data from ChronoForge Pulse models."""
    date: str
    sarima_prediction: float = 0.0
    lstm_prediction: float = 0.0
    xgb_prediction: float = 0.0
    lgb_prediction: float = 0.0
    ensemble_prediction: float = 0.0
    confidence_interval_low: float = 0.0
    confidence_interval_high: float = 0.0
    
    # Feature contributions
    feature_importance: List[Tuple[str, float]] = field(default_factory=list)


# =============================================================================
# Configuration Structures
# =============================================================================

@dataclass
class EmbeddingConfig:
    """Configuration for embedding engine."""
    model_name: str = "all-MiniLM-L6-v2"  # sentence-transformers model
    dimension: int = DEFAULT_EMBEDDING_DIM
    use_api: bool = False  # If True, use API (OpenAI/Gemini) instead of local
    api_key: Optional[str] = None
    api_provider: str = "openai"  # "openai" or "gemini"


@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""
    dimension: int = DEFAULT_EMBEDDING_DIM
    persist_directory: str = "./chroma_db"
    collection_name: str = "sales_scenarios"


@dataclass
class LLMConfig:
    """Configuration for LLM."""
    provider: str = "openai"  # "gemini", "openai", "anthropic"
    api_key: Optional[str] = None
    model_name: str = "gpt-4o"  # or "gpt-4o-mini", "claude-3-haiku"
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = 1024


@dataclass
class RAGConfig:
    """Complete RAG configuration."""
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    default_top_k: int = DEFAULT_TOP_K
    min_similarity_threshold: float = 0.3
    
    system_prompt: str = """You are ChronoForge Pulse AI, an expert sales forecasting analyst.
Your job is to analyze historical sales patterns and explain forecasting predictions.

When given retrieved scenarios and a current forecast, you should:
1. Identify patterns from similar historical situations
2. Explain why the forecast might be accurate or need adjustment
3. Highlight key factors that drove past outcomes
4. Provide actionable insights for business decisions

Be concise, data-driven, and always reference the specific scenarios you're drawing from."""


# =============================================================================
# Abstract Interfaces
# =============================================================================

class IEmbeddingEngine(ABC):
    """Interface for embedding generation."""
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass


class IVectorStore(ABC):
    """Interface for vector storage and retrieval."""
    
    @abstractmethod
    def add(self, id: str, embedding: List[float], metadata: Dict[str, Any] = None):
        """Add a single vector."""
        pass
    
    @abstractmethod
    def add_batch(self, ids: List[str], embeddings: List[List[float]], 
                  metadatas: List[Dict[str, Any]] = None):
        """Add multiple vectors."""
        pass
    
    @abstractmethod
    def search(self, query: List[float], k: int) -> List[Tuple[str, float]]:
        """Search for similar vectors. Returns (id, distance) pairs."""
        pass
    
    @abstractmethod
    def save(self, path: str):
        """Persist the vector store."""
        pass
    
    @abstractmethod
    def load(self, path: str):
        """Load from persisted storage."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get number of vectors."""
        pass


class ILLMEngine(ABC):
    """Interface for LLM inference."""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 512, 
                 temperature: float = DEFAULT_TEMPERATURE) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def set_system_prompt(self, prompt: str):
        """Set the system prompt."""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token count."""
        pass


class IKnowledgeBase(ABC):
    """Interface for knowledge base operations."""
    
    @abstractmethod
    def add_scenario(self, scenario: SalesScenario):
        """Add a single scenario."""
        pass
    
    @abstractmethod
    def add_scenarios(self, scenarios: List[SalesScenario]):
        """Add multiple scenarios."""
        pass
    
    @abstractmethod
    def get_scenario(self, id: str) -> Optional[SalesScenario]:
        """Get scenario by ID."""
        pass
    
    @abstractmethod
    def search(self, query: RAGQuery) -> List[RetrievalResult]:
        """Search for similar scenarios."""
        pass
    
    @abstractmethod
    def save(self, path: str):
        """Save knowledge base."""
        pass
    
    @abstractmethod
    def load(self, path: str):
        """Load knowledge base."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get number of scenarios."""
        pass


# =============================================================================
# Utility Functions
# =============================================================================

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0
    
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot / (norm_a * norm_b)


def get_time_ms() -> float:
    """Get current timestamp in milliseconds."""
    return time.time() * 1000


def format_scenario_for_prompt(scenario: SalesScenario) -> str:
    """Format a scenario for inclusion in LLM prompt."""
    parts = [
        f"**Date**: {scenario.date}",
        f"**Region**: {scenario.region} | **Category**: {scenario.category}",
        f"**Sales**: ${scenario.sales_value:,.2f}",
        f"**Description**: {scenario.description}",
    ]
    
    factors = []
    if scenario.had_promotion:
        factors.append("Had Promotion")
    if scenario.had_competitor_action:
        factors.append("Competitor Action")
    if scenario.weather_condition:
        factors.append(f"Weather: {scenario.weather_condition}")
    if scenario.seasonality:
        factors.append(f"Season: {scenario.seasonality}")
    
    if factors:
        parts.append(f"**Factors**: {', '.join(factors)}")
    
    if scenario.prediction_error != 0:
        parts.append(f"**Prediction Error**: ${scenario.prediction_error:,.2f}")
    
    return "\n".join(parts)

# ChronoForge Pulse RAG System (Python Edition)

A Python Retrieval-Augmented Generation (RAG) system for sales forecasting analysis. This is a port of the C++ ChronoForge RAG system, designed to use cloud APIs for embeddings and LLM inference.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  ChronoForge Pulse RAG (Python)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   Query      │────▶│  Embedding   │────▶│   Vector     │   │
│  │   Input      │     │   Engine     │     │   Store      │   │
│  └──────────────┘     │ (Sentence    │     │  (ChromaDB)  │   │
│                       │ Transformers)│     └──────┬───────┘   │
│                       └──────────────┘            │            │
│  ┌──────────────┐     ┌──────────────┐           │            │
│  │   Response   │◀────│    LLM       │◀──────────┘            │
│  │   Output     │     │  (Gemini/    │   Retrieved            │
│  └──────────────┘     │   OpenAI/    │   Scenarios            │
│                       │   Claude)    │                         │
│                       └──────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Pure Python Implementation**: Easy to install and modify
- **Multiple LLM Providers**: Gemini, OpenAI GPT-4, Anthropic Claude
- **Flexible Embeddings**: Local (sentence-transformers) or API (OpenAI/Gemini)
- **Persistent Vector Store**: ChromaDB with automatic persistence
- **Sales-Specific Knowledge Base**: Optimized for forecasting scenarios
- **Multiple Query Modes**:
  - Free-form questions about sales patterns
  - Forecast explanation
  - Risk assessment
  - Recommendation generation

## Quick Start

### 1. Installation

```bash
# Clone or copy the files
cd chronoforge_rag_python

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up API Keys

```bash
# Option A: Gemini (recommended - has free tier)
export GEMINI_API_KEY="your-gemini-api-key"

# Option B: OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Option C: Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Or create a `.env` file:
```
GEMINI_API_KEY=your-key-here
```

### 3. Build Knowledge Base

```bash
# From sample data
python build_knowledge_base.py ./kb sample_sales.csv

# From multiple files
python build_knowledge_base.py ./kb data1.csv data2.json
```

### 4. Query the System

```bash
# Interactive mode
python query_tool.py --kb ./kb

# Single query
python query_tool.py --kb ./kb --query "What patterns do we see during Black Friday?"

# Main application
python main.py --kb ./kb --interactive
```

## Usage Examples

### Interactive Queries

```
Query> What patterns do we see during Black Friday?
Query> How do competitor promotions typically affect our electronics sales?
Query> What weather conditions correlate with higher apparel sales?
```

### Python API

```python
from chronoforge_rag import RAGQuery, ForecastData
from rag_pipeline import RAGPipelineBuilder
from llm_engine import auto_detect_llm_engine

# Create pipeline
pipeline = (RAGPipelineBuilder()
    .with_llm_engine(auto_detect_llm_engine())
    .build_with_knowledge_base("./kb"))

# Simple query
response = pipeline.query(RAGQuery(
    query_text="What drives holiday sales?"
))
print(response.generated_text)

# Forecast explanation
forecast = ForecastData(
    date="2025-01-15",
    ensemble_prediction=18850.0,
    confidence_interval_low=16000.0,
    confidence_interval_high=21700.0
)
explanation = pipeline.explain_forecast(forecast)
print(explanation.generated_text)

# Risk assessment
risk = pipeline.assess_risk(forecast)
print(risk.generated_text)

# Recommendations
recs = pipeline.get_recommendations(forecast, "maximize_sales")
print(recs.generated_text)
```

### Filtering Queries

```python
# Filter by region and date
response = pipeline.query(RAGQuery(
    query_text="Sales performance analysis",
    region_filter="North",
    date_from="2024-01-01",
    date_to="2024-06-30"
))
```

## Data Format

### CSV Format

```csv
date,sales_value,region,category,promotion,competitor_action,weather_condition,seasonality,epidemic_flag,description
2024-01-15,15234.50,North,Electronics,1,0,Clear,Winter,0,Strong post-holiday sales
```

### JSON Format

```json
{
  "id": "scenario_001",
  "date": "2024-01-15",
  "description": "Strong post-holiday sales",
  "sales_value": 15234.50,
  "region": "North",
  "category": "Electronics",
  "had_promotion": true,
  "had_competitor_action": false,
  "weather_condition": "Clear",
  "seasonality": "Winter"
}
```

## Configuration

### Using Different LLM Providers

```python
from chronoforge_rag import LLMConfig
from rag_pipeline import RAGPipelineBuilder

# Gemini
pipeline = (RAGPipelineBuilder()
    .with_llm_config(LLMConfig(
        provider="gemini",
        model_name="gemini-1.5-pro",
        temperature=0.7
    ))
    .build())

# OpenAI
pipeline = (RAGPipelineBuilder()
    .with_llm_config(LLMConfig(
        provider="openai",
        model_name="gpt-4o-mini"
    ))
    .build())

# Anthropic
pipeline = (RAGPipelineBuilder()
    .with_llm_config(LLMConfig(
        provider="anthropic",
        model_name="claude-3-haiku-20240307"
    ))
    .build())
```

### Custom System Prompt

```python
pipeline = (RAGPipelineBuilder()
    .with_system_prompt("""
You are a sales forecasting expert.
Focus on actionable insights.
Be concise and data-driven.
    """)
    .build())
```

### API vs Local Embeddings

```python
from chronoforge_rag import EmbeddingConfig

# Local (default) - requires sentence-transformers
config = EmbeddingConfig(
    model_name="all-MiniLM-L6-v2"
)

# OpenAI API embeddings
config = EmbeddingConfig(
    use_api=True,
    api_provider="openai"
)

# Gemini API embeddings
config = EmbeddingConfig(
    use_api=True,
    api_provider="gemini"
)
```

## Project Structure

```
chronoforge_rag_python/
├── chronoforge_rag.py      # Core types and interfaces
├── embedding_engine.py     # Embedding implementations
├── llm_engine.py           # LLM provider implementations
├── vector_store.py         # ChromaDB vector store
├── knowledge_base.py       # Sales scenario management
├── rag_pipeline.py         # Main RAG orchestration
├── build_knowledge_base.py # CLI: Build knowledge base
├── query_tool.py           # CLI: Interactive queries
├── main.py                 # Main application
├── requirements.txt        # Python dependencies
├── sample_sales.csv        # Sample data
└── README.md               # This file
```

## Comparison: C++ vs Python

| Feature | C++ Version | Python Version |
|---------|-------------|----------------|
| LLM | llama.cpp (local) | Gemini/OpenAI/Claude API |
| Embeddings | ONNX Runtime | sentence-transformers or API |
| Vector Store | hnswlib | ChromaDB |
| Deployment | Compiled binary | Python script |
| Dependencies | Complex build | pip install |
| Performance | Faster inference | API latency |
| Cost | Free (local) | API costs |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Alternative for Gemini |

## Troubleshooting

### "No API key found"
Set one of the API key environment variables or use `--llm mock` for testing.

### "chromadb not installed"
Run `pip install chromadb`. The system will fall back to in-memory storage otherwise.

### "sentence-transformers not installed"
Run `pip install sentence-transformers` or use API embeddings with `--use-api`.

### Slow first query
The embedding model loads on first use. Subsequent queries will be faster.

## License

MIT License

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

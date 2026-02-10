# ChronoForge Pulse Backend

Time Series Forecasting Backend with AI Integration (Ollama + Claude)

## Features

### ✅ Core Features (v1)
- **Demand Forecasting**: Auto model selection (LSTM, ARIMA, XGBoost, LightGBM, Prophet)
- **LLM Integration**: Dual LLM support (Ollama primary, Claude secondary)
- **Intelligent Routing**: Automatic LLM selection based on task complexity
- **Auto Model Selection**: MAPE/RMSE-based best model selection
- **Background Training**: Automatic model retraining on data upload
- **RAG Support**: Query historical patterns (when knowledge base is built)

### 🚧 Stub Features (Coming in v2)
- Lot Sizing (EOQ, Wagner-Whitin)
- Production Schedule Optimization (MHP, Genetic Algorithm)
- Materials Acquisition Planning (MRP, Regression)

## Architecture

```
Backend Services:
├── Forecast Service (Core forecasting logic)
├── LLM Service (Ollama + Claude routing)
├── RAG Service (Historical pattern analysis)
└── Training Service (Background model training)

ML Models:
├── LSTM (TensorFlow)
├── ARIMA/SARIMA (statsmodels)
├── XGBoost
├── LightGBM
└── Prophet

LLM Engines:
├── Ollama (Primary) - llama3/mistral
└── Claude (Secondary) - claude-3-5-sonnet
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd /app/backend
pip install -r requirements.txt
```

### 2. Install & Configure Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Pull llama3 model
ollama pull llama3

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### 3. Configure Environment Variables

Edit `/app/backend/.env`:

```bash
# MongoDB
MONGO_URL=mongodb://localhost:27017/chronoforge

# LLM Configuration
ANTHROPIC_API_KEY=sk-ant-api03-xxx...  # Your Claude API key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Server Configuration
BACKEND_PORT=8001
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 4. (Optional) Build Knowledge Base for RAG

```bash
cd /app
python build_knowledge_base.py ./kb sales_data.csv
```

### 5. Start the Backend

**Option A: Direct Run**
```bash
cd /app/backend
python server.py
```

**Option B: Using Supervisor**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start backend
```

## API Endpoints

### Forecasting

#### POST /api/forecast/demand
Generate demand forecast with auto model selection

```json
{
  "data": [15234.5, 12450.75, 18500.0, ...],
  "model": "auto",
  "horizon": 7,
  "confidence_level": 0.95,
  "use_claude": false
}
```

Response:
```json
{
  "success": true,
  "forecast_id": "uuid",
  "model_used": "lstm",
  "predictions": [22000, 21500, ...],
  "confidence_intervals": {
    "lower": [20000, 19500, ...],
    "upper": [24000, 23500, ...]
  },
  "metrics": {
    "mape": 5.2,
    "rmse": 1250.5,
    "mae": 980.3,
    "r2": 0.92
  },
  "llm_explanation": "The forecast indicates...",
  "llm_used": "ollama-llama3"
}
```

#### POST /api/forecast/lot-sizing (STUB)
```json
{
  "demand_forecast": [1000, 1200, 1100],
  "holding_cost": 1.0,
  "ordering_cost": 100.0
}
```

#### POST /api/forecast/production-schedule (STUB)
```json
{
  "demand_forecast": [1000, 1200, 1100],
  "capacity": 1500.0,
  "resource_constraints": {}
}
```

#### POST /api/forecast/materials-acquisition (STUB)
```json
{
  "production_schedule": [1000, 1200, 1100],
  "lead_time": 7,
  "safety_stock": 100.0
}
```

### Data Management

#### POST /api/data/upload
Upload CSV/JSON data and trigger auto-training

```bash
curl -X POST -F "file=@sales_data.csv" -F "auto_train=true" \
  http://localhost:8001/api/data/upload
```

#### GET /api/data/datasets
List all uploaded datasets

#### GET /api/data/train/status/{job_id}
Get training job status

### RAG Queries

#### POST /api/rag/query
Query historical patterns

```json
{
  "question": "What patterns occurred during Black Friday?",
  "use_claude": false,
  "top_k": 5
}
```

#### POST /api/rag/explain-forecast
Get forecast explanation with historical context

```json
{
  "forecast_data": {...},
  "use_claude": false
}
```

### Health & Status

#### GET /api/health
Check system health and service availability

#### GET /api/forecast/models/status
Check forecasting models status

## LLM Routing Logic

The backend intelligently routes requests between Ollama and Claude:

| Task Type | Complexity | LLM Used | Reason |
|-----------|------------|----------|--------|
| Simple Query | Low (0.0-0.5) | Ollama | Fast, cost-effective |
| Data Description | Low (0.3) | Ollama | Quick summaries |
| Forecast Explanation | High (0.8) | Claude | Better reasoning |
| Risk Assessment | High (0.8) | Claude | Complex analysis |
| Pattern Analysis | Medium (0.7) | Ollama/Claude | Context-dependent |

**Override**: Set `use_claude=true` to force Claude usage

## Model Auto-Selection

The backend automatically selects the best model based on validation performance:

1. **Data Split**: 80% training, 20% validation
2. **Train All Models**: LSTM, ARIMA, XGBoost, LightGBM, Prophet
3. **Evaluate**: Calculate MAPE, RMSE, MAE, R² for each model
4. **Select Best**: Lowest MAPE wins
5. **Generate Forecast**: Use best model for final predictions

Manual Override: Set `model="lstm"` (or arima, xgboost, etc.)

## Testing

### Test Ollama
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Explain demand forecasting in one sentence",
  "stream": false
}'
```

### Test Claude
```bash
curl -X POST http://localhost:8001/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test Claude integration",
    "use_claude": true
  }'
```

### Test Forecast Endpoint
```bash
curl -X POST http://localhost:8001/api/forecast/demand \
  -H "Content-Type: application/json" \
  -d '{
    "data": [15234.5, 12450.75, 18500.0, 22100.25, 9800.0, 14200.0, 16750.5, 11500.0, 19800.0, 21500.75, 24300.0, 28500.5, 17200.0, 15800.0, 31200.0],
    "model": "auto",
    "horizon": 7,
    "use_claude": false
  }'
```

## Troubleshooting

### Ollama not available
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve &

# Pull model if not exists
ollama pull llama3
```

### Claude API errors
- Verify API key in `.env`
- Check API quota/limits
- System will fallback to Ollama if Claude fails

### Models not training
- Ensure minimum 10 data points
- Check logs: `tail -f /var/log/supervisor/backend.err.log`
- Verify all ML libraries installed

### Knowledge Base not found
- RAG features require building knowledge base first
- Run: `python /app/build_knowledge_base.py /app/kb /app/sales_data.csv`
- APIs will work without RAG (LLM explanation only)

## Performance Notes

- **LSTM**: Best for sequential patterns, longer training time
- **ARIMA**: Fast, works well with seasonal data
- **XGBoost**: Excellent for feature-rich data
- **LightGBM**: Fast training, good general performance
- **Prophet**: Handles missing data and holidays well

## Next Steps

1. ✅ Backend fully functional
2. 🔄 Build knowledge base for RAG
3. 🚀 Build frontend (React + Recharts)
4. 📊 Add MongoDB persistence
5. 🔧 Implement full Lot Sizing, Production, Materials features

## API Documentation

Full interactive API documentation available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

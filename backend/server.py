"""
ChronoForge Pulse Backend - FastAPI Server
Time Series Forecasting with AI Integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import uvicorn

# Load environment variables (don't override Kubernetes env vars)
load_dotenv(override=False)

# Import routes
from routes.forecast_routes import router as forecast_router
from routes.data_routes import router as data_router
from routes.rag_routes import router as rag_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI"""
    # Startup
    print("=" * 60)
    print("🚀 ChronoForge Pulse Backend Starting...")
    print("=" * 60)
    
    # Check environment variables
    mongo_url = os.getenv("MONGO_URL", "Not configured")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    has_claude = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    print(f"📊 MongoDB: {mongo_url}")
    print(f"🤖 Ollama: {ollama_url}")
    print(f"🧠 Claude: {'✓ Configured' if has_claude else '✗ Not configured'}")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("\n👋 ChronoForge Pulse Backend Shutting Down...")


# Create FastAPI app
app = FastAPI(
    title="ChronoForge Pulse API",
    description="Time Series Forecasting Backend with AI Integration (Ollama + Claude)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(forecast_router)
app.include_router(data_router)
app.include_router(rag_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ChronoForge Pulse API v1.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "forecasting": "/api/forecast/*",
            "data_management": "/api/data/*",
            "rag_queries": "/api/rag/*"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    # Check Ollama
    ollama_available = False
    try:
        import requests
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        ollama_available = response.status_code == 200
    except:
        pass
    
    # Check Claude
    claude_available = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "ollama": "available" if ollama_available else "unavailable",
            "claude": "configured" if claude_available else "not configured",
            "mongodb": "configured" if os.getenv("MONGO_URL") else "not configured"
        },
        "models": {
            "lstm": "available",
            "arima": "available",
            "xgboost": "available",
            "lightgbm": "available",
            "prophet": "available"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "detail": "Internal server error"
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8001))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

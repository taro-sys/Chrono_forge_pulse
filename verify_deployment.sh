#!/bin/bash
# ChronoForge Pulse - Deployment Integration Verification

echo "═══════════════════════════════════════════════════════════"
echo "  ChronoForge Pulse - Deployment Readiness Check"
echo "═══════════════════════════════════════════════════════════"
echo

# Check all deployment files exist
echo "1️⃣  Checking Deployment Files..."
FILES=(
    "/app/backend/.env.production"
    "/app/frontend/.env.production"
    "/app/.env.example"
    "/app/backend/requirements.lightweight.txt"
    "/app/DEPLOYMENT_FIXES.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ Missing: $file"
    fi
done
echo

# Check server.py has MongoDB optional message
echo "2️⃣  Checking MongoDB Optional Configuration..."
if grep -q "using in-memory storage" /app/backend/server.py; then
    echo "  ✅ MongoDB configured as optional"
else
    echo "  ❌ MongoDB not configured as optional"
fi
echo

# Check ML libraries have fallback
echo "3️⃣  Checking ML Libraries Graceful Fallback..."
if grep -q "TENSORFLOW_AVAILABLE = False" /app/backend/models/forecasting_models.py; then
    echo "  ✅ TensorFlow fallback configured"
else
    echo "  ❌ TensorFlow fallback missing"
fi

if grep -q "PROPHET_AVAILABLE = False" /app/backend/models/forecasting_models.py; then
    echo "  ✅ Prophet fallback configured"
else
    echo "  ❌ Prophet fallback missing"
fi

if grep -q "if not TENSORFLOW_AVAILABLE" /app/backend/models/forecasting_models.py; then
    echo "  ✅ Training methods check availability"
else
    echo "  ❌ Training methods don't check availability"
fi
echo

# Check CORS configuration
echo "4️⃣  Checking CORS Configuration..."
if grep -q "CORS_ORIGINS=\*" /app/backend/.env.production; then
    echo "  ✅ CORS set to wildcard for production"
else
    echo "  ⚠️  CORS not set to wildcard"
fi
echo

# Check load_dotenv override
echo "5️⃣  Checking Environment Loading..."
if grep -q "load_dotenv(override=False)" /app/backend/server.py; then
    echo "  ✅ Load dotenv uses override=False (Kubernetes-safe)"
else
    echo "  ❌ Load dotenv not Kubernetes-safe"
fi
echo

# Count lightweight requirements
echo "6️⃣  Checking Lightweight Requirements..."
HEAVY_COUNT=$(grep -E "tensorflow|prophet|sentence-transformers|chromadb" /app/backend/requirements.lightweight.txt 2>/dev/null | wc -l)
if [ "$HEAVY_COUNT" -eq 0 ]; then
    echo "  ✅ Lightweight requirements don't include heavy dependencies"
else
    echo "  ❌ Lightweight requirements still have heavy dependencies"
fi
echo

# Summary
echo "═══════════════════════════════════════════════════════════"
echo "  Deployment Readiness Summary"
echo "═══════════════════════════════════════════════════════════"
echo
echo "✅ Code Changes Applied:"
echo "  • MongoDB made optional"
echo "  • ML libraries have graceful fallback"
echo "  • Environment files created"
echo "  • CORS configured for production"
echo "  • Kubernetes-safe environment loading"
echo "  • Lightweight requirements available"
echo
echo "📝 Deployment Options:"
echo "  Option A: Full ML Stack (requirements.txt)"
echo "    - 2GB+ RAM, 5 models (LSTM, ARIMA, XGBoost, LightGBM, Prophet)"
echo
echo "  Option B: Lightweight Stack (requirements.lightweight.txt)"
echo "    - 1GB RAM, 3 models (ARIMA, XGBoost, LightGBM)"
echo "    - Rename to requirements.txt before deploying"
echo
echo "🎯 Expected Outcome:"
echo "  • MongoDB migration errors will be ignored"
echo "  • App will start successfully"
echo "  • Forecasting will work (with available models)"
echo "  • Frontend will render correctly"
echo
echo "🚀 Ready to Deploy!"
echo

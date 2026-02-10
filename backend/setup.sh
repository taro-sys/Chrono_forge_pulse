#!/bin/bash
# ChronoForge Pulse Backend - Setup Script

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  ChronoForge Pulse Backend - Setup"
echo "═══════════════════════════════════════════════════════════"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "⚠️  Please run as root (use sudo)"
   exit 1
fi

# Step 1: Install system dependencies
echo "📦 Step 1: Installing system dependencies..."
apt-get update -qq
apt-get install -y zstd curl python3 python3-pip -qq
echo "✓ System dependencies installed"
echo

# Step 2: Install Python dependencies
echo "🐍 Step 2: Installing Python dependencies..."
cd /app/backend
pip install -q -r requirements.txt
echo "✓ Python dependencies installed"
echo

# Step 3: Install Ollama
echo "🤖 Step 3: Installing Ollama..."
if [ ! -f "/usr/local/bin/ollama" ]; then
    curl -fsSL https://ollama.com/install.sh | bash > /tmp/ollama_install.log 2>&1
    echo "✓ Ollama installed"
else
    echo "✓ Ollama already installed"
fi
echo

# Step 4: Start Ollama service
echo "🚀 Step 4: Starting Ollama service..."
pkill -f "ollama serve" 2>/dev/null || true
nohup /usr/local/bin/ollama serve > /var/log/ollama.log 2>&1 &
sleep 3
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama service started"
else
    echo "⚠️  Ollama service may not be running properly"
fi
echo

# Step 5: Pull llama3 model
echo "📥 Step 5: Pulling llama3 model (this may take a few minutes)..."
/usr/local/bin/ollama pull llama3 > /tmp/ollama_pull.log 2>&1 &
PULL_PID=$!
echo "✓ Model download started in background (PID: $PULL_PID)"
echo "   Monitor progress: tail -f /tmp/ollama_pull.log"
echo

# Step 6: Configure environment
echo "⚙️  Step 6: Checking environment configuration..."
if [ -f "/app/backend/.env" ]; then
    echo "✓ Environment file exists"
    # Check if Anthropic API key is set
    if grep -q "ANTHROPIC_API_KEY=sk-ant" /app/backend/.env; then
        echo "✓ Claude API key configured"
    else
        echo "⚠️  Claude API key not configured"
    fi
else
    echo "⚠️  Environment file not found at /app/backend/.env"
fi
echo

# Step 7: Setup supervisor (optional)
echo "🔧 Step 7: Setting up supervisor..."
if [ -f "/etc/supervisor/conf.d/backend.conf" ]; then
    supervisorctl reread 2>/dev/null || true
    supervisorctl update 2>/dev/null || true
    echo "✓ Supervisor configuration updated"
else
    echo "⚠️  Supervisor config not found (optional)"
fi
echo

# Step 8: Start backend
echo "🚀 Step 8: Starting backend server..."
pkill -f "python3 server.py" 2>/dev/null || true
cd /app/backend
nohup python3 server.py > /tmp/backend.log 2>&1 &
sleep 5

if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "✓ Backend server started successfully"
else
    echo "⚠️  Backend may not have started. Check logs: tail -f /tmp/backend.log"
fi
echo

echo "═══════════════════════════════════════════════════════════"
echo "  Setup Complete!"
echo "═══════════════════════════════════════════════════════════"
echo
echo "✅ Backend API: http://localhost:8001"
echo "📚 API Documentation: http://localhost:8001/docs"
echo "🤖 Ollama: $(curl -s http://localhost:11434/api/tags | grep -q 'models' && echo 'Running' || echo 'Starting...')"
echo "🧠 Claude: $(grep -q 'ANTHROPIC_API_KEY=sk-ant' /app/backend/.env && echo 'Configured' || echo 'Not configured')"
echo
echo "Test the backend:"
echo "  bash /app/backend/test_backend.sh"
echo
echo "Monitor logs:"
echo "  Backend: tail -f /tmp/backend.log"
echo "  Ollama: tail -f /var/log/ollama.log"
echo "  Model download: tail -f /tmp/ollama_pull.log"
echo
echo "Build knowledge base (optional for RAG):"
echo "  python /app/build_knowledge_base.py /app/kb /app/sales_data.csv"
echo

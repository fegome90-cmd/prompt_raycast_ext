#!/bin/bash
# DeepSeek Integration Test Script
# Tests configuration, API connectivity, and backend health

set -e  # Fail on error

echo "🔍 DeepSeek Integration Test"
echo "================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verify .env configuration
echo ""
echo "1️⃣  Checking .env configuration..."
if grep -q "LLM_PROVIDER=deepseek" .env; then
    echo -e "${GREEN}✓${NC} LLM_PROVIDER=deepseek"
else
    echo -e "${RED}✗${NC} LLM_PROVIDER not set to deepseek"
    echo "   Please set LLM_PROVIDER=deepseek in .env"
    exit 1
fi

if grep -q "DEEPSEEK_API_KEY=sk-" .env; then
    echo -e "${GREEN}✓${NC} DEEPSEEK_API_KEY is set"
else
    echo -e "${RED}✗${NC} DEEPSEEK_API_KEY not found or invalid"
    echo "   Please set DEEPSEEK_API_KEY=sk-... in .env"
    exit 1
fi

# Check if user still has placeholder key
if grep -q "DEEPSEEK_API_KEY=sk-your-api-key-here" .env; then
    echo -e "${RED}✗${NC} DEEPSEEK_API_KEY is still placeholder"
    echo "   Please replace 'sk-your-api-key-here' with your actual API key"
    echo "   Get your key from: https://platform.deepseek.com/"
    exit 1
fi

# 2. Test DeepSeek API connectivity
echo ""
echo "2️⃣  Testing DeepSeek API connectivity..."
API_KEY=$(grep "DEEPSEEK_API_KEY" .env | cut -d'=' -f2)

response=$(curl -s https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $API_KEY")

if echo "$response" | grep -q "deepseek-chat"; then
    echo -e "${GREEN}✓${NC} DeepSeek API is accessible"
else
    echo -e "${RED}✗${NC} Cannot reach DeepSeek API"
    echo "   Response: $response"
    exit 1
fi

# 3. Verify Python dependencies
echo ""
echo "3️⃣  Checking Python dependencies..."
if python -c "import dspy" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} DSPy installed"
else
    echo -e "${RED}✗${NC} DSPy not installed"
    exit 1
fi

if python -c "import litellm" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} LiteLLM installed"
else
    echo -e "${RED}✗${NC} LiteLLM not installed"
    exit 1
fi

# 4. Test backend startup
echo ""
echo "4️⃣  Testing backend startup (timed 10s)..."
timeout 10s python main.py &
BACKEND_PID=$!

# Wait for startup
sleep 5

# Check health endpoint
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Backend is healthy"

    # Show provider info
    health_info=$(curl -s http://localhost:8000/health)
    provider=$(echo "$health_info" | grep -o '"provider":"[^"]*"' | cut -d'"' -f4)
    model=$(echo "$health_info" | grep -o '"model":"[^"]*"' | cut -d'"' -f4)
    echo "   Provider: $provider"
    echo "   Model: $model"
else
    echo -e "${RED}✗${NC} Backend health check failed"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Cleanup
kill $BACKEND_PID 2>/dev/null || true

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start backend: python main.py"
echo "  2. Run variability test: cd dashboard && npx tsx scripts/test-variability.ts 10 specific"
echo "  3. Compare results with CRT-03 baseline"

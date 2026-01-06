#!/bin/bash
# Quick DeepSeek variability test - 10 iterations

echo "🧪 DeepSeek Variability Test (10 iterations)"
echo "=============================================="
echo ""
echo "Input: 'Create a sorting function in Python'"
echo ""

API_URL="http://localhost:8000/api/v1/improve-prompt"
IDEA='{"idea": "Create a sorting function in Python"}'

success=0
failed=0
total_confidence=0

for i in {1..10}; do
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "$IDEA")

    # Check if response is valid JSON
    if echo "$response" | jq -e '.improved_prompt' > /dev/null 2>&1; then
        confidence=$(echo "$response" | jq -r '.confidence')
        prompt=$(echo "$response" | jq -r '.improved_prompt' | head -c 100)
        ((success++))
        total_confidence=$(echo "$total_confidence + $confidence" | bc)
        echo "  ✅ Run $i/10 - Confidence: $confidence"
    else
        ((failed++))
        echo "  ❌ Run $i/10 - Failed to parse JSON"
    fi
done

echo ""
echo "=============================================="
echo "📊 RESULTS"
echo "=============================================="
echo "Total runs: 10"
echo "Successful: $success/10 ($((success * 10))%)"
echo "Failed: $failed/10 ($((failed * 10))%)"
if [ $success -gt 0 ]; then
    avg_confidence=$(echo "scale=2; $total_confidence / $success" | bc)
    echo "Avg Confidence: $avg_confidence"
fi
echo ""
echo "🎯 Comparison to CRT-03 Baseline (Ollama):"
echo "  JSON parse success: 30-40% → $((success * 10))%"
echo ""

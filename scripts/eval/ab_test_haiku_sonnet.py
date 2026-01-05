"""A/B Test: Haiku 4.5 vs Sonnet 4.5 for DSPy Prompt Improver"""

import os
import time
import json
from datetime import datetime
from pathlib import Path

# Test prompts
TEST_PROMPTS = [
    {"idea": "create a todo app", "context": "productivity"},
    {"idea": "write a python script to parse csv", "context": "programming"},
    {"idea": "plan a marketing strategy", "context": "business"},
    {"idea": "explain quantum computing", "context": "education"},
    {"idea": "design a landing page", "context": "web design"},
]

# CORRECT MODELS
PROVIDERS = [
    {"name": "Haiku 4.5", "provider": "anthropic", "model": "claude-haiku-4-5-20251001", "key": "HEMDOV_ANTHROPIC_API_KEY"},
    {"name": "Sonnet 4.5", "provider": "anthropic", "model": "claude-sonnet-4-5-20250929", "key": "HEMDOV_ANTHROPIC_API_KEY"},
]

def test_provider(provider_config):
    """Test a single provider with all prompts."""
    import requests
    
    results = []
    url = "http://localhost:8000/api/v1/improve-prompt"
    
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        print(f"  Testing prompt {i}/{len(TEST_PROMPTS)}...")
        
        start = time.time()
        try:
            response = requests.post(url, json=prompt, timeout=60)
            latency = (time.time() - start) * 1000  # ms
            
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "prompt_index": i,
                    "latency_ms": round(latency, 2),
                    "confidence": data.get("confidence", 0),
                    "prompt_length": len(data.get("improved_prompt", "")),
                    "success": True,
                })
            else:
                results.append({
                    "prompt_index": i,
                    "latency_ms": round(latency, 2),
                    "success": False,
                    "error": response.status_code,
                })
        except Exception as e:
            results.append({
                "prompt_index": i,
                "latency_ms": round((time.time() - start) * 1000, 2),
                "success": False,
                "error": str(e),
            })
    
    # Calculate stats
    successful = [r for r in results if r["success"]]
    if successful:
        avg_latency = sum(r["latency_ms"] for r in successful) / len(successful)
        avg_confidence = sum(r["confidence"] for r in successful) / len(successful)
        avg_length = sum(r["prompt_length"] for r in successful) / len(successful)
    else:
        avg_latency = avg_confidence = avg_length = 0
    
    return {
        "provider": provider_config["name"],
        "model": provider_config["model"],
        "total_prompts": len(TEST_PROMPTS),
        "successful": len(successful),
        "failed": len(results) - len(successful),
        "avg_latency_ms": round(avg_latency, 2),
        "avg_confidence": round(avg_confidence, 3),
        "avg_prompt_length": round(avg_length, 0),
        "results": results,
    }

def main():
    """Run A/B test comparing Haiku 4.5 vs Sonnet 4.5."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"scripts/eval/ab_test_haiku_sonnet_{timestamp}.json")
    
    print("=" * 60)
    print("A/B Test: Haiku 4.5 vs Sonnet 4.5 (CORRECTED)")
    print("=" * 60)
    
    all_results = []
    
    for provider_config in PROVIDERS:
        print(f"\n🔵 Testing {provider_config['name']} ({provider_config['model']})...")
        result = test_provider(provider_config)
        all_results.append(result)
        
        print(f"  ✓ Average latency: {result['avg_latency_ms']:.0f}ms")
        print(f"  ✓ Average confidence: {result['avg_confidence']:.2f}")
        print(f"  ✓ Success rate: {result['successful']}/{result['total_prompts']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    haiku = all_results[0]
    sonnet = all_results[1]
    
    print(f"\n{haiku['provider']}:")
    print(f"  Latency:  {haiku['avg_latency_ms']:.0f}ms")
    print(f"  Confidence: {haiku['avg_confidence']:.2f}")
    
    print(f"\n{sonnet['provider']}:")
    print(f"  Latency:  {sonnet['avg_latency_ms']:.0f}ms")
    print(f"  Confidence: {sonnet['avg_confidence']:.2f}")
    
    latency_diff = haiku['avg_latency_ms'] - sonnet['avg_latency_ms']
    confidence_diff = haiku['avg_confidence'] - sonnet['avg_confidence']
    
    print(f"\n📊 Comparison:")
    print(f"  Latency difference: {latency_diff:+.0f}ms ({'Haiku faster' if latency_diff < 0 else 'Sonnet faster'})")
    print(f"  Confidence difference: {confidence_diff:+.3f}")
    
    # Save results
    output_file.write_text(json.dumps({
        "timestamp": timestamp,
        "providers": PROVIDERS,
        "results": all_results,
        "summary": {
            "haiku_latency_ms": haiku['avg_latency_ms'],
            "sonnet_latency_ms": sonnet['avg_latency_ms'],
            "latency_diff_ms": latency_diff,
            "haiku_confidence": haiku['avg_confidence'],
            "sonnet_confidence": sonnet['avg_confidence'],
            "confidence_diff": confidence_diff,
        }
    }, indent=2))
    
    print(f"\n✅ Results saved to: {output_file}")

if __name__ == "__main__":
    main()

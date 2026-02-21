import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_post_api_v1_improve_prompt_valid_input():
    url = f"{BASE_URL}/api/v1/improve-prompt"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "idea": "write a python function to validate email addresses",
        "context": "backend utility",
        "guardrails": ["no external deps"]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        data = response.json()
        
        # Validate response keys
        assert "improved_prompt" in data, "Response missing 'improved_prompt'"
        assert isinstance(data["improved_prompt"], str) and data["improved_prompt"], "'improved_prompt' should be a non-empty string"
        
        assert "confidence" in data, "Response missing 'confidence'"
        assert isinstance(data["confidence"], (float, int)), "'confidence' should be a number"
        assert 0 <= data["confidence"] <= 1, "'confidence' should be between 0 and 1"
        
        assert "quality_gate" in data, "Response missing 'quality_gate'"
        assert isinstance(data["quality_gate"], dict), "'quality_gate' should be an object"
        
        assert "degradation_flags" in data, "Response missing 'degradation_flags'"
        assert isinstance(data["degradation_flags"], list), "'degradation_flags' should be a list"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_post_api_v1_improve_prompt_valid_input()
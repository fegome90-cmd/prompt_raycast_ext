import requests

def test_get_health_check_healthy_status():
    base_url = "http://localhost:8000"
    url = f"{base_url}/health"
    timeout = 30
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to /health failed: {e}"

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

    json_data = response.json()

    # Validate required keys exist
    expected_keys = {"status", "provider", "model", "dspy_configured"}
    assert expected_keys.issubset(json_data.keys()), f"Response keys missing, expected at least {expected_keys}"

    # Validate response values for healthy status case
    assert json_data["status"] == "healthy", f"Expected status 'healthy', got {json_data['status']}"
    assert json_data["provider"] == "anthropic", f"Expected provider 'anthropic', got {json_data['provider']}"
    assert json_data["model"] == "claude-haiku-4-5-20251001", f"Expected model 'claude-haiku-4-5-20251001', got {json_data['model']}"
    assert isinstance(json_data["dspy_configured"], bool), "dspy_configured should be a boolean"
    assert json_data["dspy_configured"] is True, "dspy_configured should be True"

test_get_health_check_healthy_status()
import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_health_check_degraded_status():
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate degraded status scenario when DSPy or LLM provider config is missing
    # The test description expects the following values in degraded state:
    # status == "degraded"
    # provider == None (null)
    # model == None (null)
    # dspy_configured == False

    assert "status" in data, "'status' field is missing in response"
    assert data["status"] == "degraded", f"Expected status 'degraded' but got '{data['status']}'"

    # provider field must exist and be None
    assert "provider" in data, "'provider' field is missing in response"
    assert data["provider"] is None, f"Expected provider None but got '{data['provider']}'"

    # model field must exist and be None
    assert "model" in data, "'model' field is missing in response"
    assert data["model"] is None, f"Expected model None but got '{data['model']}'"

    # dspy_configured must be False
    assert "dspy_configured" in data, "'dspy_configured' field is missing in response"
    assert data["dspy_configured"] is False, f"Expected dspy_configured False but got {data['dspy_configured']}"

test_get_health_check_degraded_status()
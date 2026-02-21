import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_post_api_v1_improve_prompt_llm_provider_unavailable():
    url = f"{BASE_URL}/api/v1/improve-prompt"
    headers = {"Content-Type": "application/json"}
    payload = {
        "idea": "generate marketing copy",
        "guardrails": []
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 503, f"Expected status code 503, got {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert "error" in data, "Response JSON missing 'error' field"
    assert data["error"] == "service_unavailable", f"Expected error 'service_unavailable' but got '{data['error']}'"

    assert "message" in data, "Response JSON missing 'message' field"
    assert data["message"] == "LLM provider not configured or circuit breaker open", (
        f"Expected message 'LLM provider not configured or circuit breaker open' but got '{data['message']}'"
    )

    if "degradation_flags" in data:
        assert isinstance(data["degradation_flags"], list), "degradation_flags should be a list"
        flags = data["degradation_flags"]
        expected_flags = {"provider_unavailable", "complex_strategy_disabled"}
        assert any(flag in expected_flags for flag in flags), (
            f"Expected degradation_flags to contain one of {expected_flags}, got {flags}"
        )


test_post_api_v1_improve_prompt_llm_provider_unavailable()

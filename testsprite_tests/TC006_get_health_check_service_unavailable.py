import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_health_check_service_unavailable():
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    except requests.RequestException as e:
        # If the server is down, this might raise a connection error.
        assert False, f"Request failed with exception: {e}"

    # We expect a 503 status for this test case indicating service unavailable
    assert response.status_code == 503, f"Expected status 503, got {response.status_code}"

    json_response = response.json()
    assert isinstance(json_response, dict), "Response is not a JSON object"

    # Expected error response for service unavailable
    assert "error" in json_response, "Missing 'error' field in response"
    assert json_response["error"] == "service_unavailable", f"Expected error 'service_unavailable', got {json_response.get('error')}"
    assert "message" in json_response, "Missing 'message' field in response"
    assert isinstance(json_response["message"], str) and len(json_response["message"]) > 0, "Invalid or empty message field"

test_get_health_check_service_unavailable()
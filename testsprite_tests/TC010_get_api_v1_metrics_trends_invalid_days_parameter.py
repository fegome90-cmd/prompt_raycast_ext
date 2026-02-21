import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_v1_metrics_trends_invalid_days_parameter():
    url = f"{BASE_URL}/api/v1/metrics/trends"
    params = {"days": -7}
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 400, f"Expected status 400, got {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert "error" in data, "Response JSON missing 'error'"
    assert data["error"] == "invalid_parameter", f"Expected error 'invalid_parameter', got {data['error']}"
    assert "detail" in data, "Response JSON missing 'detail'"
    assert data["detail"] == "days must be a positive integer", f"Expected detail 'days must be a positive integer', got {data['detail']}"

test_get_api_v1_metrics_trends_invalid_days_parameter()
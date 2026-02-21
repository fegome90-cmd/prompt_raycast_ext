import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_v1_metrics_trends_valid_days_parameter():
    url = f"{BASE_URL}/api/v1/metrics/trends"
    params = {"days": 30}
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        assert False, f"HTTP request failed: {e}"

    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"

    json_data = response.json()
    assert isinstance(json_data, dict), "Response is not a JSON object"
    assert "periods" in json_data, "'periods' key not found in response"
    assert isinstance(json_data["periods"], list), "'periods' should be a list"
    assert len(json_data["periods"]) > 0, "'periods' list is empty"

    assert "trends" in json_data, "'trends' key not found in response"
    assert isinstance(json_data["trends"], dict), "'trends' should be an object"

test_get_api_v1_metrics_trends_valid_days_parameter()
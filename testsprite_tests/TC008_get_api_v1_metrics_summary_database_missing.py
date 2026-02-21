import requests

def test_get_api_v1_metrics_summary_database_missing():
    base_url = "http://localhost:8000"
    url = f"{base_url}/api/v1/metrics/summary"
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 503, f"Expected status code 503 but got {response.status_code}"
    try:
        json_data = response.json()
    except ValueError:
        assert False, "Response is not a valid JSON"

    assert "error" in json_data, "Response JSON missing 'error' field"
    assert json_data["error"] == "metrics_unavailable", f"Expected error 'metrics_unavailable' but got '{json_data['error']}'"
    assert "message" in json_data, "Response JSON missing 'message' field"
    assert isinstance(json_data["message"], str) and len(json_data["message"]) > 0, "Response 'message' field should be a non-empty string"

test_get_api_v1_metrics_summary_database_missing()
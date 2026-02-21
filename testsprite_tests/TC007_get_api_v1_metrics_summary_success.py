import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_v1_metrics_summary_success():
    url = f"{BASE_URL}/api/v1/metrics/summary"
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to {url} failed with exception: {e}"

    assert response.status_code == 200, f"Expected status 200 but got {response.status_code}"
    
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert "total_prompts" in data and isinstance(data["total_prompts"], int), "Missing or invalid total_prompts"
    assert "average_quality" in data and isinstance(data["average_quality"], (float, int)), "Missing or invalid average_quality"
    assert "average_performance" in data and isinstance(data["average_performance"], (float, int)), "Missing or invalid average_performance"
    assert "average_impact" in data and isinstance(data["average_impact"], (float, int)), "Missing or invalid average_impact"
    assert "grade_distribution" in data and isinstance(data["grade_distribution"], dict), "Missing or invalid grade_distribution"

test_get_api_v1_metrics_summary_success()
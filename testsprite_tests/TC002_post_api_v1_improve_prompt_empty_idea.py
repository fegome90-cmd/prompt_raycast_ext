import requests

BASE_URL = "http://localhost:8000"
IMPROVE_PROMPT_ENDPOINT = "/api/v1/improve-prompt"
TIMEOUT = 30

def test_post_api_v1_improve_prompt_empty_idea():
    url = BASE_URL + IMPROVE_PROMPT_ENDPOINT
    headers = {"Content-Type": "application/json"}
    payload = {"idea": ""}

    response = None
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response is not None, "No response received"
    assert response.status_code == 400, f"Expected status code 400 but got {response.status_code}"

    try:
        json_response = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert "error" in json_response, "'error' field missing in response"
    assert json_response["error"] == "Invalid input", f"Unexpected error message: {json_response.get('error')}"
    assert "detail" in json_response, "'detail' field missing in response"
    assert json_response["detail"] == "idea must be a non-empty string", f"Unexpected detail message: {json_response.get('detail')}"

test_post_api_v1_improve_prompt_empty_idea()
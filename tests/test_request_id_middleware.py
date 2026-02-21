"""Tests for Request ID middleware."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware import RequestIDMiddleware


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def test_generates_request_id_when_missing(client):
    """Should generate ID if not provided."""
    response = client.get("/test")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 8


def test_preserves_existing_request_id(client):
    """Should preserve ID if provided."""
    response = client.get("/test", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"


def test_request_id_is_alphanumeric(client):
    """Should only contain hex characters."""
    response = client.get("/test")
    request_id = response.headers["X-Request-ID"]
    assert all(c in "0123456789abcdef" for c in request_id)


def test_request_id_is_8_characters(client):
    """Generated ID should be exactly 8 characters (from uuid4.hex[:8])."""
    response = client.get("/test")

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) == 8


def test_empty_string_request_id_is_replaced(client):
    """Empty string header should be replaced with generated ID."""
    response = client.get("/test", headers={"X-Request-ID": ""})

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) == 8
    assert request_id != ""


def test_multiple_requests_have_unique_ids(client):
    """Multiple requests should get unique IDs."""
    ids = set()
    for _ in range(10):
        response = client.get("/test")
        ids.add(response.headers.get("X-Request-ID"))

    assert len(ids) == 10  # All unique

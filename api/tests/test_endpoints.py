"""
Tests for API endpoints functionality.
"""
import pytest
from fastapi.testclient import TestClient

from api.app import app


def test_root_endpoint(client):
    """Test the root endpoint returns a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "welcome" in response.json().get("message", "").lower()


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


@pytest.mark.parametrize(
    "technique",
    [
        "caching",
        "connection-pool",
        "avoid-n-plus-1",
        "pagination",
        "json-serialization",
        "compression",
        "async-logging",
    ],
)
def test_technique_endpoints_exist(client, technique):
    """Test that all technique endpoints exist and are accessible."""
    response = client.get(f"/techniques/{technique}")
    assert response.status_code == 200
    # Basic validation that we get a JSON response
    assert response.headers.get("content-type", "").startswith("application/json")


def test_caching_endpoint(client):
    """Test the caching endpoint."""
    # First request should cache the result
    response = client.get("/techniques/caching")
    assert response.status_code == 200
    
    # Second request should use the cache
    response = client.get("/techniques/caching")
    assert response.status_code == 200
    
    # Test with cache bypass
    response = client.get("/techniques/caching?bypass_cache=true")
    assert response.status_code == 200


def test_json_serialization_endpoint(client):
    """Test the JSON serialization endpoint."""
    # Test with different serializers
    for serializer in ["standard", "ujson", "orjson"]:
        response = client.get(f"/techniques/json-serialization?serializer={serializer}")
        assert response.status_code == 200
        
        # Verify we get JSON back
        assert response.headers.get("content-type", "").startswith("application/json")


def test_pagination_endpoint(client):
    """Test the pagination endpoint."""
    # Test with different page parameters
    response = client.get("/techniques/pagination?page=1&size=10")
    assert response.status_code == 200
    
    # Verify pagination metadata
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    
    # Test invalid parameters
    response = client.get("/techniques/pagination?page=0&size=0")
    assert response.status_code == 422  # Validation error


def test_n_plus_1_endpoint(client):
    """Test the N+1 query optimization endpoint."""
    # Test the standard endpoint
    response = client.get("/techniques/avoid-n-plus-1")
    assert response.status_code == 200
    
    # Verify we get a list of posts
    data = response.json()
    assert isinstance(data, list)


def test_compression_endpoint(client):
    """Test the compression endpoint."""
    # Test without compression
    response = client.get("/techniques/compression")
    assert response.status_code == 200
    
    # Test with compression
    headers = {"Accept-Encoding": "br, gzip"}
    response = client.get("/techniques/compression?compressed=true", headers=headers)
    assert response.status_code == 200
    
    # If compression is applied, there should be a Content-Encoding header
    if "compressed=true" in response.request.url:
        assert "content-encoding" in [h.lower() for h in response.headers] 
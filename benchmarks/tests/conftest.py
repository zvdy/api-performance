"""
Configuration and fixtures for benchmark tests.
"""
import pytest
from unittest.mock import MagicMock
import sys
import os


# Add the project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


@pytest.fixture
def mock_response():
    """
    Fixture that provides a mock HTTP response.
    """
    response = MagicMock()
    response.status_code = 200
    response.elapsed.total_seconds.return_value = 0.1
    response.headers = {"content-length": "1024", "content-type": "application/json"}
    response.content = b'{"test": "data"}'
    return response


@pytest.fixture
def sample_benchmark_results():
    """
    Fixture that provides sample benchmark results for testing.
    """
    return {
        "with_optimization": [
            {"status_code": 200, "response_time_ms": 10.0, "content_size": 100, "success": True},
            {"status_code": 200, "response_time_ms": 12.0, "content_size": 100, "success": True},
            {"status_code": 200, "response_time_ms": 8.0, "content_size": 100, "success": True},
        ],
        "without_optimization": [
            {"status_code": 200, "response_time_ms": 20.0, "content_size": 200, "success": True},
            {"status_code": 200, "response_time_ms": 22.0, "content_size": 200, "success": True},
            {"status_code": 200, "response_time_ms": 18.0, "content_size": 200, "success": True},
        ]
    } 
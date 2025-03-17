"""
Test configuration and fixtures for the API tests.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Create mock for the database connection
@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock = MagicMock()
    mock.execute = AsyncMock()
    mock.fetch_all = AsyncMock(return_value=[])
    mock.fetch_one = AsyncMock(return_value={})
    return mock

# Patch the app's database connection - with create=True to handle missing attributes
@pytest.fixture(autouse=True)
def patch_app_db(mock_db):
    """Patch the app module to have a db attribute, creating it if not exists."""
    with patch("api.app.db", mock_db, create=True):
        yield

# Mock Redis
@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.exists = AsyncMock(return_value=0)
    return mock

# Patch Redis
@pytest.fixture(autouse=True)
def patch_redis(mock_redis):
    """Patch the Redis client."""
    with patch("api.techniques.caching.redis", mock_redis, create=True):
        yield

# Create a test client for API testing
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Import inside function to allow for patching
    from api.app import app
    
    # Return the test client
    with TestClient(app) as client:
        yield client

# Mock for asyncpg pool
@pytest.fixture
def mock_pool():
    """Create a mock connection pool."""
    mock = MagicMock()
    mock.acquire = AsyncMock().__aenter__.return_value = AsyncMock()
    mock.release = AsyncMock()
    mock.close = AsyncMock()
    return mock

# Patch the pool in connection_pool.py
@pytest.fixture(autouse=True)
def patch_connection_pool(mock_pool):
    """Patch the connection pool."""
    with patch("api.techniques.connection_pool.pool", mock_pool, create=True):
        yield

# Create a mock for API responses
@pytest.fixture
def mock_response_data():
    """Sample response data for testing."""
    return {
        "id": 1,
        "title": "Test Post",
        "content": "This is a test post",
        "user": {
            "id": 1,
            "username": "testuser"
        },
        "comments": [
            {"id": 1, "content": "Test comment"}
        ]
    }

# Patch the various technique module functions
@pytest.fixture(autouse=True)
def patch_technique_modules():
    """Patch various technique module functions."""
    with patch("api.techniques.caching.generate_cache_key", 
               return_value="test_key", create=True), \
         patch("api.techniques.pagination.paginate_query", 
               return_value=([], 0, 1, 10), create=True), \
         patch("api.techniques.avoid_n_plus_1.get_posts_with_users_and_comments", 
               AsyncMock(return_value=[]), create=True), \
         patch("api.techniques.json_serialization.serialize_json", 
               MagicMock(return_value=b"{}"), create=True), \
         patch("api.techniques.compression.compress_response", 
               MagicMock(return_value=(b"{}", {"Content-Encoding": "br"})), create=True), \
         patch("api.techniques.async_logging.log_request", 
               AsyncMock(), create=True), \
         patch("api.techniques.async_logging.calculate_async_logging_statistics", 
               AsyncMock(return_value={"avg_processing_time": 0.1}), create=True):
        yield 
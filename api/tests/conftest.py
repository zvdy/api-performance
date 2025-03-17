"""
Configuration and fixtures for API tests.
"""
import pytest
from unittest.mock import MagicMock
import sys
import os


# Add the project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


@pytest.fixture
def mock_db():
    """
    Fixture that provides a mock database connection.
    """
    db = MagicMock()
    
    # Set up common mock behaviors
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (100,)
    db.execute.return_value = mock_cursor
    
    return db


@pytest.fixture
def mock_redis():
    """
    Fixture that provides a mock Redis connection.
    """
    redis = MagicMock()
    
    # Set up common mock behaviors
    redis.get.return_value = None
    redis.set.return_value = True
    
    return redis 
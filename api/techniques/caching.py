"""
Caching Module - Technique #1

This module demonstrates Redis-based caching to improve API performance
by storing expensive operations results and retrieving them on subsequent requests.
"""

import asyncio
from typing import Any, Optional
import redis
import logging

logger = logging.getLogger(__name__)

async def setup_cache(redis_host: str = 'localhost', redis_port: int = 6379) -> redis.Redis:
    """Initialize and return Redis client for caching"""
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True
    )

async def get_cache(redis_client: redis.Redis, key: str) -> Optional[str]:
    """
    Get data from cache asynchronously
    
    Args:
        redis_client: Redis client instance
        key: Cache key to retrieve
        
    Returns:
        Cached data if found, None otherwise
    """
    try:
        # Execute Redis GET command in a non-blocking way
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: redis_client.get(key)
        )
        return result
    except Exception as e:
        logger.warning(f"Cache retrieval error: {str(e)}")
        return None

async def set_cache(redis_client: redis.Redis, key: str, value: Any, expiry: int = 300) -> bool:
    """
    Store data in cache asynchronously with expiration time
    
    Args:
        redis_client: Redis client instance
        key: Cache key to store
        value: Data to cache
        expiry: Time-to-live in seconds (default: 5 minutes)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Execute Redis SET command in a non-blocking way
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: redis_client.setex(key, expiry, value)
        )
        return True
    except Exception as e:
        logger.warning(f"Cache storage error: {str(e)}")
        return False

async def invalidate_cache(redis_client: redis.Redis, key: str) -> bool:
    """
    Delete a key from cache
    
    Args:
        redis_client: Redis client instance
        key: Cache key to delete
        
    Returns:
        True if deleted, False otherwise
    """
    try:
        # Execute Redis DEL command in a non-blocking way
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: redis_client.delete(key)
        )
        return bool(result)
    except Exception as e:
        logger.warning(f"Cache invalidation error: {str(e)}")
        return False

async def clear_cache_pattern(redis_client: redis.Redis, pattern: str) -> int:
    """
    Delete all keys matching a pattern
    
    Args:
        redis_client: Redis client instance
        pattern: Redis key pattern to match (e.g., "user:*")
        
    Returns:
        Number of keys deleted
    """
    try:
        # Execute in a non-blocking way
        loop = asyncio.get_event_loop()
        
        # First get keys matching pattern
        keys = await loop.run_in_executor(
            None,
            lambda: redis_client.keys(pattern)
        )
        
        if not keys:
            return 0
        
        # Then delete them all
        deleted = await loop.run_in_executor(
            None,
            lambda: redis_client.delete(*keys)
        )
        
        return deleted
    except Exception as e:
        logger.warning(f"Cache pattern clearing error: {str(e)}")
        return 0 
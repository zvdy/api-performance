import os
import time
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, Header, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, select
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declarative_base
from databases import Database
import redis
import ujson
import orjson
import json
from pydantic import BaseModel
import logging
import structlog
import asyncio
from starlette_exporter import PrometheusMiddleware, handle_metrics

# Import our optimization technique modules
from techniques.caching import setup_cache, get_cache, set_cache, invalidate_cache
from techniques.connection_pool import get_db, get_async_db
from techniques.avoid_n_plus_1 import get_posts_with_comments, get_posts_with_comments_optimized, get_posts_with_comments_joins
from techniques.pagination import paginate_results
from techniques.json_serialization import serialize_standard, serialize_optimized
from techniques.compression import compress_response
from techniques.async_logging import setup_async_logging, log_request

# Configure application
app = FastAPI(
    title="API Performance Techniques",
    description="Demonstration of 7 techniques to optimize API performance",
    version="1.0.0",
    default_response_class=ORJSONResponse,  # Use ORJSONResponse for faster JSON serialization
)

# Setup middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Enable GZip compression
app.add_middleware(PrometheusMiddleware)  # Add metrics endpoint for monitoring
app.add_route("/metrics", handle_metrics)

# Database configuration
DATABASE_URL = f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@{os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5432')}/{os.environ.get('POSTGRES_DB', 'api_performance')}"

# Redis configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

# Setup database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()

# Setup async database
database = Database(DATABASE_URL)

# Setup Redis for caching
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    decode_responses=True
)

# Setup logging
logger = setup_async_logging()

# Define Pydantic models for API responses
class Author(BaseModel):
    id: int
    name: str
    email: str
    bio: Optional[str] = None

class Comment(BaseModel):
    id: int
    post_id: int
    author_name: str
    content: str
    created_at: str

class Tag(BaseModel):
    id: int
    name: str

class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    published: bool
    views: int
    created_at: str
    comments: Optional[List[Comment]] = None
    tags: Optional[List[Tag]] = None
    author: Optional[Author] = None

class PaginatedPosts(BaseModel):
    items: List[Post]
    total: int
    page: int
    size: int
    pages: int
    next_page: Optional[str] = None
    prev_page: Optional[str] = None

@app.on_event("startup")
async def startup():
    try:
        await database.connect()
        logger.info("API started and connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    logger.info("API shutting down")

# Demo endpoints for each optimization technique

@app.get("/", response_class=ORJSONResponse)
async def root():
    """Root endpoint returning information about available optimization techniques"""
    return {
        "message": "API Performance Optimization Techniques",
        "techniques": [
            {"id": 1, "name": "Caching", "endpoint": "/techniques/caching"},
            {"id": 2, "name": "Connection Pooling", "endpoint": "/techniques/connection-pool"},
            {"id": 3, "name": "Avoid N+1 Query Problem", "endpoint": "/techniques/avoid-n-plus-1"},
            {"id": 4, "name": "Pagination", "endpoint": "/techniques/pagination"},
            {"id": 5, "name": "Lightweight JSON Serialization", "endpoint": "/techniques/json-serialization"},
            {"id": 6, "name": "Compression", "endpoint": "/techniques/compression"},
            {"id": 7, "name": "Asynchronous Logging", "endpoint": "/techniques/async-logging"}
        ]
    }

# 1. Caching example
@app.get("/techniques/caching", response_model=List[Post])
async def get_posts_with_caching(
    cache: bool = Query(True, description="Enable/disable caching"),
    db = Depends(get_async_db)
):
    """
    Get a list of posts with Redis caching
    
    - With caching enabled: Tries to fetch from cache first, falls back to DB
    - With caching disabled: Always fetches from DB
    """
    cache_key = "all_posts"
    log_request("Caching endpoint called", {"cache_enabled": cache})
    
    if cache:
        # Try to get data from cache first
        cached_data = await get_cache(redis_client, cache_key)
        if cached_data:
            logger.info("Cache hit", cache_key=cache_key)
            return orjson.loads(cached_data)
    
    # If no cache or cache disabled, query database
    logger.info("Cache miss or disabled", cache_key=cache_key, cache_enabled=cache)
    query = "SELECT id, title, content, author_id, published, views, created_at::text FROM posts LIMIT 20"
    results = await db.fetch_all(query)
    
    # Convert to list of dictionaries
    posts = [dict(row) for row in results]
    
    # Store in cache if caching is enabled
    if cache:
        await set_cache(redis_client, cache_key, orjson.dumps(posts), expiry=60)
    
    return posts

# 2. Connection Pooling example
@app.get("/techniques/connection-pool")
async def connection_pool_demo(pooled: bool = Query(True, description="Use connection pool")):
    """
    Demonstrate the impact of connection pooling
    
    - With pooling: Uses the existing connection from the pool
    - Without pooling: Creates a new connection for each request
    """
    start_time = time.time()
    
    if pooled:
        # Use pooled connection
        db = await get_async_db()
        query = "SELECT 1 as result"
        result = await db.fetch_one(query)
    else:
        # Create a new connection each time (simulated - don't actually do this in production!)
        temp_db_url = DATABASE_URL
        temp_db = Database(temp_db_url)
        await temp_db.connect()
        query = "SELECT 1 as result"
        result = await temp_db.fetch_one(query)
        await temp_db.disconnect()
    
    elapsed = time.time() - start_time
    
    return {
        "technique": "Connection Pooling",
        "pooled": pooled,
        "execution_time_ms": round(elapsed * 1000, 2),
        "result": dict(result) if result else None
    }

# 3. Avoid N+1 Query Problem
@app.get("/techniques/avoid-n-plus-1", response_model=List[Post])
async def n_plus_1_demo(
    optimized: bool = Query(True, description="Use optimized query pattern"),
    db = Depends(get_async_db)
):
    """
    Demonstrate the N+1 query problem and its solution
    
    - With optimization: Uses a single query with JOIN
    - Without optimization: Makes N+1 separate database queries
    """
    start_time = time.time()
    
    if optimized:
        # Use JOIN approach instead of the 2-query approach for better performance
        posts = await get_posts_with_comments_joins(db)
    else:
        posts = await get_posts_with_comments(db)
    
    elapsed = time.time() - start_time
    
    # Add execution time as header in response
    response = ORJSONResponse(content=posts)
    response.headers["X-Execution-Time"] = f"{round(elapsed * 1000, 2)}ms"
    
    return response

# 4. Pagination
@app.get("/techniques/pagination", response_model=PaginatedPosts)
async def pagination_demo(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    db = Depends(get_async_db)
):
    """
    Demonstrate the impact of pagination on response time and payload size
    """
    return await paginate_results(db, page, size)

# 5. Lightweight JSON Serialization
@app.get("/techniques/json-serialization")
async def json_serialization_demo(
    optimized: bool = Query(True, description="Use optimized JSON serialization"),
    db = Depends(get_async_db)
):
    """
    Demonstrate the performance difference between standard and optimized JSON serialization
    
    - With optimization: Uses a fast JSON library (orjson)
    - Without optimization: Uses standard json library
    """
    # Get some data to serialize
    query = "SELECT * FROM posts LIMIT 100"
    results = await db.fetch_all(query)
    posts = [dict(row) for row in results]
    
    # Time both serialization methods
    if optimized:
        start_time = time.time()
        serialized = serialize_optimized(posts)
        elapsed = time.time() - start_time
        method = "optimized (orjson)"
        serialized_size = len(serialized)
    else:
        start_time = time.time()
        serialized = serialize_standard(posts)
        elapsed = time.time() - start_time
        method = "standard (json)"
        serialized_size = len(serialized.encode('utf-8'))  # Convert string to bytes to get size
    
    return {
        "technique": "Lightweight JSON Serialization",
        "method": method,
        "serialization_time_ms": round(elapsed * 1000, 4),
        "serialized_size_bytes": serialized_size,
    }

# 6. Compression
@app.get("/techniques/compression")
async def compression_demo(
    response: Response,
    compressed: bool = Query(True, description="Use response compression"),
    db = Depends(get_async_db)
):
    """
    Demonstrate the impact of response compression
    
    - With compression: Response is compressed using Brotli or Gzip
    - Without compression: Raw response without compression
    """
    # Get a more reasonable sized dataset to demonstrate compression
    query = "SELECT * FROM posts LIMIT 10"
    results = await db.fetch_all(query)
    large_payload = [dict(row) for row in results]
    
    # Return simplified data for demonstration
    response_data = {
        "technique": "Compression",
        "compressed": compressed,
        "payload_sample": large_payload[:3],  # Only return the first 3 items in sample
        "total_items": len(large_payload)
    }
    
    # For the compression demo, we'll rely on FastAPI's built-in GZipMiddleware
    # which is already configured in the app setup
    if compressed:
        # Add header to indicate compression was requested
        response.headers["X-Compression-Requested"] = "true"
    
    return response_data

# 7. Asynchronous Logging
@app.get("/techniques/async-logging")
async def async_logging_demo(
    async_logging: bool = Query(True, description="Use asynchronous logging"),
    log_level: str = Query("info", description="Logging level (debug, info, warning, error)"),
    message_count: int = Query(10, ge=1, le=1000, description="Number of log messages to generate")
):
    """
    Demonstrate the performance impact of asynchronous vs. synchronous logging
    
    - With async logging: Log messages are processed in a separate thread
    - Without async logging: Log messages block the main thread
    """
    start_time = time.time()
    
    # Generate the specified number of log messages
    for i in range(message_count):
        if async_logging:
            # Use our async logging implementation
            log_request(
                f"Log message {i}", 
                {"level": log_level, "async": True, "timestamp": time.time()}
            )
        else:
            # Use synchronous logging
            if log_level == "debug":
                logging.debug(f"Log message {i}")
            elif log_level == "info":
                logging.info(f"Log message {i}")
            elif log_level == "warning":
                logging.warning(f"Log message {i}")
            else:
                logging.error(f"Log message {i}")
    
    elapsed = time.time() - start_time
    
    return {
        "technique": "Asynchronous Logging",
        "async_logging": async_logging,
        "log_level": log_level,
        "message_count": message_count,
        "execution_time_ms": round(elapsed * 1000, 2)
    }

# Provide combined endpoint to test all optimizations together
@app.get("/techniques/all")
async def all_optimizations_demo(
    response: Response,
    use_caching: bool = Query(True),
    use_connection_pool: bool = Query(True),
    avoid_n_plus_1: bool = Query(True),
    use_pagination: bool = Query(True),
    use_optimized_json: bool = Query(True),
    use_compression: bool = Query(True),
    use_async_logging: bool = Query(True),
    db = Depends(get_async_db)
):
    """
    Demonstrate all optimization techniques together
    """
    start_time = time.time()
    results = {}
    
    # Run each optimization based on parameters
    if use_caching:
        cache_key = "demo_all_posts"
        cached_data = await get_cache(redis_client, cache_key)
        if cached_data:
            posts = orjson.loads(cached_data)
        else:
            query = "SELECT id, title, content, author_id, published, views, created_at::text FROM posts LIMIT 20"
            results_data = await db.fetch_all(query)
            posts = [dict(row) for row in results_data]
            await set_cache(redis_client, cache_key, orjson.dumps(posts), expiry=60)
        results["cached_posts"] = len(posts)
    
    if avoid_n_plus_1:
        if use_optimized_json:
            posts = await get_posts_with_comments_joins(db)
        else:
            posts = await get_posts_with_comments(db)
        results["posts_with_comments"] = len(posts)
    
    if use_pagination:
        paginated = await paginate_results(db, 1, 10)
        results["paginated_data"] = {
            "total": paginated["total"],
            "page": paginated["page"],
            "pages": paginated["pages"]
        }
    
    if use_async_logging:
        for i in range(5):
            log_request("Demo all optimizations", {"test_run": i})
    
    elapsed = time.time() - start_time
    
    response_data = {
        "message": "All optimizations demo",
        "execution_time_ms": round(elapsed * 1000, 2),
        "optimizations_used": {
            "caching": use_caching,
            "connection_pool": use_connection_pool,
            "avoid_n_plus_1": avoid_n_plus_1,
            "pagination": use_pagination,
            "optimized_json": use_optimized_json,
            "compression": use_compression,
            "async_logging": use_async_logging
        },
        "results": results
    }
    
    # Apply compression if requested
    if use_compression:
        return await compress_response(response_data, response)
    
    return response_data 
"""
API Performance Optimization Techniques Package

This package contains modules demonstrating 7 different techniques to optimize API performance:
1. Caching - Store results of expensive operations
2. Connection Pooling - Reuse database connections
3. Avoid N+1 Query Problem - Optimize database query patterns
4. Pagination - Limit response data size
5. Lightweight JSON Serialization - Use optimized serialization
6. Compression - Reduce network payload size
7. Asynchronous Logging - Non-blocking log operations
"""

from .caching import get_cache, set_cache, invalidate_cache, clear_cache_pattern
from .connection_pool import get_db, get_async_db
from .avoid_n_plus_1 import get_posts_with_comments, get_posts_with_comments_optimized
from .pagination import paginate_results, cursor_based_pagination
from .json_serialization import serialize_standard, serialize_optimized, serialize_ujson
from .compression import compress_response, compress_with_gzip, compress_with_brotli
from .async_logging import setup_async_logging, log_request, stop_async_logging

__all__ = [
    # Caching
    'get_cache', 'set_cache', 'invalidate_cache', 'clear_cache_pattern',
    
    # Connection Pooling
    'get_db', 'get_async_db',
    
    # Avoid N+1 Query Problem
    'get_posts_with_comments', 'get_posts_with_comments_optimized',
    
    # Pagination
    'paginate_results', 'cursor_based_pagination',
    
    # Lightweight JSON Serialization
    'serialize_standard', 'serialize_optimized', 'serialize_ujson',
    
    # Compression
    'compress_response', 'compress_with_gzip', 'compress_with_brotli',
    
    # Asynchronous Logging
    'setup_async_logging', 'log_request', 'stop_async_logging'
] 
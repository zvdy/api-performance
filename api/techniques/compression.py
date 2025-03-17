"""
Compression Module - Technique #6

This module demonstrates how to implement response compression to improve API performance
by reducing the size of data transferred over the network.
"""

import gzip
import brotli
import orjson
from fastapi.responses import Response
from typing import Any, Dict
import logging
import time

logger = logging.getLogger(__name__)

async def compress_response(data: Any, response: Response) -> Response:
    """
    Compress API response data using Brotli or Gzip based on client capabilities
    
    Args:
        data: Data to compress and return
        response: FastAPI Response object to modify
        
    Returns:
        Compressed response
    """
    # Serialize data to bytes using orjson (fast JSON serialization)
    json_bytes = orjson.dumps(data)
    
    # Get original size for logging/comparison
    original_size = len(json_bytes)
    
    try:
        # Choose compression algorithm (Brotli preferred for better compression)
        # In a real-world scenario, this would check Accept-Encoding header
        # For this demo, we'll use Brotli as it generally provides better compression
        compressed_data = brotli.compress(json_bytes, quality=4)  # Use a lower quality setting for speed
        compressed_size = len(compressed_data)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        compression_algorithm = "br"  # Brotli
        
        # Set appropriate headers
        response.headers["Content-Encoding"] = compression_algorithm
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Length"] = str(compressed_size)
        response.headers["X-Original-Size"] = str(original_size)
        response.headers["X-Compressed-Size"] = str(compressed_size)
        response.headers["X-Compression-Ratio"] = f"{compression_ratio:.2f}"
        
        # Set body content
        response.body = compressed_data
        
        # Log compression results
        logger.info(
            f"Response compressed: {original_size} -> {compressed_size} bytes "
            f"({compression_ratio:.2f}x) using {compression_algorithm}"
        )
        
        return response
    except Exception as e:
        # If compression fails, return uncompressed data
        logger.error(f"Compression failed: {str(e)}")
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Length"] = str(original_size)
        response.body = json_bytes
        return response

def compress_with_gzip(data: bytes) -> bytes:
    """
    Compress data using Gzip
    
    Args:
        data: Bytes to compress
        
    Returns:
        Gzip compressed bytes
    """
    return gzip.compress(data, compresslevel=6)

def compress_with_brotli(data: bytes) -> bytes:
    """
    Compress data using Brotli
    
    Args:
        data: Bytes to compress
        
    Returns:
        Brotli compressed bytes
    """
    return brotli.compress(data, quality=6)

def compare_compression_algorithms(data: bytes) -> Dict[str, Any]:
    """
    Compare different compression algorithms on the same data
    
    Args:
        data: Bytes to compress
        
    Returns:
        Dictionary with compression statistics for each algorithm
    """
    original_size = len(data)
    
    # Gzip compression
    gzip_start = time.time()
    gzip_data = compress_with_gzip(data)
    gzip_time = time.time() - gzip_start
    gzip_size = len(gzip_data)
    
    # Brotli compression
    brotli_start = time.time()
    brotli_data = compress_with_brotli(data)
    brotli_time = time.time() - brotli_start
    brotli_size = len(brotli_data)
    
    return {
        "original_size": original_size,
        "gzip": {
            "size": gzip_size,
            "ratio": original_size / gzip_size if gzip_size > 0 else 0,
            "time_ms": gzip_time * 1000
        },
        "brotli": {
            "size": brotli_size,
            "ratio": original_size / brotli_size if brotli_size > 0 else 0,
            "time_ms": brotli_time * 1000
        }
    } 
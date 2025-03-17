"""
JSON Serialization Module - Technique #5

This module demonstrates the performance differences between standard JSON serialization
and optimized JSON serialization using libraries like orjson and ujson.
"""

import json
import ujson
import orjson
import time
from typing import Any, Dict, List
import datetime

def serialize_standard(data: Any) -> str:
    """
    Serialize data using Python's standard json library
    
    Args:
        data: Data to serialize to JSON
        
    Returns:
        JSON string
    """
    # Add a custom encoder for datetime objects
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return super().default(obj)
    
    return json.dumps(data, cls=DateTimeEncoder)

def serialize_optimized(data: Any) -> bytes:
    """
    Serialize data using the orjson library (much faster)
    
    Args:
        data: Data to serialize to JSON
        
    Returns:
        JSON bytes (needs to be decoded to string if needed)
    """
    return orjson.dumps(data)

def serialize_ujson(data: Any) -> str:
    """
    Serialize data using the ujson library (faster but less feature-rich than orjson)
    
    Args:
        data: Data to serialize to JSON
        
    Returns:
        JSON string
    """
    return ujson.dumps(data)

def deserialize_standard(json_str: str) -> Any:
    """
    Deserialize JSON string using Python's standard json library
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        Deserialized data
    """
    return json.loads(json_str)

def deserialize_optimized(json_bytes: bytes) -> Any:
    """
    Deserialize JSON bytes using the orjson library
    
    Args:
        json_bytes: JSON bytes to deserialize
        
    Returns:
        Deserialized data
    """
    return orjson.loads(json_bytes)

def deserialize_ujson(json_str: str) -> Any:
    """
    Deserialize JSON string using the ujson library
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        Deserialized data
    """
    return ujson.loads(json_str)

def benchmark_serialization(data: Any, iterations: int = 1000) -> Dict[str, float]:
    """
    Benchmark different JSON serialization methods
    
    Args:
        data: Data to serialize
        iterations: Number of iterations for the benchmark
        
    Returns:
        Dictionary with benchmark results
    """
    results = {}
    
    # Benchmark standard json
    start_time = time.time()
    for _ in range(iterations):
        json_str = serialize_standard(data)
    std_time = time.time() - start_time
    results["standard_json"] = std_time
    
    # Benchmark orjson
    start_time = time.time()
    for _ in range(iterations):
        json_bytes = serialize_optimized(data)
    orjson_time = time.time() - start_time
    results["orjson"] = orjson_time
    
    # Benchmark ujson
    start_time = time.time()
    for _ in range(iterations):
        json_str = serialize_ujson(data)
    ujson_time = time.time() - start_time
    results["ujson"] = ujson_time
    
    # Calculate speedups
    results["orjson_speedup"] = std_time / orjson_time if orjson_time > 0 else float('inf')
    results["ujson_speedup"] = std_time / ujson_time if ujson_time > 0 else float('inf')
    
    return results

def benchmark_deserialization(json_data: Any, iterations: int = 1000) -> Dict[str, float]:
    """
    Benchmark different JSON deserialization methods
    
    Args:
        json_data: JSON data to deserialize
        iterations: Number of iterations for the benchmark
        
    Returns:
        Dictionary with benchmark results
    """
    # Prepare test data
    json_str = serialize_standard(json_data)
    json_bytes = serialize_optimized(json_data)
    
    results = {}
    
    # Benchmark standard json
    start_time = time.time()
    for _ in range(iterations):
        data = deserialize_standard(json_str)
    std_time = time.time() - start_time
    results["standard_json"] = std_time
    
    # Benchmark orjson
    start_time = time.time()
    for _ in range(iterations):
        data = deserialize_optimized(json_bytes)
    orjson_time = time.time() - start_time
    results["orjson"] = orjson_time
    
    # Benchmark ujson
    start_time = time.time()
    for _ in range(iterations):
        data = deserialize_ujson(json_str)
    ujson_time = time.time() - start_time
    results["ujson"] = ujson_time
    
    # Calculate speedups
    results["orjson_speedup"] = std_time / orjson_time if orjson_time > 0 else float('inf')
    results["ujson_speedup"] = std_time / ujson_time if ujson_time > 0 else float('inf')
    
    return results 
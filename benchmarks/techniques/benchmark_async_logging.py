"""
Asynchronous Logging Benchmark Module

This module benchmarks the performance improvement from using asynchronous logging.
"""

import time
import statistics
import httpx
import asyncio
import json
from typing import Dict, Any, List
import os

async def benchmark_request(client: httpx.AsyncClient, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Make a benchmark request and measure response time
    
    Args:
        client: HTTP client
        url: URL to request
        params: Query parameters
        
    Returns:
        Dictionary with request metrics
    """
    start_time = time.time()
    response = await client.get(url, params=params)
    end_time = time.time()
    
    elapsed_ms = (end_time - start_time) * 1000
    
    result = {
        "status_code": response.status_code,
        "response_time_ms": elapsed_ms,
        "success": response.status_code == 200
    }
    
    # Store response headers that might be useful for analysis
    headers = {}
    for key in ["x-execution-time", "content-length"]:
        if key in response.headers:
            headers[key] = response.headers[key]
    
    if headers:
        result["headers"] = headers
    
    return result

async def benchmark_async_logging_single(base_url: str, async_enabled: bool) -> List[Dict[str, Any]]:
    """
    Benchmark a single async logging request
    
    Args:
        base_url: Base URL of the API
        async_enabled: Whether to use async logging
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/async-logging"
    params = {
        "async_logging": "true" if async_enabled else "false", 
        "message_count": 50,
        "log_level": "info"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform 5 requests
        results = []
        for _ in range(5):
            result = await benchmark_request(client, url, params)
            results.append(result)
            # Add a small delay between requests
            await asyncio.sleep(0.1)
    
    return results

async def benchmark_async_logging_concurrent(base_url: str, async_enabled: bool, concurrency: int = 10) -> List[Dict[str, Any]]:
    """
    Benchmark async logging with concurrent requests
    
    Args:
        base_url: Base URL of the API
        async_enabled: Whether to use async logging
        concurrency: Number of concurrent requests
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/async-logging"
    params = {
        "async_logging": "true" if async_enabled else "false", 
        "message_count": 50,
        "log_level": "info"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform concurrent requests
        tasks = []
        for _ in range(concurrency):
            tasks.append(benchmark_request(client, url, params))
        
        results = await asyncio.gather(*tasks)
    
    return results

def run_async_logging_benchmark(base_url: str, iterations: int = 3, concurrency: int = 10) -> Dict[str, Any]:
    """
    Run the asynchronous logging benchmark
    
    Args:
        base_url: Base URL of the API
        iterations: Number of iterations
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "technique": "Asynchronous Logging",
        "base_url": base_url,
        "iterations": iterations,
        "concurrency": concurrency,
        "timestamp": time.time(),
        "single_request": {
            "async": [],
            "sync": []
        },
        "concurrent_requests": {
            "async": [],
            "sync": []
        }
    }
    
    # Run single request benchmarks
    for i in range(iterations):
        print(f"Running single request benchmark iteration {i+1}/{iterations}...")
        
        # Sync logging
        sync_results = asyncio.run(benchmark_async_logging_single(base_url, False))
        results["single_request"]["sync"].extend(sync_results)
        
        # Async logging
        async_results = asyncio.run(benchmark_async_logging_single(base_url, True))
        results["single_request"]["async"].extend(async_results)
    
    # Run concurrent request benchmarks
    for i in range(iterations):
        print(f"Running concurrent request benchmark iteration {i+1}/{iterations}...")
        
        # Sync logging
        sync_results = asyncio.run(benchmark_async_logging_concurrent(base_url, False, concurrency))
        results["concurrent_requests"]["sync"].extend(sync_results)
        
        # Async logging
        async_results = asyncio.run(benchmark_async_logging_concurrent(base_url, True, concurrency))
        results["concurrent_requests"]["async"].extend(async_results)
    
    # Calculate statistics
    summary = calculate_async_logging_statistics(results)
    results["summary"] = summary
    
    # Print summary
    print("\nAsync Logging Benchmark Summary:")
    print(f"Average response time sync: {summary['sync']['avg_response_time_ms']:.2f} ms")
    print(f"Average response time async: {summary['async']['avg_response_time_ms']:.2f} ms")
    print(f"Improvement factor: {summary['improvement_factor']:.2f}x")
    
    return results

def calculate_async_logging_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics from benchmark results
    
    Args:
        results: Benchmark results
        
    Returns:
        Dictionary with statistics
    """
    # Extract response times
    sync_times = []
    async_times = []
    
    # Process single request results
    for result in results["single_request"]["sync"]:
        if result["success"]:
            sync_times.append(result["response_time_ms"])
    
    for result in results["single_request"]["async"]:
        if result["success"]:
            async_times.append(result["response_time_ms"])
    
    # Process concurrent request results
    for result in results["concurrent_requests"]["sync"]:
        if result["success"]:
            sync_times.append(result["response_time_ms"])
    
    for result in results["concurrent_requests"]["async"]:
        if result["success"]:
            async_times.append(result["response_time_ms"])
    
    # Calculate statistics
    sync_stats = {
        "avg_response_time_ms": statistics.mean(sync_times) if sync_times else 0,
        "min_response_time_ms": min(sync_times) if sync_times else 0,
        "max_response_time_ms": max(sync_times) if sync_times else 0,
        "median_response_time_ms": statistics.median(sync_times) if sync_times else 0,
        "stdev_response_time_ms": statistics.stdev(sync_times) if len(sync_times) > 1 else 0,
        "sample_size": len(sync_times)
    }
    
    async_stats = {
        "avg_response_time_ms": statistics.mean(async_times) if async_times else 0,
        "min_response_time_ms": min(async_times) if async_times else 0,
        "max_response_time_ms": max(async_times) if async_times else 0,
        "median_response_time_ms": statistics.median(async_times) if async_times else 0,
        "stdev_response_time_ms": statistics.stdev(async_times) if len(async_times) > 1 else 0,
        "sample_size": len(async_times)
    }
    
    # Calculate improvement factor
    if sync_stats["avg_response_time_ms"] > 0 and async_stats["avg_response_time_ms"] > 0:
        improvement_factor = sync_stats["avg_response_time_ms"] / async_stats["avg_response_time_ms"]
    else:
        improvement_factor = 0
    
    # Calculate requests per second
    if sync_stats["avg_response_time_ms"] > 0:
        sync_rps = 1000 / sync_stats["avg_response_time_ms"]
    else:
        sync_rps = 0
    
    if async_stats["avg_response_time_ms"] > 0:
        async_rps = 1000 / async_stats["avg_response_time_ms"]
    else:
        async_rps = 0
    
    sync_stats["requests_per_second"] = sync_rps
    async_stats["requests_per_second"] = async_rps
    
    return {
        "sync": sync_stats,
        "async": async_stats,
        "improvement_factor": improvement_factor,
        "avg_response_time_ms": async_stats["avg_response_time_ms"],
        "requests_per_second": async_rps
    }

if __name__ == "__main__":
    # Run benchmark when called directly
    base_url = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    results = run_async_logging_benchmark(base_url)
    
    # Save results to file
    with open("async_logging_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to async_logging_benchmark_results.json")

"""
Caching Benchmark Module

This module benchmarks the performance improvement from using Redis caching.
"""

import time
import statistics
import httpx
import asyncio
import json
from typing import Dict, Any, List
import os
from concurrent.futures import ThreadPoolExecutor

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
    for key in ["x-execution-time", "x-cache-hit", "content-length"]:
        if key in response.headers:
            headers[key] = response.headers[key]
    
    if headers:
        result["headers"] = headers
    
    return result

async def benchmark_caching_single(base_url: str, cache_enabled: bool) -> List[Dict[str, Any]]:
    """
    Benchmark a single caching request
    
    Args:
        base_url: Base URL of the API
        cache_enabled: Whether to use cache
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/caching"
    params = {"cache": "true" if cache_enabled else "false"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform 5 requests
        results = []
        for _ in range(5):
            result = await benchmark_request(client, url, params)
            results.append(result)
            # Add a small delay between requests
            await asyncio.sleep(0.1)
    
    return results

async def benchmark_caching_concurrent(base_url: str, cache_enabled: bool, concurrency: int = 10) -> List[Dict[str, Any]]:
    """
    Benchmark caching with concurrent requests
    
    Args:
        base_url: Base URL of the API
        cache_enabled: Whether to use cache
        concurrency: Number of concurrent requests
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/caching"
    params = {"cache": "true" if cache_enabled else "false"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform concurrent requests
        tasks = []
        for _ in range(concurrency):
            tasks.append(benchmark_request(client, url, params))
        
        results = await asyncio.gather(*tasks)
    
    return results

def run_caching_benchmark(base_url: str, iterations: int = 3, concurrency: int = 10) -> Dict[str, Any]:
    """
    Run the caching benchmark
    
    Args:
        base_url: Base URL of the API
        iterations: Number of iterations
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "technique": "Caching",
        "base_url": base_url,
        "iterations": iterations,
        "concurrency": concurrency,
        "timestamp": time.time(),
        "single_request": {
            "with_cache": [],
            "without_cache": []
        },
        "concurrent_requests": {
            "with_cache": [],
            "without_cache": []
        }
    }
    
    # Run single request benchmarks
    for i in range(iterations):
        print(f"Running single request benchmark iteration {i+1}/{iterations}...")
        
        # Without cache
        without_cache_results = asyncio.run(benchmark_caching_single(base_url, False))
        results["single_request"]["without_cache"].extend(without_cache_results)
        
        # With cache
        with_cache_results = asyncio.run(benchmark_caching_single(base_url, True))
        results["single_request"]["with_cache"].extend(with_cache_results)
    
    # Run concurrent request benchmarks
    for i in range(iterations):
        print(f"Running concurrent request benchmark iteration {i+1}/{iterations}...")
        
        # Without cache
        without_cache_results = asyncio.run(benchmark_caching_concurrent(base_url, False, concurrency))
        results["concurrent_requests"]["without_cache"].extend(without_cache_results)
        
        # With cache
        with_cache_results = asyncio.run(benchmark_caching_concurrent(base_url, True, concurrency))
        results["concurrent_requests"]["with_cache"].extend(with_cache_results)
    
    # Calculate statistics
    summary = calculate_caching_statistics(results)
    results["summary"] = summary
    
    # Print summary
    print("\nCaching Benchmark Summary:")
    print(f"Average response time without cache: {summary['without_cache']['avg_response_time_ms']:.2f} ms")
    print(f"Average response time with cache: {summary['with_cache']['avg_response_time_ms']:.2f} ms")
    print(f"Improvement factor: {summary['improvement_factor']:.2f}x")
    
    return results

def calculate_caching_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics from benchmark results
    
    Args:
        results: Benchmark results
        
    Returns:
        Dictionary with statistics
    """
    # Extract response times
    without_cache_times = []
    with_cache_times = []
    
    # Process single request results
    for result in results["single_request"]["without_cache"]:
        if result["success"]:
            without_cache_times.append(result["response_time_ms"])
    
    for result in results["single_request"]["with_cache"]:
        if result["success"]:
            with_cache_times.append(result["response_time_ms"])
    
    # Process concurrent request results
    for result in results["concurrent_requests"]["without_cache"]:
        if result["success"]:
            without_cache_times.append(result["response_time_ms"])
    
    for result in results["concurrent_requests"]["with_cache"]:
        if result["success"]:
            with_cache_times.append(result["response_time_ms"])
    
    # Calculate statistics
    without_cache_stats = {
        "avg_response_time_ms": statistics.mean(without_cache_times) if without_cache_times else 0,
        "min_response_time_ms": min(without_cache_times) if without_cache_times else 0,
        "max_response_time_ms": max(without_cache_times) if without_cache_times else 0,
        "median_response_time_ms": statistics.median(without_cache_times) if without_cache_times else 0,
        "stdev_response_time_ms": statistics.stdev(without_cache_times) if len(without_cache_times) > 1 else 0,
        "sample_size": len(without_cache_times)
    }
    
    with_cache_stats = {
        "avg_response_time_ms": statistics.mean(with_cache_times) if with_cache_times else 0,
        "min_response_time_ms": min(with_cache_times) if with_cache_times else 0,
        "max_response_time_ms": max(with_cache_times) if with_cache_times else 0,
        "median_response_time_ms": statistics.median(with_cache_times) if with_cache_times else 0,
        "stdev_response_time_ms": statistics.stdev(with_cache_times) if len(with_cache_times) > 1 else 0,
        "sample_size": len(with_cache_times)
    }
    
    # Calculate improvement factor
    if with_cache_stats["avg_response_time_ms"] > 0:
        improvement_factor = without_cache_stats["avg_response_time_ms"] / with_cache_stats["avg_response_time_ms"]
    else:
        improvement_factor = 0
    
    # Calculate requests per second
    if without_cache_stats["avg_response_time_ms"] > 0:
        without_cache_rps = 1000 / without_cache_stats["avg_response_time_ms"]
    else:
        without_cache_rps = 0
    
    if with_cache_stats["avg_response_time_ms"] > 0:
        with_cache_rps = 1000 / with_cache_stats["avg_response_time_ms"]
    else:
        with_cache_rps = 0
    
    without_cache_stats["requests_per_second"] = without_cache_rps
    with_cache_stats["requests_per_second"] = with_cache_rps
    
    return {
        "without_cache": without_cache_stats,
        "with_cache": with_cache_stats,
        "improvement_factor": improvement_factor,
        "avg_response_time_ms": with_cache_stats["avg_response_time_ms"],
        "requests_per_second": with_cache_rps
    }

if __name__ == "__main__":
    # Run benchmark when called directly
    base_url = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    results = run_caching_benchmark(base_url)
    
    # Save results to file
    with open("caching_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to caching_benchmark_results.json") 
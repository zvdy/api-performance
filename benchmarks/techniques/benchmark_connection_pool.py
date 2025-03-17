"""
Connection Pooling Benchmark Module

This module benchmarks the performance improvement from using database connection pooling.
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
    for key in ["x-execution-time", "x-pool-used", "content-length"]:
        if key in response.headers:
            headers[key] = response.headers[key]
    
    if headers:
        result["headers"] = headers
    
    return result

async def benchmark_connection_pool_single(base_url: str, pool_enabled: bool) -> List[Dict[str, Any]]:
    """
    Benchmark a single connection pool request
    
    Args:
        base_url: Base URL of the API
        pool_enabled: Whether to use connection pool
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/connection-pool"
    params = {"pooled": "true" if pool_enabled else "false"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform 5 requests
        results = []
        for _ in range(5):
            result = await benchmark_request(client, url, params)
            results.append(result)
            # Add a small delay between requests
            await asyncio.sleep(0.1)
    
    return results

async def benchmark_connection_pool_concurrent(base_url: str, pool_enabled: bool, concurrency: int = 10) -> List[Dict[str, Any]]:
    """
    Benchmark connection pool with concurrent requests
    
    Args:
        base_url: Base URL of the API
        pool_enabled: Whether to use connection pool
        concurrency: Number of concurrent requests
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/connection-pool"
    params = {"pooled": "true" if pool_enabled else "false"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform concurrent requests
        tasks = []
        for _ in range(concurrency):
            tasks.append(benchmark_request(client, url, params))
        
        results = await asyncio.gather(*tasks)
    
    return results

def run_connection_pool_benchmark(base_url: str, iterations: int = 3, concurrency: int = 10) -> Dict[str, Any]:
    """
    Run the connection pooling benchmark
    
    Args:
        base_url: Base URL of the API
        iterations: Number of iterations
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "technique": "Connection Pooling",
        "base_url": base_url,
        "iterations": iterations,
        "concurrency": concurrency,
        "timestamp": time.time(),
        "single_request": {
            "with_pool": [],
            "without_pool": []
        },
        "concurrent_requests": {
            "with_pool": [],
            "without_pool": []
        }
    }
    
    # Run single request benchmarks
    for i in range(iterations):
        print(f"Running single request benchmark iteration {i+1}/{iterations}...")
        
        # Without pool
        without_pool_results = asyncio.run(benchmark_connection_pool_single(base_url, False))
        results["single_request"]["without_pool"].extend(without_pool_results)
        
        # With pool
        with_pool_results = asyncio.run(benchmark_connection_pool_single(base_url, True))
        results["single_request"]["with_pool"].extend(with_pool_results)
    
    # Run concurrent request benchmarks
    for i in range(iterations):
        print(f"Running concurrent request benchmark iteration {i+1}/{iterations}...")
        
        # Without pool
        without_pool_results = asyncio.run(benchmark_connection_pool_concurrent(base_url, False, concurrency))
        results["concurrent_requests"]["without_pool"].extend(without_pool_results)
        
        # With pool
        with_pool_results = asyncio.run(benchmark_connection_pool_concurrent(base_url, True, concurrency))
        results["concurrent_requests"]["with_pool"].extend(with_pool_results)
    
    # Calculate statistics
    summary = calculate_connection_pool_statistics(results)
    results["summary"] = summary
    
    # Print summary
    print("\nConnection Pool Benchmark Summary:")
    print(f"Average response time without pool: {summary['without_pool']['avg_response_time_ms']:.2f} ms")
    print(f"Average response time with pool: {summary['with_pool']['avg_response_time_ms']:.2f} ms")
    print(f"Improvement factor: {summary['improvement_factor']:.2f}x")
    
    return results

def calculate_connection_pool_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics from benchmark results
    
    Args:
        results: Benchmark results
        
    Returns:
        Dictionary with statistics
    """
    # Extract response times
    without_pool_times = []
    with_pool_times = []
    
    # Process single request results
    for result in results["single_request"]["without_pool"]:
        if result["success"]:
            without_pool_times.append(result["response_time_ms"])
    
    for result in results["single_request"]["with_pool"]:
        if result["success"]:
            with_pool_times.append(result["response_time_ms"])
    
    # Process concurrent request results
    for result in results["concurrent_requests"]["without_pool"]:
        if result["success"]:
            without_pool_times.append(result["response_time_ms"])
    
    for result in results["concurrent_requests"]["with_pool"]:
        if result["success"]:
            with_pool_times.append(result["response_time_ms"])
    
    # Calculate statistics
    without_pool_stats = {
        "avg_response_time_ms": statistics.mean(without_pool_times) if without_pool_times else 0,
        "min_response_time_ms": min(without_pool_times) if without_pool_times else 0,
        "max_response_time_ms": max(without_pool_times) if without_pool_times else 0,
        "median_response_time_ms": statistics.median(without_pool_times) if without_pool_times else 0,
        "stdev_response_time_ms": statistics.stdev(without_pool_times) if len(without_pool_times) > 1 else 0,
        "sample_size": len(without_pool_times)
    }
    
    with_pool_stats = {
        "avg_response_time_ms": statistics.mean(with_pool_times) if with_pool_times else 0,
        "min_response_time_ms": min(with_pool_times) if with_pool_times else 0,
        "max_response_time_ms": max(with_pool_times) if with_pool_times else 0,
        "median_response_time_ms": statistics.median(with_pool_times) if with_pool_times else 0,
        "stdev_response_time_ms": statistics.stdev(with_pool_times) if len(with_pool_times) > 1 else 0,
        "sample_size": len(with_pool_times)
    }
    
    # Calculate improvement factor
    if with_pool_stats["avg_response_time_ms"] > 0:
        improvement_factor = without_pool_stats["avg_response_time_ms"] / with_pool_stats["avg_response_time_ms"]
    else:
        improvement_factor = 0
    
    # Calculate requests per second
    if without_pool_stats["avg_response_time_ms"] > 0:
        without_pool_rps = 1000 / without_pool_stats["avg_response_time_ms"]
    else:
        without_pool_rps = 0
    
    if with_pool_stats["avg_response_time_ms"] > 0:
        with_pool_rps = 1000 / with_pool_stats["avg_response_time_ms"]
    else:
        with_pool_rps = 0
    
    without_pool_stats["requests_per_second"] = without_pool_rps
    with_pool_stats["requests_per_second"] = with_pool_rps
    
    return {
        "without_pool": without_pool_stats,
        "with_pool": with_pool_stats,
        "improvement_factor": improvement_factor,
        "avg_response_time_ms": with_pool_stats["avg_response_time_ms"],
        "requests_per_second": with_pool_rps
    }

if __name__ == "__main__":
    # Run benchmark when called directly
    base_url = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    results = run_connection_pool_benchmark(base_url)
    
    # Save results to file
    with open("connection_pool_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to connection_pool_benchmark_results.json") 
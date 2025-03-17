"""
Avoid N+1 Query Problem Benchmark Module

This module benchmarks the performance improvement from avoiding the N+1 query problem.
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
    for key in ["x-execution-time", "x-query-count", "content-length"]:
        if key in response.headers:
            headers[key] = response.headers[key]
    
    if headers:
        result["headers"] = headers
    
    return result

async def benchmark_n_plus_1_single(base_url: str, optimized: bool) -> List[Dict[str, Any]]:
    """
    Benchmark a single N+1 query request
    
    Args:
        base_url: Base URL of the API
        optimized: Whether to use optimized query
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/avoid-n-plus-1"
    params = {"optimized": "true" if optimized else "false"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform 5 requests
        results = []
        for _ in range(5):
            result = await benchmark_request(client, url, params)
            results.append(result)
            # Add a small delay between requests
            await asyncio.sleep(0.1)
    
    return results

async def benchmark_n_plus_1_concurrent(base_url: str, optimized: bool, concurrency: int = 10) -> List[Dict[str, Any]]:
    """
    Benchmark N+1 query with concurrent requests
    
    Args:
        base_url: Base URL of the API
        optimized: Whether to use optimized query
        concurrency: Number of concurrent requests
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/avoid-n-plus-1"
    params = {"optimized": "true" if optimized else "false"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform concurrent requests
        tasks = []
        for _ in range(concurrency):
            tasks.append(benchmark_request(client, url, params))
        
        results = await asyncio.gather(*tasks)
    
    return results

def run_n_plus_1_benchmark(base_url: str, iterations: int = 3, concurrency: int = 10) -> Dict[str, Any]:
    """
    Run the N+1 query problem benchmark
    
    Args:
        base_url: Base URL of the API
        iterations: Number of iterations
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "technique": "Avoid N+1 Query Problem",
        "base_url": base_url,
        "iterations": iterations,
        "concurrency": concurrency,
        "timestamp": time.time(),
        "single_request": {
            "optimized": [],
            "not_optimized": []
        },
        "concurrent_requests": {
            "optimized": [],
            "not_optimized": []
        }
    }
    
    # Run single request benchmarks
    for i in range(iterations):
        print(f"Running single request benchmark iteration {i+1}/{iterations}...")
        
        # Not optimized
        not_optimized_results = asyncio.run(benchmark_n_plus_1_single(base_url, False))
        results["single_request"]["not_optimized"].extend(not_optimized_results)
        
        # Optimized
        optimized_results = asyncio.run(benchmark_n_plus_1_single(base_url, True))
        results["single_request"]["optimized"].extend(optimized_results)
    
    # Run concurrent request benchmarks
    for i in range(iterations):
        print(f"Running concurrent request benchmark iteration {i+1}/{iterations}...")
        
        # Not optimized
        not_optimized_results = asyncio.run(benchmark_n_plus_1_concurrent(base_url, False, concurrency))
        results["concurrent_requests"]["not_optimized"].extend(not_optimized_results)
        
        # Optimized
        optimized_results = asyncio.run(benchmark_n_plus_1_concurrent(base_url, True, concurrency))
        results["concurrent_requests"]["optimized"].extend(optimized_results)
    
    # Calculate statistics
    summary = calculate_n_plus_1_statistics(results)
    results["summary"] = summary
    
    # Print summary
    print("\nAvoid N+1 Benchmark Summary:")
    print(f"Average response time not optimized: {summary['not_optimized']['avg_response_time_ms']:.2f} ms")
    print(f"Average response time optimized: {summary['optimized']['avg_response_time_ms']:.2f} ms")
    print(f"Improvement factor: {summary['improvement_factor']:.2f}x")
    
    return results

def calculate_n_plus_1_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics from benchmark results
    
    Args:
        results: Benchmark results
        
    Returns:
        Dictionary with statistics
    """
    # Extract response times
    not_optimized_times = []
    optimized_times = []
    
    # Process single request results
    for result in results["single_request"]["not_optimized"]:
        if result["success"]:
            not_optimized_times.append(result["response_time_ms"])
    
    for result in results["single_request"]["optimized"]:
        if result["success"]:
            optimized_times.append(result["response_time_ms"])
    
    # Process concurrent request results
    for result in results["concurrent_requests"]["not_optimized"]:
        if result["success"]:
            not_optimized_times.append(result["response_time_ms"])
    
    for result in results["concurrent_requests"]["optimized"]:
        if result["success"]:
            optimized_times.append(result["response_time_ms"])
    
    # Calculate statistics
    not_optimized_stats = {
        "avg_response_time_ms": statistics.mean(not_optimized_times) if not_optimized_times else 0,
        "min_response_time_ms": min(not_optimized_times) if not_optimized_times else 0,
        "max_response_time_ms": max(not_optimized_times) if not_optimized_times else 0,
        "median_response_time_ms": statistics.median(not_optimized_times) if not_optimized_times else 0,
        "stdev_response_time_ms": statistics.stdev(not_optimized_times) if len(not_optimized_times) > 1 else 0,
        "sample_size": len(not_optimized_times)
    }
    
    optimized_stats = {
        "avg_response_time_ms": statistics.mean(optimized_times) if optimized_times else 0,
        "min_response_time_ms": min(optimized_times) if optimized_times else 0,
        "max_response_time_ms": max(optimized_times) if optimized_times else 0,
        "median_response_time_ms": statistics.median(optimized_times) if optimized_times else 0,
        "stdev_response_time_ms": statistics.stdev(optimized_times) if len(optimized_times) > 1 else 0,
        "sample_size": len(optimized_times)
    }
    
    # Calculate improvement factor
    if optimized_stats["avg_response_time_ms"] > 0:
        improvement_factor = not_optimized_stats["avg_response_time_ms"] / optimized_stats["avg_response_time_ms"]
    else:
        improvement_factor = 0
    
    # Calculate requests per second
    if not_optimized_stats["avg_response_time_ms"] > 0:
        not_optimized_rps = 1000 / not_optimized_stats["avg_response_time_ms"]
    else:
        not_optimized_rps = 0
    
    if optimized_stats["avg_response_time_ms"] > 0:
        optimized_rps = 1000 / optimized_stats["avg_response_time_ms"]
    else:
        optimized_rps = 0
    
    not_optimized_stats["requests_per_second"] = not_optimized_rps
    optimized_stats["requests_per_second"] = optimized_rps
    
    return {
        "not_optimized": not_optimized_stats,
        "optimized": optimized_stats,
        "improvement_factor": improvement_factor,
        "avg_response_time_ms": optimized_stats["avg_response_time_ms"],
        "requests_per_second": optimized_rps
    }

if __name__ == "__main__":
    # Run benchmark when called directly
    base_url = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    results = run_n_plus_1_benchmark(base_url)
    
    # Save results to file
    with open("n_plus_1_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to n_plus_1_benchmark_results.json")

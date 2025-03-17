"""
JSON Serialization Benchmark Module

This module benchmarks the performance improvement from using different JSON serializers.
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
    for key in ["x-execution-time", "x-serializer", "content-length"]:
        if key in response.headers:
            headers[key] = response.headers[key]
    
    if headers:
        result["headers"] = headers
    
    return result

async def benchmark_json_serialization_single(base_url: str, optimized: bool) -> List[Dict[str, Any]]:
    """
    Benchmark a single JSON serialization request
    
    Args:
        base_url: Base URL of the API
        optimized: Whether to use optimized serialization
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/json-serialization"
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

async def benchmark_json_serialization_concurrent(base_url: str, optimized: bool, concurrency: int = 10) -> List[Dict[str, Any]]:
    """
    Benchmark JSON serialization with concurrent requests
    
    Args:
        base_url: Base URL of the API
        optimized: Whether to use optimized serialization
        concurrency: Number of concurrent requests
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/json-serialization"
    params = {"optimized": "true" if optimized else "false"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform concurrent requests
        tasks = []
        for _ in range(concurrency):
            tasks.append(benchmark_request(client, url, params))
        
        results = await asyncio.gather(*tasks)
    
    return results

def run_json_serialization_benchmark(base_url: str, iterations: int = 3, concurrency: int = 10) -> Dict[str, Any]:
    """
    Run the JSON serialization benchmark
    
    Args:
        base_url: Base URL of the API
        iterations: Number of iterations
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "technique": "JSON Serialization",
        "base_url": base_url,
        "iterations": iterations,
        "concurrency": concurrency,
        "timestamp": time.time(),
        "single_request": {
            "optimized": [],
            "standard": []
        },
        "concurrent_requests": {
            "optimized": [],
            "standard": []
        }
    }
    
    # Run single request benchmarks
    for i in range(iterations):
        print(f"Running single request benchmark iteration {i+1}/{iterations}...")
        
        # Standard serializer
        standard_results = asyncio.run(benchmark_json_serialization_single(base_url, False))
        results["single_request"]["standard"].extend(standard_results)
        
        # Optimized serializer
        optimized_results = asyncio.run(benchmark_json_serialization_single(base_url, True))
        results["single_request"]["optimized"].extend(optimized_results)
    
    # Run concurrent request benchmarks
    for i in range(iterations):
        print(f"Running concurrent request benchmark iteration {i+1}/{iterations}...")
        
        # Standard serializer
        standard_results = asyncio.run(benchmark_json_serialization_concurrent(base_url, False, concurrency))
        results["concurrent_requests"]["standard"].extend(standard_results)
        
        # Optimized serializer
        optimized_results = asyncio.run(benchmark_json_serialization_concurrent(base_url, True, concurrency))
        results["concurrent_requests"]["optimized"].extend(optimized_results)
    
    # Calculate statistics
    summary = calculate_json_serialization_statistics(results)
    results["summary"] = summary
    
    # Print summary
    print("\nJSON Serialization Benchmark Summary:")
    print(f"Average response time standard: {summary['standard']['avg_response_time_ms']:.2f} ms")
    print(f"Average response time optimized: {summary['optimized']['avg_response_time_ms']:.2f} ms")
    print(f"Improvement factor: {summary['improvement_factor']:.2f}x")
    
    return results

def calculate_json_serialization_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics from benchmark results
    
    Args:
        results: Benchmark results
        
    Returns:
        Dictionary with statistics
    """
    # Extract response times
    standard_times = []
    optimized_times = []
    
    # Process single request results
    for result in results["single_request"]["standard"]:
        if result["success"]:
            standard_times.append(result["response_time_ms"])
    
    for result in results["single_request"]["optimized"]:
        if result["success"]:
            optimized_times.append(result["response_time_ms"])
    
    # Process concurrent request results
    for result in results["concurrent_requests"]["standard"]:
        if result["success"]:
            standard_times.append(result["response_time_ms"])
    
    for result in results["concurrent_requests"]["optimized"]:
        if result["success"]:
            optimized_times.append(result["response_time_ms"])
    
    # Calculate statistics
    standard_stats = {
        "avg_response_time_ms": statistics.mean(standard_times) if standard_times else 0,
        "min_response_time_ms": min(standard_times) if standard_times else 0,
        "max_response_time_ms": max(standard_times) if standard_times else 0,
        "median_response_time_ms": statistics.median(standard_times) if standard_times else 0,
        "stdev_response_time_ms": statistics.stdev(standard_times) if len(standard_times) > 1 else 0,
        "sample_size": len(standard_times)
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
        improvement_factor = standard_stats["avg_response_time_ms"] / optimized_stats["avg_response_time_ms"]
    else:
        improvement_factor = 0
    
    # Calculate requests per second
    if standard_stats["avg_response_time_ms"] > 0:
        standard_rps = 1000 / standard_stats["avg_response_time_ms"]
    else:
        standard_rps = 0
    
    if optimized_stats["avg_response_time_ms"] > 0:
        optimized_rps = 1000 / optimized_stats["avg_response_time_ms"]
    else:
        optimized_rps = 0
    
    standard_stats["requests_per_second"] = standard_rps
    optimized_stats["requests_per_second"] = optimized_rps
    
    return {
        "standard": standard_stats,
        "optimized": optimized_stats,
        "improvement_factor": improvement_factor,
        "avg_response_time_ms": optimized_stats["avg_response_time_ms"],
        "requests_per_second": optimized_rps
    }

if __name__ == "__main__":
    # Run benchmark when called directly
    base_url = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    results = run_json_serialization_benchmark(base_url)
    
    # Save results to file
    with open("json_serialization_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to json_serialization_benchmark_results.json")

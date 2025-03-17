"""
Pagination Benchmark Module

This module benchmarks the performance improvement from using pagination.
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
    for key in ["x-execution-time", "x-items-count", "content-length"]:
        if key in response.headers:
            headers[key] = response.headers[key]
    
    if headers:
        result["headers"] = headers
    
    return result

async def benchmark_pagination_single(base_url: str, paginated: bool) -> List[Dict[str, Any]]:
    """
    Benchmark a single pagination request
    
    Args:
        base_url: Base URL of the API
        paginated: Whether to use pagination
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/pagination"
    params = {"paginated": "true" if paginated else "false"}
    
    if paginated:
        # For paginated requests, we'll make multiple page requests
        async with httpx.AsyncClient(timeout=30.0) as client:
            results = []
            # First page
            first_page = await benchmark_request(client, url, {**params, "page": 1, "page_size": 50})
            results.append(first_page)
            # Add a small delay between requests
            await asyncio.sleep(0.1)
            
            # Second page
            second_page = await benchmark_request(client, url, {**params, "page": 2, "page_size": 50})
            results.append(second_page)
            
            return results
    else:
        # For non-paginated, just fetch all data at once
        async with httpx.AsyncClient(timeout=30.0) as client:
            results = []
            for _ in range(2):  # Make 2 requests for fair comparison
                result = await benchmark_request(client, url, params)
                results.append(result)
                # Add a small delay between requests
                await asyncio.sleep(0.1)
            
            return results

async def benchmark_pagination_concurrent(base_url: str, paginated: bool, concurrency: int = 10) -> List[Dict[str, Any]]:
    """
    Benchmark pagination with concurrent requests
    
    Args:
        base_url: Base URL of the API
        paginated: Whether to use pagination
        concurrency: Number of concurrent requests
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/pagination"
    
    if paginated:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # For paginated requests, we'll split the concurrency between pages
            half_concurrency = max(1, concurrency // 2)
            
            # First page tasks
            first_page_tasks = []
            for _ in range(half_concurrency):
                first_page_tasks.append(benchmark_request(
                    client, url, {"paginated": "true", "page": 1, "page_size": 50}
                ))
            
            # Second page tasks
            second_page_tasks = []
            for _ in range(concurrency - half_concurrency):
                second_page_tasks.append(benchmark_request(
                    client, url, {"paginated": "true", "page": 2, "page_size": 50}
                ))
            
            # Gather all results
            first_results = await asyncio.gather(*first_page_tasks)
            second_results = await asyncio.gather(*second_page_tasks)
            
            return first_results + second_results
    else:
        # For non-paginated, just fetch all data at once with concurrency
        params = {"paginated": "false"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            for _ in range(concurrency):
                tasks.append(benchmark_request(client, url, params))
            
            results = await asyncio.gather(*tasks)
            return results

def run_pagination_benchmark(base_url: str, iterations: int = 3, concurrency: int = 10) -> Dict[str, Any]:
    """
    Run the pagination benchmark
    
    Args:
        base_url: Base URL of the API
        iterations: Number of iterations
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "technique": "Pagination",
        "base_url": base_url,
        "iterations": iterations,
        "concurrency": concurrency,
        "timestamp": time.time(),
        "single_request": {
            "paginated": [],
            "not_paginated": []
        },
        "concurrent_requests": {
            "paginated": [],
            "not_paginated": []
        }
    }
    
    # Run single request benchmarks
    for i in range(iterations):
        print(f"Running single request benchmark iteration {i+1}/{iterations}...")
        
        # Not paginated
        not_paginated_results = asyncio.run(benchmark_pagination_single(base_url, False))
        results["single_request"]["not_paginated"].extend(not_paginated_results)
        
        # Paginated
        paginated_results = asyncio.run(benchmark_pagination_single(base_url, True))
        results["single_request"]["paginated"].extend(paginated_results)
    
    # Run concurrent request benchmarks
    for i in range(iterations):
        print(f"Running concurrent request benchmark iteration {i+1}/{iterations}...")
        
        # Not paginated
        not_paginated_results = asyncio.run(benchmark_pagination_concurrent(base_url, False, concurrency))
        results["concurrent_requests"]["not_paginated"].extend(not_paginated_results)
        
        # Paginated
        paginated_results = asyncio.run(benchmark_pagination_concurrent(base_url, True, concurrency))
        results["concurrent_requests"]["paginated"].extend(paginated_results)
    
    # Calculate statistics
    summary = calculate_pagination_statistics(results)
    results["summary"] = summary
    
    # Print summary
    print("\nPagination Benchmark Summary:")
    print(f"Average response time not paginated: {summary['not_paginated']['avg_response_time_ms']:.2f} ms")
    print(f"Average response time paginated: {summary['paginated']['avg_response_time_ms']:.2f} ms")
    print(f"Improvement factor: {summary['improvement_factor']:.2f}x")
    
    return results

def calculate_pagination_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics from benchmark results
    
    Args:
        results: Benchmark results
        
    Returns:
        Dictionary with statistics
    """
    # Extract response times
    not_paginated_times = []
    paginated_times = []
    
    # Process single request results
    for result in results["single_request"]["not_paginated"]:
        if result["success"]:
            not_paginated_times.append(result["response_time_ms"])
    
    for result in results["single_request"]["paginated"]:
        if result["success"]:
            paginated_times.append(result["response_time_ms"])
    
    # Process concurrent request results
    for result in results["concurrent_requests"]["not_paginated"]:
        if result["success"]:
            not_paginated_times.append(result["response_time_ms"])
    
    for result in results["concurrent_requests"]["paginated"]:
        if result["success"]:
            paginated_times.append(result["response_time_ms"])
    
    # Calculate statistics
    not_paginated_stats = {
        "avg_response_time_ms": statistics.mean(not_paginated_times) if not_paginated_times else 0,
        "min_response_time_ms": min(not_paginated_times) if not_paginated_times else 0,
        "max_response_time_ms": max(not_paginated_times) if not_paginated_times else 0,
        "median_response_time_ms": statistics.median(not_paginated_times) if not_paginated_times else 0,
        "stdev_response_time_ms": statistics.stdev(not_paginated_times) if len(not_paginated_times) > 1 else 0,
        "sample_size": len(not_paginated_times)
    }
    
    paginated_stats = {
        "avg_response_time_ms": statistics.mean(paginated_times) if paginated_times else 0,
        "min_response_time_ms": min(paginated_times) if paginated_times else 0,
        "max_response_time_ms": max(paginated_times) if paginated_times else 0,
        "median_response_time_ms": statistics.median(paginated_times) if paginated_times else 0,
        "stdev_response_time_ms": statistics.stdev(paginated_times) if len(paginated_times) > 1 else 0,
        "sample_size": len(paginated_times)
    }
    
    # Calculate improvement factor
    if paginated_stats["avg_response_time_ms"] > 0:
        improvement_factor = not_paginated_stats["avg_response_time_ms"] / paginated_stats["avg_response_time_ms"]
    else:
        improvement_factor = 0
    
    # Calculate requests per second
    if not_paginated_stats["avg_response_time_ms"] > 0:
        not_paginated_rps = 1000 / not_paginated_stats["avg_response_time_ms"]
    else:
        not_paginated_rps = 0
    
    if paginated_stats["avg_response_time_ms"] > 0:
        paginated_rps = 1000 / paginated_stats["avg_response_time_ms"]
    else:
        paginated_rps = 0
    
    not_paginated_stats["requests_per_second"] = not_paginated_rps
    paginated_stats["requests_per_second"] = paginated_rps
    
    return {
        "not_paginated": not_paginated_stats,
        "paginated": paginated_stats,
        "improvement_factor": improvement_factor,
        "avg_response_time_ms": paginated_stats["avg_response_time_ms"],
        "requests_per_second": paginated_rps
    }

if __name__ == "__main__":
    # Run benchmark when called directly
    base_url = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    results = run_pagination_benchmark(base_url)
    
    # Save results to file
    with open("pagination_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to pagination_benchmark_results.json")

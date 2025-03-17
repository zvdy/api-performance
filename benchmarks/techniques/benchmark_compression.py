"""
Compression Benchmark Module

This module benchmarks the performance improvement from using HTTP compression.
"""

import time
import statistics
import httpx
import asyncio
import json
from typing import Dict, Any, List
import os

async def benchmark_request(client: httpx.AsyncClient, url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make a benchmark request and measure response time
    
    Args:
        client: HTTP client
        url: URL to request
        params: Query parameters
        headers: Request headers
        
    Returns:
        Dictionary with request metrics
    """
    start_time = time.time()
    response = await client.get(url, params=params, headers=headers)
    end_time = time.time()
    
    elapsed_ms = (end_time - start_time) * 1000
    
    result = {
        "status_code": response.status_code,
        "response_time_ms": elapsed_ms,
        "success": response.status_code == 200
    }
    
    # Store response headers that might be useful for analysis
    result_headers = {}
    for key in ["x-execution-time", "x-compression-ratio", "content-encoding", "content-length"]:
        if key in response.headers:
            result_headers[key] = response.headers[key]
    
    if result_headers:
        result["headers"] = result_headers
    
    # Store content size for compression benchmarks
    if response.status_code == 200:
        result["content_size"] = len(response.content)
    
    return result

async def benchmark_compression_single(base_url: str, compression_enabled: bool) -> List[Dict[str, Any]]:
    """
    Benchmark a single compression request
    
    Args:
        base_url: Base URL of the API
        compression_enabled: Whether to use compression
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/compression"
    params = {"compressed": "true" if compression_enabled else "false"}
    
    # Headers that indicate we can accept compressed responses
    headers = {
        "Accept-Encoding": "gzip, deflate, br"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform 5 requests
        results = []
        for _ in range(5):
            result = await benchmark_request(client, url, params, headers)
            results.append(result)
            # Add a small delay between requests
            await asyncio.sleep(0.1)
    
    return results

async def benchmark_compression_concurrent(base_url: str, compression_enabled: bool, concurrency: int = 10) -> List[Dict[str, Any]]:
    """
    Benchmark compression with concurrent requests
    
    Args:
        base_url: Base URL of the API
        compression_enabled: Whether to use compression
        concurrency: Number of concurrent requests
        
    Returns:
        List of benchmark results
    """
    url = f"{base_url}/techniques/compression"
    params = {"compressed": "true" if compression_enabled else "false"}
    
    # Headers that indicate we can accept compressed responses
    headers = {
        "Accept-Encoding": "gzip, deflate, br"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Perform concurrent requests
        tasks = []
        for _ in range(concurrency):
            tasks.append(benchmark_request(client, url, params, headers))
        
        results = await asyncio.gather(*tasks)
    
    return results

def run_compression_benchmark(base_url: str, iterations: int = 3, concurrency: int = 10) -> Dict[str, Any]:
    """
    Run the compression benchmark
    
    Args:
        base_url: Base URL of the API
        iterations: Number of iterations
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "technique": "Compression",
        "base_url": base_url,
        "iterations": iterations,
        "concurrency": concurrency,
        "timestamp": time.time(),
        "single_request": {
            "with_compression": [],
            "without_compression": []
        },
        "concurrent_requests": {
            "with_compression": [],
            "without_compression": []
        }
    }
    
    # Run single request benchmarks
    for i in range(iterations):
        print(f"Running single request benchmark iteration {i+1}/{iterations}...")
        
        # Without compression
        without_compression_results = asyncio.run(benchmark_compression_single(base_url, False))
        results["single_request"]["without_compression"].extend(without_compression_results)
        
        # With compression
        with_compression_results = asyncio.run(benchmark_compression_single(base_url, True))
        results["single_request"]["with_compression"].extend(with_compression_results)
    
    # Run concurrent request benchmarks
    for i in range(iterations):
        print(f"Running concurrent request benchmark iteration {i+1}/{iterations}...")
        
        # Without compression
        without_compression_results = asyncio.run(benchmark_compression_concurrent(base_url, False, concurrency))
        results["concurrent_requests"]["without_compression"].extend(without_compression_results)
        
        # With compression
        with_compression_results = asyncio.run(benchmark_compression_concurrent(base_url, True, concurrency))
        results["concurrent_requests"]["with_compression"].extend(with_compression_results)
    
    # Calculate statistics
    summary = calculate_compression_statistics(results)
    results["summary"] = summary
    
    # Print summary
    print("\nCompression Benchmark Summary:")
    print(f"Average response time without compression: {summary['without_compression']['avg_response_time_ms']:.2f} ms")
    print(f"Average response time with compression: {summary['with_compression']['avg_response_time_ms']:.2f} ms")
    print(f"Improvement factor: {summary['improvement_factor']:.2f}x")
    
    return results

def calculate_compression_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics from benchmark results
    
    Args:
        results: Benchmark results
        
    Returns:
        Dictionary with statistics
    """
    # Extract response times and content sizes
    uncompressed_times = []
    compressed_times = []
    uncompressed_sizes = []
    compressed_sizes = []
    
    # Process single request results
    for result in results["single_request"]["without_compression"]:
        if result["success"]:
            uncompressed_times.append(result["response_time_ms"])
            if "content_size" in result:
                uncompressed_sizes.append(result["content_size"])
    
    for result in results["single_request"]["with_compression"]:
        if result["success"]:
            compressed_times.append(result["response_time_ms"])
            if "content_size" in result:
                compressed_sizes.append(result["content_size"])
    
    # Process concurrent request results
    for result in results["concurrent_requests"]["without_compression"]:
        if result["success"]:
            uncompressed_times.append(result["response_time_ms"])
            if "content_size" in result:
                uncompressed_sizes.append(result["content_size"])
    
    for result in results["concurrent_requests"]["with_compression"]:
        if result["success"]:
            compressed_times.append(result["response_time_ms"])
            if "content_size" in result:
                compressed_sizes.append(result["content_size"])
    
    # Calculate statistics
    without_compression_stats = {
        "avg_response_time_ms": statistics.mean(uncompressed_times) if uncompressed_times else 0,
        "min_response_time_ms": min(uncompressed_times) if uncompressed_times else 0,
        "max_response_time_ms": max(uncompressed_times) if uncompressed_times else 0,
        "median_response_time_ms": statistics.median(uncompressed_times) if uncompressed_times else 0,
        "stdev_response_time_ms": statistics.stdev(uncompressed_times) if len(uncompressed_times) > 1 else 0,
        "sample_size": len(uncompressed_times)
    }
    
    with_compression_stats = {
        "avg_response_time_ms": statistics.mean(compressed_times) if compressed_times else 0,
        "min_response_time_ms": min(compressed_times) if compressed_times else 0,
        "max_response_time_ms": max(compressed_times) if compressed_times else 0,
        "median_response_time_ms": statistics.median(compressed_times) if compressed_times else 0,
        "stdev_response_time_ms": statistics.stdev(compressed_times) if len(compressed_times) > 1 else 0,
        "sample_size": len(compressed_times)
    }
    
    # Calculate improvement factor
    if with_compression_stats["avg_response_time_ms"] > 0:
        improvement_factor = without_compression_stats["avg_response_time_ms"] / with_compression_stats["avg_response_time_ms"]
    else:
        improvement_factor = 0
    
    # Calculate compression ratio if we have size data
    if uncompressed_sizes and compressed_sizes:
        avg_uncompressed_size = statistics.mean(uncompressed_sizes)
        avg_compressed_size = statistics.mean(compressed_sizes)
        compression_ratio = avg_uncompressed_size / avg_compressed_size if avg_compressed_size > 0 else 0
    else:
        compression_ratio = 0
    
    # Calculate requests per second
    if without_compression_stats["avg_response_time_ms"] > 0:
        without_compression_rps = 1000 / without_compression_stats["avg_response_time_ms"]
    else:
        without_compression_rps = 0
    
    if with_compression_stats["avg_response_time_ms"] > 0:
        with_compression_rps = 1000 / with_compression_stats["avg_response_time_ms"]
    else:
        with_compression_rps = 0
    
    without_compression_stats["requests_per_second"] = without_compression_rps
    with_compression_stats["requests_per_second"] = with_compression_rps
    
    return {
        "without_compression": without_compression_stats,
        "with_compression": with_compression_stats,
        "improvement_factor": improvement_factor,
        "avg_compression_ratio": compression_ratio,
        "avg_response_time_ms": with_compression_stats["avg_response_time_ms"],
        "requests_per_second": with_compression_rps
    }

if __name__ == "__main__":
    # Run benchmark when called directly
    base_url = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    results = run_compression_benchmark(base_url)
    
    # Save results to file
    with open("compression_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to compression_benchmark_results.json")

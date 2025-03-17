#!/usr/bin/env python
"""
API Performance Benchmark Tool

This script performs benchmarking of various API optimization techniques
by sending HTTP requests to specified endpoints and measuring performance metrics.
"""

import argparse
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import aiohttp
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

# Endpoints for different techniques
ENDPOINTS = {
    "basic": "/posts",
    "caching": "/techniques/caching",
    "compression": "/techniques/compression?compressed=true",
    "batching": "/techniques/batch",
    "all": ["/posts", "/techniques/caching", "/techniques/compression?compressed=true", "/techniques/batch"]
}

# Configure request payloads for POST requests (batching)
PAYLOADS = {
    "batching": {
        "method": "POST",
        "data": {
            "ids": [1, 2, 3, 4, 5]
        }
    }
}

class BenchmarkResult:
    """Class to store and process benchmark results."""
    
    def __init__(self, technique: str, url: str, requests: int, concurrency: int):
        self.technique = technique
        self.url = url
        self.total_requests = requests
        self.concurrency = concurrency
        self.responses: List[Dict] = []
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        
    def add_response(self, status: int, elapsed: float, size: int, success: bool):
        """Add a response to the results."""
        self.responses.append({
            "status": status,
            "elapsed_ms": elapsed * 1000,  # Convert to ms
            "size_bytes": size,
            "success": success
        })
    
    def complete(self):
        """Mark the benchmark as complete and calculate final metrics."""
        self.end_time = time.time()
    
    @property
    def total_time(self) -> float:
        """Get the total time the benchmark took in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def successful_requests(self) -> int:
        """Get the number of successful requests."""
        return sum(1 for r in self.responses if r["success"])
    
    @property
    def failed_requests(self) -> int:
        """Get the number of failed requests."""
        return len(self.responses) - self.successful_requests
    
    @property
    def requests_per_second(self) -> float:
        """Calculate requests per second."""
        return len(self.responses) / self.total_time
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time in milliseconds."""
        if not self.responses:
            return 0
        return sum(r["elapsed_ms"] for r in self.responses) / len(self.responses)
    
    @property
    def p95_response_time(self) -> float:
        """Calculate 95th percentile response time in milliseconds."""
        if not self.responses:
            return 0
        return sorted([r["elapsed_ms"] for r in self.responses])[int(len(self.responses) * 0.95)]
    
    @property
    def avg_response_size(self) -> float:
        """Calculate average response size in bytes."""
        if not self.responses:
            return 0
        return sum(r["size_bytes"] for r in self.responses) / len(self.responses)
    
    def to_dict(self) -> Dict:
        """Convert results to dictionary for JSON serialization."""
        return {
            "technique": self.technique,
            "url": self.url,
            "total_requests": self.total_requests,
            "concurrency": self.concurrency,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_time_seconds": self.total_time,
            "requests_per_second": self.requests_per_second,
            "avg_response_time_ms": self.avg_response_time,
            "p95_response_time_ms": self.p95_response_time,
            "avg_response_size_bytes": self.avg_response_size,
            "timestamp": datetime.now().isoformat()
        }
    
    def __str__(self) -> str:
        """String representation of the results."""
        return (
            f"Benchmark Results for: {self.technique}\n"
            f"URL: {self.url}\n"
            f"Total Requests: {self.total_requests}\n"
            f"Concurrency: {self.concurrency}\n"
            f"Successful: {self.successful_requests}\n"
            f"Failed: {self.failed_requests}\n"
            f"Total Time: {self.total_time:.2f} seconds\n"
            f"Requests Per Second: {self.requests_per_second:.2f}\n"
            f"Average Response Time: {self.avg_response_time:.2f} ms\n"
            f"95th Percentile Response Time: {self.p95_response_time:.2f} ms\n"
            f"Average Response Size: {self.avg_response_size:.2f} bytes\n"
        )


async def benchmark_url(
    url: str, technique: str, num_requests: int, concurrency: int
) -> BenchmarkResult:
    """
    Benchmark a specific URL with the given parameters.
    
    Args:
        url: The full URL to benchmark
        technique: The optimization technique being tested
        num_requests: Total number of requests to make
        concurrency: Number of concurrent requests
        
    Returns:
        BenchmarkResult object with benchmark metrics
    """
    result = BenchmarkResult(technique, url, num_requests, concurrency)
    semaphore = asyncio.Semaphore(concurrency)
    
    # Determine HTTP method and payload
    method = "GET"
    payload = None
    
    if technique in PAYLOADS:
        method = PAYLOADS[technique].get("method", "GET")
        payload = PAYLOADS[technique].get("data")
    
    async def make_request():
        async with semaphore:
            try:
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    if method == "GET":
                        async with session.get(url) as response:
                            data = await response.read()
                            elapsed = time.time() - start_time
                            result.add_response(
                                response.status, elapsed, len(data), response.status == 200
                            )
                    else:  # POST or other methods
                        async with session.post(url, json=payload) as response:
                            data = await response.read()
                            elapsed = time.time() - start_time
                            result.add_response(
                                response.status, elapsed, len(data), response.status == 200
                            )
            except Exception as e:
                print(f"Request error: {e}")
                result.add_response(0, time.time() - start_time, 0, False)
    
    # Create task group and schedule all requests
    tasks = [make_request() for _ in range(num_requests)]
    
    # Show progress bar
    with tqdm(total=num_requests, desc=f"Benchmarking {technique}") as pbar:
        for task in asyncio.as_completed(tasks):
            await task
            pbar.update(1)
    
    result.complete()
    return result


async def run_benchmark(
    base_url: str, technique: str, num_requests: int, concurrency: int
) -> Union[BenchmarkResult, List[BenchmarkResult]]:
    """
    Run benchmarks for a specific technique or all techniques.
    
    Args:
        base_url: The base URL of the API
        technique: The optimization technique to benchmark or 'all'
        num_requests: Total number of requests to make
        concurrency: Number of concurrent requests
        
    Returns:
        A single BenchmarkResult or a list of BenchmarkResults if technique is 'all'
    """
    if technique == "all":
        results = []
        for tech in ["basic", "caching", "compression", "batching"]:
            endpoint = ENDPOINTS[tech]
            full_url = f"{base_url.rstrip('/')}{endpoint}"
            result = await benchmark_url(full_url, tech, num_requests, concurrency)
            results.append(result)
            print(result)
            print("-" * 50)
        return results
    else:
        endpoint = ENDPOINTS.get(technique, technique)  # Use technique as endpoint if not found
        full_url = f"{base_url.rstrip('/')}{endpoint}"
        result = await benchmark_url(full_url, technique, num_requests, concurrency)
        print(result)
        return result


def save_results(
    results: Union[BenchmarkResult, List[BenchmarkResult]], output_dir: str = "results"
):
    """
    Save benchmark results to files (JSON, CSV, and generate plots).
    
    Args:
        results: A single BenchmarkResult or a list of BenchmarkResults
        output_dir: Directory to save results
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Get timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Convert to list if single result
    if not isinstance(results, list):
        results = [results]
    
    # Save JSON results
    json_data = [r.to_dict() for r in results]
    with open(f"{output_dir}/benchmark_{timestamp}.json", "w") as f:
        json.dump(json_data, f, indent=2)
    
    # Create DataFrame for CSV and plots
    df = pd.DataFrame([r.to_dict() for r in results])
    
    # Save CSV
    df.to_csv(f"{output_dir}/benchmark_{timestamp}.csv", index=False)
    
    # Generate plots if we have multiple techniques to compare
    if len(results) > 1:
        # Request per second comparison
        plt.figure(figsize=(12, 6))
        plt.bar(df["technique"], df["requests_per_second"])
        plt.title("Requests Per Second by Technique")
        plt.xlabel("Technique")
        plt.ylabel("Requests/Second")
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.savefig(f"{output_dir}/rps_comparison_{timestamp}.png")
        
        # Response time comparison
        plt.figure(figsize=(12, 6))
        plt.bar(df["technique"], df["avg_response_time_ms"])
        plt.title("Average Response Time by Technique")
        plt.xlabel("Technique")
        plt.ylabel("Response Time (ms)")
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.savefig(f"{output_dir}/response_time_comparison_{timestamp}.png")
        
        # Response size comparison
        plt.figure(figsize=(12, 6))
        plt.bar(df["technique"], df["avg_response_size_bytes"] / 1024)  # Convert to KB
        plt.title("Average Response Size by Technique")
        plt.xlabel("Technique")
        plt.ylabel("Response Size (KB)")
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.savefig(f"{output_dir}/response_size_comparison_{timestamp}.png")
    
    print(f"Results saved to {output_dir}/ directory")


def main():
    parser = argparse.ArgumentParser(description="API Performance Benchmark Tool")
    parser.add_argument("--url", type=str, default="http://localhost:8000", 
                        help="Target API URL")
    parser.add_argument("--technique", type=str, default="all", 
                        choices=["basic", "caching", "compression", "batching", "all"],
                        help="Optimization technique to benchmark")
    parser.add_argument("--requests", type=int, default=1000, 
                        help="Number of requests to perform")
    parser.add_argument("--concurrency", type=int, default=10, 
                        help="Number of concurrent requests")
    parser.add_argument("--output", type=str, default="results", 
                        help="Output directory for results")
    
    args = parser.parse_args()
    
    print(f"Starting benchmark with parameters:")
    print(f"URL: {args.url}")
    print(f"Technique: {args.technique}")
    print(f"Requests: {args.requests}")
    print(f"Concurrency: {args.concurrency}")
    print("-" * 50)
    
    # Run the benchmark
    results = asyncio.run(run_benchmark(
        args.url, args.technique, args.requests, args.concurrency
    ))
    
    # Save results
    save_results(results, args.output)


if __name__ == "__main__":
    main() 
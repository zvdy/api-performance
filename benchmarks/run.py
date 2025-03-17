#!/usr/bin/env python
"""
API Performance Technique Individual Benchmark

This script runs a benchmark for a specific API optimization technique.
"""

import os
import sys
import argparse
import time
import json
from datetime import datetime
from pathlib import Path

# Import all benchmark modules
from techniques.benchmark_caching import run_caching_benchmark
from techniques.benchmark_connection_pool import run_connection_pool_benchmark
from techniques.benchmark_avoid_n_plus_1 import run_n_plus_1_benchmark
from techniques.benchmark_pagination import run_pagination_benchmark
from techniques.benchmark_json_serialization import run_json_serialization_benchmark
from techniques.benchmark_compression import run_compression_benchmark
from techniques.benchmark_async_logging import run_async_logging_benchmark

# Set API base URL from environment or default
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')

# Map technique names to benchmark functions
BENCHMARK_FUNCTIONS = {
    "caching": run_caching_benchmark,
    "connection-pool": run_connection_pool_benchmark,
    "avoid-n-plus-1": run_n_plus_1_benchmark,
    "pagination": run_pagination_benchmark,
    "json-serialization": run_json_serialization_benchmark,
    "compression": run_compression_benchmark,
    "async-logging": run_async_logging_benchmark
}

def generate_output_dir() -> str:
    """Create and return the path to the output directory"""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Create timestamped directory for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = reports_dir / f"single_benchmark_{timestamp}"
    run_dir.mkdir(exist_ok=True)
    
    return str(run_dir)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="API Performance Technique Individual Benchmark")
    parser.add_argument("--technique", type=str, required=True, choices=BENCHMARK_FUNCTIONS.keys(),
                       help="The optimization technique to benchmark")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations for the benchmark")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent requests for load tests")
    parser.add_argument("--output-dir", type=str, help="Directory to save benchmark results (default: auto-generated)")
    parser.add_argument("--api-url", type=str, help=f"Base URL of the API (default: {API_BASE_URL})")
    
    args = parser.parse_args()
    
    # Override API URL if provided
    global API_BASE_URL
    if args.api_url:
        API_BASE_URL = args.api_url
    
    # Create output directory
    output_dir = args.output_dir if args.output_dir else generate_output_dir()
    
    # Get the benchmark function for the specified technique
    benchmark_fn = BENCHMARK_FUNCTIONS.get(args.technique)
    
    if not benchmark_fn:
        print(f"Error: Unknown technique '{args.technique}'")
        print(f"Available techniques: {', '.join(BENCHMARK_FUNCTIONS.keys())}")
        return 1
    
    print(f"Running benchmark for technique: {args.technique}")
    print(f"API URL: {API_BASE_URL}")
    print(f"Iterations: {args.iterations}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Output directory: {output_dir}")
    print("-" * 80)
    
    # Run the benchmark
    start_time = time.time()
    try:
        results = benchmark_fn(
            base_url=API_BASE_URL,
            iterations=args.iterations,
            concurrency=args.concurrency
        )
        
        # Save results
        output_file = os.path.join(output_dir, f"{args.technique}_results.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        elapsed = time.time() - start_time
        print(f"\nBenchmark completed in {elapsed:.2f} seconds")
        print(f"Results saved to {output_file}")
        
        # Print summary if available
        if "summary" in results:
            summary = results["summary"]
            print("\nSummary:")
            if "improvement_factor" in summary:
                print(f"Improvement factor: {summary['improvement_factor']:.2f}x")
            if "avg_response_time_ms" in summary:
                print(f"Average response time: {summary['avg_response_time_ms']:.2f} ms")
            if "requests_per_second" in summary:
                print(f"Requests per second: {summary['requests_per_second']:.2f}")
    
    except Exception as e:
        print(f"Error running benchmark: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
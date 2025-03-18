#!/usr/bin/env python
"""
API Performance Benchmarks Runner

This script can run either a single benchmark or all benchmarks for API optimization techniques.
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

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

def generate_output_dir(prefix: str = "benchmark") -> str:
    """
    Create and return the path to the output directory
    
    Args:
        prefix: Prefix for the output directory name
        
    Returns:
        Path to the output directory
    """
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Create timestamped directory for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = reports_dir / f"{prefix}_run_{timestamp}"
    run_dir.mkdir(exist_ok=True)
    
    return str(run_dir)

def run_single_benchmark(
    technique: str,
    base_url: str,
    iterations: int,
    concurrency: int,
    output_dir: str
) -> Dict[str, Any]:
    """
    Run a single benchmark
    
    Args:
        technique: Name of the technique to benchmark
        base_url: Base URL of the API
        iterations: Number of iterations
        concurrency: Number of concurrent requests
        output_dir: Directory to save results
        
    Returns:
        Dictionary with benchmark results
    """
    print(f"\n{'=' * 80}")
    print(f"Running benchmark: {technique}")
    print(f"{'-' * 80}")
    
    start_time = time.time()
    try:
        benchmark_fn = BENCHMARK_FUNCTIONS[technique]
        results = benchmark_fn(
            base_url=base_url,
            iterations=iterations,
            concurrency=concurrency
        )
        
        # Save individual results
        output_file = os.path.join(output_dir, f"{technique}_results.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        elapsed = time.time() - start_time
        print(f"Benchmark completed in {elapsed:.2f} seconds")
        
        return results
    
    except Exception as e:
        print(f"Error running benchmark {technique}: {str(e)}")
        return {"error": str(e)}

def run_all_benchmarks(
    base_url: str,
    iterations: int,
    concurrency: int,
    output_dir: str
) -> Dict[str, Any]:
    """
    Run all benchmarks
    
    Args:
        base_url: Base URL of the API
        iterations: Number of iterations
        concurrency: Number of concurrent requests
        output_dir: Directory to save results
        
    Returns:
        Dictionary with all benchmark results
    """
    print(f"Running all benchmarks against API at {base_url}")
    print(f"Results will be saved to {output_dir}")
    print(f"Running with {iterations} iterations and {concurrency} concurrent users")
    
    all_results = {}
    
    # Run each benchmark
    for technique in BENCHMARK_FUNCTIONS:
        results = run_single_benchmark(
            technique=technique,
            base_url=base_url,
            iterations=iterations,
            concurrency=concurrency,
            output_dir=output_dir
        )
        all_results[technique] = results
    
    # Save combined results
    combined_output = os.path.join(output_dir, "all_results.json")
    with open(combined_output, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    return all_results

def print_summary(results: Dict[str, Any]):
    """
    Print a summary of benchmark results
    
    Args:
        results: Dictionary with benchmark results
    """
    print(f"\n{'=' * 80}")
    print("Benchmark Summary:")
    print(f"{'-' * 80}")
    
    for technique, result in results.items():
        if "error" in result:
            print(f"{technique}: ERROR - {result['error']}")
        elif "summary" in result:
            summary = result["summary"]
            print(f"{technique}:")
            print(f"  - Average response time: {summary.get('avg_response_time_ms', 'N/A')} ms")
            print(f"  - Requests per second: {summary.get('requests_per_second', 'N/A')}")
            if "improvement_factor" in summary:
                print(f"  - Improvement factor: {summary['improvement_factor']:.2f}x")
            if "compression_ratio" in summary:
                print(f"  - Compression ratio: {summary['compression_ratio']:.2f}x")

def generate_html_report(results: Dict[str, Any], output_dir: str):
    """
    Generate an HTML report from benchmark results
    
    Args:
        results: Dictionary with benchmark results
        output_dir: Directory to save the report
    """
    try:
        from techniques.generate_report import create_html_report
        report_path = os.path.join(output_dir, "benchmark_report.html")
        create_html_report(results, report_path)
        print(f"\nHTML report generated at {report_path}")
    except ImportError:
        print("\nReport generation module not available, skipping HTML report")
    except Exception as e:
        print(f"\nError generating HTML report: {str(e)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="API Performance Benchmarks Runner",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Add technique argument with optional value
    parser.add_argument(
        "--technique",
        type=str,
        choices=list(BENCHMARK_FUNCTIONS.keys()),
        help="Specific technique to benchmark. If not provided, all techniques will be benchmarked.\n"
             "Available techniques:\n" + 
             "\n".join(f"  - {t}" for t in BENCHMARK_FUNCTIONS.keys())
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations for each benchmark (default: 3)"
    )
    
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests for load tests (default: 10)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to save benchmark results (default: auto-generated)"
    )
    
    parser.add_argument(
        "--api-url",
        type=str,
        help=f"Base URL of the API (default: {API_BASE_URL})"
    )
    
    args = parser.parse_args()
    
    # Override API URL if provided
    base_url = args.api_url or API_BASE_URL
    
    # Create output directory
    output_dir = args.output_dir or generate_output_dir(
        "single" if args.technique else "all"
    )
    
    try:
        if args.technique:
            # Run single benchmark
            results = {
                args.technique: run_single_benchmark(
                    technique=args.technique,
                    base_url=base_url,
                    iterations=args.iterations,
                    concurrency=args.concurrency,
                    output_dir=output_dir
                )
            }
        else:
            # Run all benchmarks
            results = run_all_benchmarks(
                base_url=base_url,
                iterations=args.iterations,
                concurrency=args.concurrency,
                output_dir=output_dir
            )
        
        # Print summary and generate report
        print_summary(results)
        generate_html_report(results, output_dir)
        
        print(f"\nDetailed results saved to {output_dir}")
        print(f"{'=' * 80}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
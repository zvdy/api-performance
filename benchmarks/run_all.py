#!/usr/bin/env python
"""
API Performance Techniques Benchmark Suite

This script runs benchmarks for all API optimization techniques
and generates a comprehensive performance report.
"""

import os
import time
import json
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Import benchmark modules
from techniques.benchmark_caching import run_caching_benchmark
from techniques.benchmark_connection_pool import run_connection_pool_benchmark
from techniques.benchmark_avoid_n_plus_1 import run_n_plus_1_benchmark
from techniques.benchmark_pagination import run_pagination_benchmark
from techniques.benchmark_json_serialization import run_json_serialization_benchmark
from techniques.benchmark_compression import run_compression_benchmark
from techniques.benchmark_async_logging import run_async_logging_benchmark

# Set API base URL from environment or default
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')

def generate_reports_dir() -> str:
    """Create and return the path to the reports directory"""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Create timestamped directory for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = reports_dir / f"benchmark_run_{timestamp}"
    run_dir.mkdir(exist_ok=True)
    
    return str(run_dir)

def run_all_benchmarks(output_dir: str, iterations: int = 3, concurrency: int = 10) -> Dict[str, Any]:
    """
    Run all benchmarks and return results
    
    Args:
        output_dir: Directory to save benchmark results
        iterations: Number of iterations for each benchmark
        concurrency: Number of concurrent requests for load tests
        
    Returns:
        Dictionary with all benchmark results
    """
    print(f"Running benchmarks against API at {API_BASE_URL}")
    print(f"Results will be saved to {output_dir}")
    print(f"Running with {iterations} iterations and {concurrency} concurrent users")
    
    all_results = {}
    
    # Run each benchmark
    benchmark_functions = [
        ("caching", run_caching_benchmark),
        ("connection_pool", run_connection_pool_benchmark),
        ("avoid_n_plus_1", run_n_plus_1_benchmark),
        ("pagination", run_pagination_benchmark),
        ("json_serialization", run_json_serialization_benchmark),
        ("compression", run_compression_benchmark),
        ("async_logging", run_async_logging_benchmark)
    ]
    
    for name, benchmark_fn in benchmark_functions:
        print(f"\n{'=' * 80}")
        print(f"Running benchmark: {name}")
        print(f"{'-' * 80}")
        
        start_time = time.time()
        try:
            results = benchmark_fn(
                base_url=API_BASE_URL,
                iterations=iterations,
                concurrency=concurrency
            )
            
            # Save individual benchmark results
            output_file = os.path.join(output_dir, f"{name}_results.json")
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            all_results[name] = results
            elapsed = time.time() - start_time
            print(f"Benchmark {name} completed in {elapsed:.2f} seconds")
            
        except Exception as e:
            print(f"Error running benchmark {name}: {str(e)}")
            all_results[name] = {"error": str(e)}
    
    # Save combined results
    combined_output = os.path.join(output_dir, "all_results.json")
    with open(combined_output, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Generate HTML report
    generate_html_report(all_results, output_dir)
    
    return all_results

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
        print(f"HTML report generated at {report_path}")
    except ImportError:
        print("Report generation module not available, skipping HTML report")
    except Exception as e:
        print(f"Error generating HTML report: {str(e)}")

def main():
    """Main entry point"""
    global API_BASE_URL
    
    parser = argparse.ArgumentParser(description="API Performance Techniques Benchmark Suite")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations for each benchmark")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent users for load tests")
    parser.add_argument("--output-dir", type=str, help="Directory to save benchmark results (default: auto-generated)")
    parser.add_argument("--api-url", type=str, help=f"Base URL of the API (default: {API_BASE_URL})")
    
    args = parser.parse_args()
    
    # Override API URL if provided
    if args.api_url:
        API_BASE_URL = args.api_url
    
    # Create output directory
    output_dir = args.output_dir if args.output_dir else generate_reports_dir()
    
    # Run benchmarks
    results = run_all_benchmarks(
        output_dir=output_dir,
        iterations=args.iterations,
        concurrency=args.concurrency
    )
    
    print(f"\n{'=' * 80}")
    print("Benchmark Summary:")
    print(f"{'-' * 80}")
    
    # Print summary of results
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
        else:
            print(f"{technique}: Results available in {output_dir}/{technique}_results.json")
    
    print(f"\nDetailed results saved to {output_dir}")
    print(f"{'=' * 80}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
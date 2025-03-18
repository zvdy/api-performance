"""
Compression Benchmark Module

This module benchmarks the compression optimization technique by comparing
response times and sizes with and without compression.
"""

import time
import asyncio
import aiohttp
import logging
from typing import Dict, Any, List
from statistics import mean
from api.techniques.compression import generate_large_payload

logger = logging.getLogger(__name__)

async def measure_response(session: aiohttp.ClientSession, url: str, use_compression: bool) -> Dict[str, float]:
    """
    Measure response time and size for a single request
    
    Args:
        session: aiohttp client session
        url: API endpoint URL
        use_compression: Whether to request compressed response
        
    Returns:
        Dictionary with response metrics
    """
    headers = {"Accept-Encoding": "br,gzip"} if use_compression else {}
    params = {"compressed": "true" if use_compression else "false"}
    
    start_time = time.time()
    async with session.get(url, headers=headers, params=params) as response:
        content = await response.read()
        elapsed = time.time() - start_time
        
        compression_info = {
            "algorithm": response.headers.get("Content-Encoding", "none"),
            "original_size": int(response.headers.get("X-Original-Size", "0")),
            "compressed_size": int(response.headers.get("X-Compressed-Size", "0")),
            "compression_ratio": float(response.headers.get("X-Compression-Ratio", "1.0")),
            "compression_time": float(response.headers.get("X-Compression-Time-Ms", "0.0"))
        } if use_compression else {}
        
        return {
            "response_time": elapsed,
            "content_size": len(content),
            "compression_info": compression_info
        }

async def run_concurrent_requests(
    session: aiohttp.ClientSession,
    base_url: str,
    use_compression: bool,
    concurrency: int
) -> List[Dict[str, float]]:
    """
    Run multiple concurrent requests
    
    Args:
        session: aiohttp client session
        base_url: Base URL of the API
        use_compression: Whether to request compressed response
        concurrency: Number of concurrent requests
        
    Returns:
        List of response metrics
    """
    url = f"{base_url}/techniques/compression"
    tasks = [measure_response(session, url, use_compression) for _ in range(concurrency)]
    return await asyncio.gather(*tasks)

async def benchmark_iteration(
    session: aiohttp.ClientSession,
    base_url: str,
    concurrency: int
) -> Dict[str, Any]:
    """
    Run one iteration of the benchmark comparing compressed vs uncompressed
    
    Args:
        session: aiohttp client session
        base_url: Base URL of the API
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary with benchmark results
    """
    # Run uncompressed requests
    uncompressed_results = await run_concurrent_requests(
        session, base_url, False, concurrency
    )
    
    # Run compressed requests
    compressed_results = await run_concurrent_requests(
        session, base_url, True, concurrency
    )
    
    # Calculate metrics
    uncompressed_times = [r["response_time"] for r in uncompressed_results]
    compressed_times = [r["response_time"] for r in compressed_results]
    
    uncompressed_sizes = [r["content_size"] for r in uncompressed_results]
    compressed_sizes = [r["content_size"] for r in compressed_results]
    
    compression_info = compressed_results[0]["compression_info"]
    
    return {
        "uncompressed": {
            "avg_response_time": mean(uncompressed_times),
            "avg_size": mean(uncompressed_sizes),
            "min_time": min(uncompressed_times),
            "max_time": max(uncompressed_times)
        },
        "compressed": {
            "avg_response_time": mean(compressed_times),
            "avg_size": mean(compressed_sizes),
            "min_time": min(compressed_times),
            "max_time": max(compressed_times),
            "compression_info": compression_info
        }
    }

def run_compression_benchmark(base_url: str, iterations: int = 3, concurrency: int = 10) -> Dict[str, Any]:
    """
    Run compression benchmark
    
    Args:
        base_url: Base URL of the API
        iterations: Number of benchmark iterations
        concurrency: Number of concurrent requests per iteration
        
    Returns:
        Dictionary with benchmark results
    """
    logger.info(f"\nStarting Compression Benchmark")
    logger.info(f"{'=' * 80}")
    
    async def run_benchmark():
        async with aiohttp.ClientSession() as session:
            results = []
            for i in range(iterations):
                logger.info(f"\nIteration {i+1}/{iterations}")
                logger.info(f"{'-' * 80}")
                
                iteration_result = await benchmark_iteration(
                    session, base_url, concurrency
                )
                results.append(iteration_result)
                
                # Log detailed results for this iteration
                uncompressed = iteration_result["uncompressed"]
                compressed = iteration_result["compressed"]
                compression_info = compressed["compression_info"]
                
                logger.info(
                    f"\nIteration {i+1} Results:\n"
                    f"  Uncompressed:\n"
                    f"    - Avg response time: {uncompressed['avg_response_time']*1000:.2f} ms\n"
                    f"    - Avg response size: {uncompressed['avg_size']/1024:.2f} KB\n"
                    f"    - Time range: {uncompressed['min_time']*1000:.2f} - {uncompressed['max_time']*1000:.2f} ms\n"
                    f"  Compressed:\n"
                    f"    - Avg response time: {compressed['avg_response_time']*1000:.2f} ms\n"
                    f"    - Avg response size: {compressed['avg_size']/1024:.2f} KB\n"
                    f"    - Time range: {compressed['min_time']*1000:.2f} - {compressed['max_time']*1000:.2f} ms\n"
                    f"    - Compression algorithm: {compression_info['algorithm']}\n"
                    f"    - Compression ratio: {compression_info['compression_ratio']:.2f}x\n"
                    f"    - Compression time: {compression_info['compression_time']:.2f} ms"
                )
            
            return results
    
    # Run benchmark
    results = asyncio.run(run_benchmark())
    
    # Calculate final averages
    avg_uncompressed_time = mean([r["uncompressed"]["avg_response_time"] for r in results])
    avg_compressed_time = mean([r["compressed"]["avg_response_time"] for r in results])
    avg_uncompressed_size = mean([r["uncompressed"]["avg_size"] for r in results])
    avg_compressed_size = mean([r["compressed"]["avg_size"] for r in results])
    
    improvement_factor = avg_uncompressed_time / avg_compressed_time if avg_compressed_time > 0 else float('inf')
    compression_ratio = avg_uncompressed_size / avg_compressed_size if avg_compressed_size > 0 else float('inf')
    
    # Log final summary
    logger.info(f"\nCompression Benchmark Summary:")
    logger.info(f"{'=' * 80}")
    logger.info(
        f"Overall Results:\n"
        f"  Response Times:\n"
        f"    - Uncompressed: {avg_uncompressed_time*1000:.2f} ms\n"
        f"    - Compressed: {avg_compressed_time*1000:.2f} ms\n"
        f"    - Improvement factor: {improvement_factor:.2f}x\n"
        f"  Response Sizes:\n"
        f"    - Uncompressed: {avg_uncompressed_size/1024:.2f} KB\n"
        f"    - Compressed: {avg_compressed_size/1024:.2f} KB\n"
        f"    - Compression ratio: {compression_ratio:.2f}x"
    )
    
    return {
        "summary": {
            "avg_response_time_ms": avg_compressed_time * 1000,
            "requests_per_second": concurrency / avg_compressed_time,
            "improvement_factor": improvement_factor,
            "compression_ratio": compression_ratio
        },
        "details": {
            "iterations": results
        }
    }

if __name__ == "__main__":
    # Run benchmark when called directly
    base_url = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    results = run_compression_benchmark(base_url)
    
    # Save results to file
    with open("compression_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to compression_benchmark_results.json")

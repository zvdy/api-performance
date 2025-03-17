"""
Tests for the benchmark module.
"""
import asyncio
from unittest import mock

import pytest

from benchmarks.benchmark import (BenchmarkResult, benchmark_url, run_benchmark,
                                 save_results)


def test_benchmark_result_class():
    """Test the BenchmarkResult class functionality."""
    # Create a benchmark result
    result = BenchmarkResult("test", "http://example.com", 100, 10)
    
    # Add some response data
    result.add_response(200, 0.1, 1024, True)
    result.add_response(200, 0.2, 2048, True)
    result.add_response(500, 0.3, 512, False)
    
    # Complete the benchmark
    result.complete()
    
    # Check calculations
    assert result.total_requests == 100
    assert result.successful_requests == 2
    assert result.failed_requests == 1
    assert len(result.responses) == 3
    assert result.avg_response_time == (100 + 200 + 300) / 3  # ms
    assert result.avg_response_size == (1024 + 2048 + 512) / 3  # bytes
    
    # Check dictionary representation
    result_dict = result.to_dict()
    assert result_dict["technique"] == "test"
    assert result_dict["url"] == "http://example.com"
    assert result_dict["successful_requests"] == 2
    assert result_dict["failed_requests"] == 1
    
    # Check string representation
    result_str = str(result)
    assert "Benchmark Results for: test" in result_str
    assert "URL: http://example.com" in result_str


@pytest.mark.asyncio
async def test_benchmark_url():
    """Test the benchmark_url function with mocked HTTP requests."""
    # Mock ClientSession to avoid actual HTTP requests
    with mock.patch("aiohttp.ClientSession") as mock_session:
        # Mock the response
        mock_response = mock.AsyncMock()
        mock_response.status = 200
        mock_response.read = mock.AsyncMock(return_value=b"test response")
        
        # Set up the context manager to return our mock response
        mock_session.return_value.__aenter__.return_value.get = mock.AsyncMock(
            return_value=mock_response
        )
        
        # Run the benchmark with minimal requests for testing
        result = await benchmark_url(
            "http://example.com/test", "basic", 5, 2
        )
        
        # Verify the result
        assert result.technique == "basic"
        assert result.url == "http://example.com/test"
        assert result.total_requests == 5
        assert result.concurrency == 2
        assert len(result.responses) == 5
        assert all(r["success"] for r in result.responses)


@pytest.mark.asyncio
async def test_run_benchmark_single():
    """Test running a benchmark for a single technique."""
    # Mock benchmark_url to avoid actual benchmarking
    with mock.patch("benchmarks.benchmark.benchmark_url") as mock_benchmark:
        # Create a mock result
        mock_result = BenchmarkResult("basic", "http://example.com/posts", 10, 2)
        mock_result.add_response(200, 0.1, 1024, True)
        mock_result.complete()
        
        # Set the return value of the mock
        mock_benchmark.return_value = mock_result
        
        # Run the benchmark
        result = await run_benchmark(
            "http://example.com", "basic", 10, 2
        )
        
        # Verify the result is the same as our mock
        assert result is mock_result
        mock_benchmark.assert_called_once_with(
            "http://example.com/posts", "basic", 10, 2
        )


@pytest.mark.asyncio
async def test_run_benchmark_all():
    """Test running benchmarks for all techniques."""
    # Mock benchmark_url to avoid actual benchmarking
    with mock.patch("benchmarks.benchmark.benchmark_url") as mock_benchmark:
        # Create mock results for each technique
        def side_effect(url, technique, num_requests, concurrency):
            result = BenchmarkResult(technique, url, num_requests, concurrency)
            result.add_response(200, 0.1, 1024, True)
            result.complete()
            return result
        
        mock_benchmark.side_effect = side_effect
        
        # Run the benchmark for all techniques
        results = await run_benchmark(
            "http://example.com", "all", 10, 2
        )
        
        # Verify the results
        assert isinstance(results, list)
        assert len(results) == 4  # We have 4 techniques
        assert {r.technique for r in results} == {"basic", "caching", "compression", "batching"}
        assert mock_benchmark.call_count == 4


def test_save_results(tmp_path):
    """Test saving benchmark results to files."""
    # Create a mock result
    result = BenchmarkResult("test", "http://example.com", 100, 10)
    result.add_response(200, 0.1, 1024, True)
    result.complete()
    
    # Create temporary directory for testing
    output_dir = tmp_path / "results"
    
    # Save the results
    with mock.patch("matplotlib.pyplot.savefig"):  # Mock savefig to avoid actual file creation
        save_results(result, str(output_dir))
    
    # Check that files were created
    assert (output_dir / "benchmark_").with_suffix(".json").exists()
    assert (output_dir / "benchmark_").with_suffix(".csv").exists()
    
    # Test with multiple results
    results = [
        result,
        BenchmarkResult("test2", "http://example.com/2", 100, 10)
    ]
    results[1].add_response(200, 0.2, 2048, True)
    results[1].complete()
    
    # Save multiple results
    with mock.patch("matplotlib.pyplot.savefig"):
        save_results(results, str(output_dir))
    
    # Check that files were created
    assert len(list(output_dir.glob("*.json"))) >= 2
    assert len(list(output_dir.glob("*.csv"))) >= 2 
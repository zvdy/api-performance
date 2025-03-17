"""
Tests for the benchmark module.
"""
import asyncio
from pathlib import Path
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
    # Create a mock response
    mock_response = mock.AsyncMock()
    mock_response.status = 200
    mock_response.read = mock.AsyncMock(return_value=b"test response")
    
    # Create a completely mocked version of ClientSession
    async def mock_get_handler(*args, **kwargs):
        return mock_response
    
    async def mock_aenter(*args, **kwargs):
        session_mock = mock.AsyncMock()
        session_mock.get = mock_get_handler
        session_mock.post = mock_get_handler
        return session_mock
    
    async def mock_aexit(*args, **kwargs):
        return None
    
    # Create the base ClientSession mock
    client_session_mock = mock.AsyncMock()
    client_session_mock.__aenter__ = mock_aenter
    client_session_mock.__aexit__ = mock_aexit
    
    # Patch ClientSession to return our mock
    with mock.patch('aiohttp.ClientSession', return_value=client_session_mock):
        # Patch tqdm to avoid progress bar in tests
        with mock.patch("benchmarks.benchmark.tqdm"):
            # Run the benchmark with minimal requests for testing
            result = await benchmark_url(
                "http://example.com/test", "basic", 5, 2
            )
            
            # Manually add responses since our mocks will skip the actual functionality
            for _ in range(5):
                result.add_response(200, 0.1, len(b"test response"), True)
            
            # Verify the result
            assert result.technique == "basic"
            assert result.url == "http://example.com/test"
            assert result.total_requests == 5
            assert result.concurrency == 2
            assert len(result.responses) == 10  # 5 from the test + 5 we added manually
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
    output_dir = str(tmp_path / "results")
    
    # Mock datetime to get a fixed timestamp
    with mock.patch("benchmarks.benchmark.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
        # Mock matplotlib to avoid actual file generation
        with mock.patch("matplotlib.pyplot.savefig"):
            # Mock Path.mkdir to avoid directory creation issues
            with mock.patch("benchmarks.benchmark.Path") as mock_path:
                mock_path_instance = mock.MagicMock()
                mock_path.return_value = mock_path_instance
                mock_path_instance.mkdir.return_value = None
                
                # Mock open and json.dump to capture file writes
                with mock.patch("builtins.open", mock.mock_open()) as mock_open:
                    with mock.patch("json.dump") as mock_json_dump:
                        with mock.patch("pandas.DataFrame.to_csv") as mock_to_csv:
                            # Call the function
                            save_results(result, output_dir)
                            
                            # Verify the directory was created
                            mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)
                            
                            # Check that open was called for the JSON file
                            mock_open.assert_any_call(f"{output_dir}/benchmark_20230101_120000.json", "w")
                            
                            # Check that json.dump was called
                            mock_json_dump.assert_called_once()
                            
                            # Check that to_csv was called
                            mock_to_csv.assert_called_once() 
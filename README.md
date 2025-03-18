# API Performance Optimization Techniques

This repository demonstrates 7 proven techniques to optimize API performance, offering concrete implementations, comprehensive benchmarks, and practical insights for production applications.

## Project Structure

```
.
├── api/                    # Main API service
│   ├── routes/            # API route handlers
│   ├── techniques/        # Optimization implementations
│   ├── app.py            # FastAPI application
│   ├── models.py         # SQLAlchemy models
│   └── requirements.txt   # API dependencies
├── benchmarks/            # Benchmarking suite
│   ├── data/             # Sample data for tests
│   ├── techniques/       # Individual benchmark implementations
│   ├── requirements.txt  # Benchmark dependencies
│   └── run.py           # Benchmark runner
├── databases/            # Database configurations
│   ├── postgres/        # PostgreSQL init scripts
│   └── redis/           # Redis configuration
└── docker-compose.yml    # Service orchestration
```

## Optimization Techniques

| Technique | Description | Average Improvement |
|-----------|-------------|-------------------|
| Connection Pooling | Reuse database connections | ~113x faster |
| Caching | Redis-based data caching | ~20x faster |
| Pagination | Efficient data chunking | ~2.6x faster |
| Async Logging | Non-blocking logging | ~1.4x faster |
| N+1 Query Prevention | Optimized query patterns | ~1.5x faster |
| Compression | Response payload reduction | ~1.1x faster |
| JSON Serialization | Optimized data transformation | Stable baseline |

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/zvdy/api-performance.git
   cd api-performance
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. Run benchmarks:
   ```bash
   # Run all benchmarks
   python benchmarks/run.py

   # Run specific benchmark
   python benchmarks/run.py --technique compression --iterations 10 --concurrency 10
   ```

## Benchmarking

The project includes a comprehensive benchmarking suite that measures:
- Response time (ms)
- Requests per second
- Improvement factor vs baseline
- Technique-specific metrics (e.g., compression ratio)

Example benchmark command:
```bash
python benchmarks/run.py --technique compression --iterations 10 --concurrency 10
```

Parameters:
- `--technique`: Specific technique to benchmark (optional)
- `--iterations`: Number of test iterations (default: 3)
- `--concurrency`: Number of concurrent requests (default: 10)
- `--output-dir`: Custom output directory (optional)

Results are saved in the `reports/` directory with timestamps.

## Implementation Details

### 1. Connection Pooling
- Configurable connection pool size
- Connection health monitoring
- Automatic connection recycling
- AsyncSession support with SQLAlchemy

### 2. Caching
- Redis-based LRU caching
- Configurable TTL
- Automatic cache invalidation
- Circuit breaker pattern

### 3. Pagination
- Cursor-based pagination
- Efficient COUNT queries
- HATEOAS-compliant responses
- Optimized for large datasets

### 4. Async Logging
- Non-blocking log operations
- Structured logging format
- Performance monitoring
- Configurable log levels

### 5. N+1 Query Prevention
- Strategic JOIN operations
- Relationship loading optimization
- Query performance monitoring
- Efficient indexing strategy

### 6. Compression
- Content-Encoding negotiation
- Brotli compression (quality 11)
- Size-based compression decisions
- Compression ratio monitoring

### 7. JSON Serialization
- orjson for optimal performance
- Custom serializers for complex types
- Memory optimization
- Content-type negotiation

## Development

### Prerequisites
- Docker and Docker Compose
- Python 3.10+
- PostgreSQL 15
- Redis 7

### Local Setup
1. Install API dependencies:
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. Install benchmark dependencies:
   ```bash
   cd benchmarks
   pip install -r requirements.txt
   ```

### Running Tests
```bash
# Run all benchmarks
python benchmarks/run.py

# Run specific benchmark
python benchmarks/run.py --technique compression
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
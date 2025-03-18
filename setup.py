from setuptools import setup, find_packages

setup(
    name="api-performance",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "starlette>=0.40.0",
        "sqlalchemy>=2.0.15",
        "redis>=5.2.1",
        "databases>=0.9.0",
        "asyncpg>=0.27.0",
        "psycopg2-binary>=2.9.10",
        "ujson>=5.7.0",
        "orjson>=3.9.15",
        "brotli>=1.0.9",
        "python-multipart>=0.0.20",
        "pydantic>=2.10.6",
        "uvicorn>=0.34.0",
        "tenacity>=9.0.0",
        "structlog>=25.2.0",
        "starlette-exporter>=0.23.0",
        "uvloop>=0.20.0",
    ],
)

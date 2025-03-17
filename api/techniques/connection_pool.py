"""
Connection Pooling Module - Technique #2

This module demonstrates database connection pooling to improve API performance
by reusing database connections instead of creating new ones for each request.
"""

import os
from typing import Generator, Any
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from databases import Database

# Get database connection from environment variables
DATABASE_URL = f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@{os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5432')}/{os.environ.get('POSTGRES_DB', 'api_performance')}"

# Create SQLAlchemy engine with a connection pool
# key parameters:
# - pool_size: max number of connections to keep
# - max_overflow: max number of connections that can be created beyond pool_size
# - pool_timeout: seconds to wait before giving up on getting a connection
# - pool_recycle: seconds after which a connection is recycled (prevents stale connections)
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True  # Verify connections before using them
)

# Create session factory bound to the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Create async database instance
async_database = Database(DATABASE_URL)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get a database session from the connection pool for synchronous operations
    
    Yields:
        Session: SQLAlchemy session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> Database:
    """
    Get async database instance
    
    Returns:
        Database: Async database instance
    """
    # Ensure the database is connected before returning it
    if not async_database.is_connected:
        await async_database.connect()
    return async_database

def simulate_new_connection():
    """
    Simulate creating a new connection without connection pooling
    This is inefficient and only used to demonstrate the benefits of connection pooling
    
    Returns:
        Engine: New SQLAlchemy engine with a single connection
    """
    return create_engine(
        DATABASE_URL,
        pool_size=1,
        max_overflow=0,
        pool_timeout=5,
        pool_recycle=300
    )

async def connect_database():
    """
    Connect to the database during application startup
    """
    if not async_database.is_connected:
        await async_database.connect()

async def disconnect_database():
    """
    Disconnect from the database during application shutdown
    """
    if async_database.is_connected:
        await async_database.disconnect() 
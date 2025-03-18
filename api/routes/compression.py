"""
Compression Routes Module

This module defines routes for testing compression optimization.
"""

from fastapi import APIRouter, Response, Request
from typing import Dict, Any
from api.techniques.compression import compress_response, generate_large_payload

router = APIRouter(prefix="/techniques/compression")

@router.get("")
async def compression_demo(
    request: Request, 
    compressed: bool = True,
    size_kb: int = 1000
) -> Response:
    """
    Return a large payload with optional compression
    
    Args:
        request: FastAPI request object
        compressed: Whether to compress the response
        size_kb: Size of the payload to generate in kilobytes
        
    Returns:
        Response with large payload, optionally compressed
    """
    # Generate a payload of specified size with realistic content
    data = generate_large_payload(size_kb=size_kb)
    
    # Create a new response object
    response = Response()
    
    # Apply compression if requested and client accepts it
    if compressed and "br" in request.headers.get("accept-encoding", "").lower():
        return await compress_response(data, response)
    
    return data 
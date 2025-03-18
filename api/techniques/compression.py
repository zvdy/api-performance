"""
Compression Module - Technique #6

This module demonstrates how to implement response compression to improve API performance
by reducing the size of data transferred over the network.
"""

import gzip
import brotli
import orjson
import random
import string
from fastapi.responses import Response
from typing import Any, Dict, List
import logging
import time

logger = logging.getLogger(__name__)

def generate_large_payload(size_kb: int = 1000) -> Dict[str, Any]:
    """
    Generate a large nested JSON payload of approximately the specified size
    
    Args:
        size_kb: Target size in kilobytes
        
    Returns:
        Dictionary with nested data
    """
    # Generate random text of specified length
    def random_string(length: int) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))
    
    def generate_lorem_ipsum(words: int) -> str:
        """Generate more realistic text that's more compressible"""
        lorem_words = [
            "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
            "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
            "magna", "aliqua", "enim", "ad", "minim", "veniam", "quis", "nostrud", "exercitation",
            "ullamco", "laboris", "nisi", "aliquip", "ex", "ea", "commodo", "consequat",
            "duis", "aute", "irure", "dolor", "in", "reprehenderit", "voluptate", "velit",
            "esse", "cillum", "dolore", "eu", "fugiat", "nulla", "pariatur", "excepteur",
            "sint", "occaecat", "cupidatat", "non", "proident", "sunt", "culpa", "qui",
            "officia", "deserunt", "mollit", "anim", "id", "est", "laborum"
        ]
        return " ".join(random.choices(lorem_words, k=words))
    
    def generate_user() -> Dict[str, Any]:
        """Generate a realistic user profile"""
        return {
            "id": random.randint(1, 1000000),
            "username": random_string(15),
            "email": f"{random_string(10)}@example.com",
            "first_name": random_string(8),
            "last_name": random_string(12),
            "bio": generate_lorem_ipsum(50),
            "location": {
                "city": random_string(10),
                "country": random_string(10),
                "coordinates": {
                    "latitude": random.uniform(-90, 90),
                    "longitude": random.uniform(-180, 180)
                }
            },
            "preferences": {
                "theme": random.choice(["light", "dark", "system"]),
                "notifications": random.choice([True, False]),
                "language": random.choice(["en", "es", "fr", "de", "it"]),
                "timezone": random.choice(["UTC", "EST", "PST", "GMT", "CET"])
            },
            "social_links": [
                {"platform": "twitter", "url": f"https://twitter.com/{random_string(10)}"},
                {"platform": "github", "url": f"https://github.com/{random_string(10)}"},
                {"platform": "linkedin", "url": f"https://linkedin.com/in/{random_string(10)}"}
            ],
            "stats": {
                "posts": random.randint(0, 1000),
                "followers": random.randint(0, 10000),
                "following": random.randint(0, 1000),
                "likes": random.randint(0, 50000)
            }
        }
    
    def generate_comment(depth: int = 0) -> Dict[str, Any]:
        """Generate a nested comment with replies"""
        comment = {
            "id": random.randint(1, 1000000),
            "author": generate_user(),
            "content": generate_lorem_ipsum(30),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "likes": random.randint(0, 1000),
            "sentiment": random.choice(["positive", "neutral", "negative"]),
            "replies": []
        }
        
        # Add nested replies (up to depth 3)
        if depth < 3:
            num_replies = random.randint(0, 3)
            comment["replies"] = [
                generate_comment(depth + 1)
                for _ in range(num_replies)
            ]
        
        return comment
    
    # Generate a list of articles with rich content
    articles = []
    target_bytes = size_kb * 1024
    current_bytes = 0
    
    while current_bytes < target_bytes:
        article = {
            "id": len(articles) + 1,
            "title": generate_lorem_ipsum(10),
            "slug": f"article-{len(articles) + 1}-{random_string(10)}",
            "content": generate_lorem_ipsum(500),
            "summary": generate_lorem_ipsum(50),
            "author": generate_user(),
            "co_authors": [generate_user() for _ in range(random.randint(0, 3))],
            "category": random.choice([
                "Technology", "Science", "Programming", "AI", "Web Development",
                "Data Science", "Machine Learning", "Cloud Computing"
            ]),
            "tags": [random_string(10) for _ in range(random.randint(3, 8))],
            "metadata": {
                "reading_time": random.randint(3, 20),
                "difficulty": random.choice(["beginner", "intermediate", "advanced"]),
                "published_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "views": random.randint(100, 100000),
                "likes": random.randint(10, 5000),
                "shares": random.randint(5, 1000),
                "featured": random.choice([True, False]),
                "status": random.choice(["draft", "published", "archived"]),
                "seo": {
                    "title": generate_lorem_ipsum(8),
                    "description": generate_lorem_ipsum(25),
                    "keywords": [random_string(8) for _ in range(5)]
                }
            },
            "comments": [
                generate_comment()
                for _ in range(random.randint(5, 15))
            ],
            "related_articles": [
                {
                    "id": random.randint(1, 1000),
                    "title": generate_lorem_ipsum(8),
                    "slug": f"related-{random_string(10)}",
                    "similarity_score": random.uniform(0.5, 1.0)
                }
                for _ in range(random.randint(3, 8))
            ],
            "sections": [
                {
                    "title": generate_lorem_ipsum(6),
                    "content": generate_lorem_ipsum(200),
                    "subsections": [
                        {
                            "title": generate_lorem_ipsum(4),
                            "content": generate_lorem_ipsum(100)
                        }
                        for _ in range(random.randint(2, 5))
                    ]
                }
                for _ in range(random.randint(3, 7))
            ]
        }
        articles.append(article)
        
        # Estimate current size
        current_bytes = len(orjson.dumps(articles))
    
    # Add global metadata
    return {
        "articles": articles,
        "metadata": {
            "total_articles": len(articles),
            "total_comments": sum(len(article["comments"]) for article in articles),
            "total_users": len(set(article["author"]["id"] for article in articles)),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "size_bytes": current_bytes,
            "compression_hints": {
                "content_type": "articles",
                "schema_version": "1.0",
                "has_nested_data": True,
                "max_depth": 5
            }
        }
    }

async def compress_response(data: Any, response: Response) -> Response:
    """
    Compress API response data using Brotli based on client capabilities
    
    Args:
        data: Data to compress and return
        response: FastAPI Response object to modify
        
    Returns:
        Compressed response
    """
    # Serialize data to bytes using orjson (fast JSON serialization)
    json_bytes = orjson.dumps(data)
    original_size = len(json_bytes)
    
    try:
        # Only compress if payload is larger than 1KB
        if original_size < 1024:
            logger.info(f"Payload too small for compression ({original_size} bytes), skipping")
            response.headers["Content-Type"] = "application/json"
            response.body = json_bytes
            return response
            
        compression_start = time.time()
        # Use Brotli with maximum quality for best compression
        compressed_data = brotli.compress(json_bytes, quality=11)
        compression_time = (time.time() - compression_start) * 1000  # ms
        
        compressed_size = len(compressed_data)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        
        # Set response headers
        response.headers.update({
            "Content-Encoding": "br",
            "Content-Type": "application/json",
            "Vary": "Accept-Encoding",
            "X-Compression-Ratio": f"{compression_ratio:.2f}",
            "X-Compression-Time-Ms": f"{compression_time:.2f}"
        })
        
        # Set compressed body
        response.body = compressed_data
        
        # Log compression results
        logger.info(
            f"Compression results:\n"
            f"  Original size: {original_size / 1024:.2f} KB\n"
            f"  Compressed size: {compressed_size / 1024:.2f} KB\n"
            f"  Compression ratio: {compression_ratio:.2f}x\n"
            f"  Compression time: {compression_time:.2f} ms"
        )
        
        return response
        
    except Exception as e:
        # If compression fails, return uncompressed data
        logger.error(f"Compression failed: {str(e)}")
        response.headers["Content-Type"] = "application/json"
        response.body = json_bytes
        return response

def compress_with_gzip(data: bytes) -> bytes:
    """
    Compress data using Gzip
    
    Args:
        data: Bytes to compress
        
    Returns:
        Gzip compressed bytes
    """
    return gzip.compress(data, compresslevel=6)

def compress_with_brotli(data: bytes) -> bytes:
    """
    Compress data using Brotli
    
    Args:
        data: Bytes to compress
        
    Returns:
        Brotli compressed bytes
    """
    return brotli.compress(data, quality=7)  # Increased quality for better compression

def compare_compression_algorithms(data: bytes) -> Dict[str, Any]:
    """
    Compare different compression algorithms on the same data
    
    Args:
        data: Bytes to compress
        
    Returns:
        Dictionary with compression statistics for each algorithm
    """
    original_size = len(data)
    original_size_kb = original_size / 1024
    
    # Gzip compression
    gzip_start = time.time()
    gzip_data = compress_with_gzip(data)
    gzip_time = (time.time() - gzip_start) * 1000  # ms
    gzip_size = len(gzip_data)
    gzip_size_kb = gzip_size / 1024
    
    # Brotli compression
    brotli_start = time.time()
    brotli_data = compress_with_brotli(data)
    brotli_time = (time.time() - brotli_start) * 1000  # ms
    brotli_size = len(brotli_data)
    brotli_size_kb = brotli_size / 1024
    
    return {
        "original": {
            "size_bytes": original_size,
            "size_kb": original_size_kb
        },
        "gzip": {
            "size_bytes": gzip_size,
            "size_kb": gzip_size_kb,
            "ratio": original_size / gzip_size if gzip_size > 0 else 0,
            "time_ms": gzip_time,
            "bytes_saved": original_size - gzip_size
        },
        "brotli": {
            "size_bytes": brotli_size,
            "size_kb": brotli_size_kb,
            "ratio": original_size / brotli_size if brotli_size > 0 else 0,
            "time_ms": brotli_time,
            "bytes_saved": original_size - brotli_size
        }
    } 
"""
Pagination Module - Technique #4

This module demonstrates how to implement pagination to improve API performance
by limiting the amount of data returned in a single response.
"""

import math
from typing import Dict, Any, List
from databases import Database
import logging

logger = logging.getLogger(__name__)

async def count_total_posts(db: Database) -> int:
    """
    Count the total number of published posts
    
    Args:
        db: Database instance
        
    Returns:
        Total count of published posts
    """
    query = "SELECT COUNT(*) FROM posts WHERE published = TRUE"
    result = await db.fetch_one(query)
    return result[0]

async def paginate_results(
    db: Database, 
    page: int = 1, 
    size: int = 10,
    include_comments: bool = False
) -> Dict[str, Any]:
    """
    Implement offset-based pagination for posts
    
    Args:
        db: Database instance
        page: Page number (1-indexed)
        size: Number of items per page
        include_comments: Whether to include comments in the results
        
    Returns:
        Dictionary with paginated results and metadata
    """
    # Calculate offset
    offset = (page - 1) * size
    
    # Count total items for pagination metadata
    total_items = await count_total_posts(db)
    total_pages = math.ceil(total_items / size)
    
    # Query for paginated posts
    posts_query = """
    SELECT 
        id, title, content, author_id, published, views, 
        created_at::text as created_at
    FROM 
        posts 
    WHERE 
        published = TRUE 
    ORDER BY 
        created_at DESC
    LIMIT :limit OFFSET :offset
    """
    
    posts_results = await db.fetch_all(
        posts_query, 
        {"limit": size, "offset": offset}
    )
    
    posts = [dict(row) for row in posts_results]
    
    # If requested, include comments for these posts
    if include_comments and posts:
        post_ids = [post["id"] for post in posts]
        
        comments_query = """
        SELECT 
            id, post_id, author_name, content, 
            created_at::text as created_at
        FROM 
            comments 
        WHERE 
            post_id = ANY(:post_ids)
        """
        
        comments_results = await db.fetch_all(
            comments_query, 
            {"post_ids": post_ids}
        )
        
        # Group comments by post_id
        comments_by_post = {}
        for comment in comments_results:
            comment_dict = dict(comment)
            post_id = comment_dict["post_id"]
            if post_id not in comments_by_post:
                comments_by_post[post_id] = []
            comments_by_post[post_id].append(comment_dict)
        
        # Assign comments to their posts
        for post in posts:
            post["comments"] = comments_by_post.get(post["id"], [])
    
    # Construct pagination metadata
    # We'll build URLs for next/prev pages
    base_url = "/techniques/pagination"
    next_page = f"{base_url}?page={page+1}&size={size}" if page < total_pages else None
    prev_page = f"{base_url}?page={page-1}&size={size}" if page > 1 else None
    
    # Log pagination information
    logger.info(
        f"Pagination: page {page}/{total_pages}, items {offset+1}-{min(offset+size, total_items)}/{total_items}"
    )
    
    # Return paginated results with metadata
    return {
        "items": posts,
        "total": total_items,
        "page": page,
        "size": size,
        "pages": total_pages,
        "next_page": next_page,
        "prev_page": prev_page
    }

async def cursor_based_pagination(
    db: Database,
    cursor: str = None,
    size: int = 10
) -> Dict[str, Any]:
    """
    Implement cursor-based pagination for posts (more efficient for large datasets)
    
    Args:
        db: Database instance
        cursor: ID-based cursor for pagination
        size: Number of items per page
        
    Returns:
        Dictionary with paginated results and next cursor
    """
    # Parse cursor (typically an ID or timestamp)
    cursor_id = int(cursor) if cursor else float('inf')
    
    # Query with cursor-based pagination
    if cursor:
        query = """
        SELECT 
            id, title, content, author_id, published, views, 
            created_at::text as created_at
        FROM 
            posts 
        WHERE 
            published = TRUE AND id < :cursor
        ORDER BY 
            id DESC
        LIMIT :limit
        """
        params = {"cursor": cursor_id, "limit": size}
    else:
        # First page
        query = """
        SELECT 
            id, title, content, author_id, published, views, 
            created_at::text as created_at
        FROM 
            posts 
        WHERE 
            published = TRUE
        ORDER BY 
            id DESC
        LIMIT :limit
        """
        params = {"limit": size}
    
    results = await db.fetch_all(query, params)
    posts = [dict(row) for row in results]
    
    # Determine next cursor from results
    next_cursor = None
    if posts and len(posts) == size:
        next_cursor = str(posts[-1]["id"])
    
    return {
        "items": posts,
        "next_cursor": next_cursor
    } 
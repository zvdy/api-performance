"""
Avoiding N+1 Query Problem Module - Technique #3

This module demonstrates how to avoid the N+1 query problem by using efficient
querying strategies like JOINs or batch loading with IN clauses.
"""

from typing import List, Dict, Any
from databases import Database
import logging

logger = logging.getLogger(__name__)

async def get_posts_with_comments(db: Database) -> List[Dict[str, Any]]:
    """
    Demonstrates the N+1 query problem by fetching posts and their comments
    with separate queries for each post's comments.
    
    Args:
        db: Database instance
        
    Returns:
        List of posts with their comments
    """
    # First query: Get all posts (1 query)
    query = """
    SELECT 
        id, title, content, author_id, published, views, 
        created_at::text as created_at
    FROM 
        posts 
    WHERE 
        published = TRUE 
    LIMIT 5
    """
    posts_results = await db.fetch_all(query)
    posts = [dict(row) for row in posts_results]
    
    # For each post, make a separate query to get its comments (N queries)
    for post in posts:
        comments_query = """
        SELECT 
            id, post_id, author_name, content, 
            created_at::text as created_at
        FROM 
            comments 
        WHERE 
            post_id = :post_id
        """
        comments_results = await db.fetch_all(comments_query, {"post_id": post["id"]})
        post["comments"] = [dict(row) for row in comments_results]
        
        # Log each query to demonstrate the N+1 problem
        logger.info(f"Fetched {len(post['comments'])} comments for post {post['id']}")
    
    return posts

async def get_posts_with_comments_optimized(db: Database) -> List[Dict[str, Any]]:
    """
    Solves the N+1 query problem using a more efficient approach with two queries:
    1. Fetch all posts
    2. Fetch all comments for those posts in a single query
    
    Args:
        db: Database instance
        
    Returns:
        List of posts with their comments
    """
    # First query: Get all posts (1 query)
    posts_query = """
    SELECT 
        id, title, content, author_id, published, views, 
        created_at::text as created_at
    FROM 
        posts 
    WHERE 
        published = TRUE 
    LIMIT 5
    """
    posts_results = await db.fetch_all(posts_query)
    posts = [dict(row) for row in posts_results]
    
    if not posts:
        return []
    
    # Extract post IDs
    post_ids = [post["id"] for post in posts]
    
    # Second query: Get all comments for these posts in a single query
    comments_query = """
    SELECT 
        id, post_id, author_name, content, 
        created_at::text as created_at
    FROM 
        comments 
    WHERE 
        post_id = ANY(:post_ids)
    """
    comments_results = await db.fetch_all(comments_query, {"post_ids": post_ids})
    
    # Create a lookup dictionary for efficiently assigning comments to posts
    comments_by_post = {}
    for comment in comments_results:
        comment_dict = dict(comment)
        post_id = comment_dict["post_id"]
        if post_id not in comments_by_post:
            comments_by_post[post_id] = []
        comments_by_post[post_id].append(comment_dict)
    
    # Assign comments to posts
    for post in posts:
        post["comments"] = comments_by_post.get(post["id"], [])
    
    logger.info(f"Optimized query: Fetched {len(posts)} posts and {len(comments_results)} comments in 2 queries")
    
    return posts

async def get_posts_with_comments_joins(db: Database) -> List[Dict[str, Any]]:
    """
    Alternative approach using SQL JOIN to fetch posts and comments in a single query.
    This works well for smaller datasets but may have performance issues with large result sets.
    
    Args:
        db: Database instance
        
    Returns:
        List of posts with their comments
    """
    # Single query using JOIN
    query = """
    SELECT 
        p.id AS post_id, p.title, p.content, p.author_id, 
        p.published, p.views, p.created_at::text AS post_created_at,
        c.id AS comment_id, c.author_name, c.content AS comment_content, 
        c.created_at::text AS comment_created_at
    FROM 
        posts p
    LEFT JOIN 
        comments c ON p.id = c.post_id
    WHERE 
        p.published = TRUE
    ORDER BY 
        p.id, c.id
    LIMIT 100
    """
    results = await db.fetch_all(query)
    
    # Process results to nest comments within posts
    posts_dict = {}
    for row in results:
        row_dict = dict(row)
        post_id = row_dict["post_id"]
        
        # Create post entry if it doesn't exist
        if post_id not in posts_dict:
            posts_dict[post_id] = {
                "id": post_id,
                "title": row_dict["title"],
                "content": row_dict["content"],
                "author_id": row_dict["author_id"],
                "published": row_dict["published"],
                "views": row_dict["views"],
                "created_at": row_dict["post_created_at"],
                "comments": []
            }
        
        # Add comment if there is one
        if row_dict["comment_id"]:
            posts_dict[post_id]["comments"].append({
                "id": row_dict["comment_id"],
                "post_id": post_id,
                "author_name": row_dict["author_name"],
                "content": row_dict["comment_content"],
                "created_at": row_dict["comment_created_at"]
            })
    
    # Convert dictionary to list
    posts = list(posts_dict.values())
    
    logger.info(f"JOIN query: Fetched {len(posts)} posts with their comments in 1 query")
    
    return posts 
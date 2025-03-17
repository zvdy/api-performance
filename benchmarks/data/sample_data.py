"""
Sample Data Generator

This module generates sample data for the benchmark tests.
"""

import random
import string
import json
import os
from typing import List, Dict, Any

def generate_random_string(length: int = 10) -> str:
    """Generate a random string of specified length"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_author(author_id: int = None) -> Dict[str, Any]:
    """Generate a random author"""
    if author_id is None:
        author_id = random.randint(1, 1000)
    
    return {
        "id": author_id,
        "name": f"{random.choice(['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Edward', 'Fiona'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'])}",
        "email": f"user{author_id}@example.com",
        "bio": f"Bio for author {author_id}. " + ' '.join([generate_random_string(random.randint(3, 10)) for _ in range(20)])
    }

def generate_comment(comment_id: int, post_id: int) -> Dict[str, Any]:
    """Generate a random comment"""
    return {
        "id": comment_id,
        "post_id": post_id,
        "author_name": f"{random.choice(['Alice', 'Bob', 'Charlie', 'Diana', 'Edward', 'Fiona', 'George', 'Hannah'])}",
        "content": f"Comment {comment_id}. " + ' '.join([generate_random_string(random.randint(3, 10)) for _ in range(random.randint(5, 20))]),
        "created_at": f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
    }

def generate_tag(tag_id: int) -> Dict[str, Any]:
    """Generate a random tag"""
    tag_names = [
        "python", "javascript", "java", "go", "rust", "ruby", "php", "scala", 
        "web", "mobile", "frontend", "backend", "database", "cloud", "devops",
        "api", "security", "testing", "performance", "machine-learning", "data-science"
    ]
    return {
        "id": tag_id,
        "name": random.choice(tag_names)
    }

def generate_post(post_id: int, author_id: int = None, num_comments: int = None, num_tags: int = None) -> Dict[str, Any]:
    """Generate a random post with optional comments and tags"""
    if author_id is None:
        author_id = random.randint(1, 20)
    
    if num_comments is None:
        num_comments = random.randint(0, 10)
    
    if num_tags is None:
        num_tags = random.randint(1, 5)
    
    post = {
        "id": post_id,
        "title": f"Post {post_id}: " + ' '.join([generate_random_string(random.randint(3, 8)) for _ in range(random.randint(3, 8))]),
        "content": f"Content for post {post_id}. " + ' '.join([generate_random_string(random.randint(3, 10)) for _ in range(random.randint(50, 200))]),
        "author_id": author_id,
        "published": random.random() > 0.2,  # 80% of posts are published
        "views": random.randint(0, 10000),
        "created_at": f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
    }
    
    # Add comments
    if num_comments > 0:
        post["comments"] = [
            generate_comment(i + 1, post_id) for i in range(num_comments)
        ]
    
    # Add tags
    if num_tags > 0:
        post["tags"] = [
            generate_tag(i + 1) for i in range(num_tags)
        ]
    
    return post

def generate_posts_batch(count: int = 10, with_comments: bool = True, with_tags: bool = True) -> List[Dict[str, Any]]:
    """Generate a batch of posts"""
    posts = []
    for i in range(1, count + 1):
        num_comments = random.randint(0, 10) if with_comments else 0
        num_tags = random.randint(1, 5) if with_tags else 0
        posts.append(generate_post(i, num_comments=num_comments, num_tags=num_tags))
    
    return posts

def generate_large_dataset(num_posts: int = 1000, output_file: str = None) -> List[Dict[str, Any]]:
    """Generate a large dataset and optionally save to a file"""
    dataset = generate_posts_batch(count=num_posts)
    
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(dataset, f)
    
    return dataset

def get_sample_data(size: str = 'medium') -> List[Dict[str, Any]]:
    """
    Get sample data of the specified size
    
    Args:
        size: 'small', 'medium', or 'large'
        
    Returns:
        List of sample data items
    """
    if size == 'small':
        return generate_posts_batch(count=10)
    elif size == 'medium':
        return generate_posts_batch(count=100)
    elif size == 'large':
        return generate_posts_batch(count=1000)
    else:
        raise ValueError(f"Invalid size: {size}. Choose from 'small', 'medium', or 'large'.")

if __name__ == "__main__":
    # Generate sample data when run directly
    data = generate_large_dataset(num_posts=1000, output_file="sample_data.json")
    print(f"Generated {len(data)} sample posts") 
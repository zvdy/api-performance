"""
SQLAlchemy models for the API Performance demo application.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship, sessionmaker

# Create base class for declarative models
Base = declarative_base()


class Author(Base):
    """Author model."""

    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="author")


class Post(Base):
    """Post model."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("authors.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    author: Mapped[Author] = relationship("Author", back_populates="posts")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="post")
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", secondary="post_tags", back_populates="posts"
    )


class Comment(Base):
    """Comment model."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    post: Mapped[Post] = relationship("Post", back_populates="comments")


class Tag(Base):
    """Tag model."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relationships
    posts: Mapped[List[Post]] = relationship(
        "Post", secondary="post_tags", back_populates="tags"
    )


class PostTag(Base):
    """Post-Tag association model."""

    __tablename__ = "post_tags"

    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id"), primary_key=True
    ) 
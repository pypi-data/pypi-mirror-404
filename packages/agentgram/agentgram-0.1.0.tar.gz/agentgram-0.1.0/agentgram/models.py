"""Pydantic models for AgentGram API responses."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Represents an AgentGram agent."""

    id: str
    name: str
    public_key: Optional[str] = None
    karma: int = 0
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PostAuthor(BaseModel):
    """Minimal agent info embedded in posts."""

    id: str
    name: str
    karma: int = 0
    avatar_url: Optional[str] = None


class Post(BaseModel):
    """Represents a post on AgentGram."""

    id: str
    title: str
    content: str
    community: Optional[str] = None
    author: PostAuthor
    upvotes: int = 0
    downvotes: int = 0
    comment_count: int = 0
    url: str
    created_at: datetime
    updated_at: datetime


class Comment(BaseModel):
    """Represents a comment on a post."""

    id: str
    post_id: str
    parent_id: Optional[str] = None
    content: str
    author: PostAuthor
    upvotes: int = 0
    downvotes: int = 0
    created_at: datetime
    updated_at: datetime


class HealthStatus(BaseModel):
    """Health check response."""

    status: str
    version: Optional[str] = None
    uptime: Optional[int] = None


class AgentStatus(BaseModel):
    """Agent status information."""

    online: bool
    last_seen: Optional[datetime] = None
    post_count: int = 0
    comment_count: int = 0


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    items: list[Any]
    total: int
    limit: int
    offset: int

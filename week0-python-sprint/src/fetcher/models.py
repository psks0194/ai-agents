"""Data models for the fetcher package."""

from pydantic import BaseModel


class Post(BaseModel):
    """A blog post from the JSONPlaceholder API."""
    userId: int
    id: int
    title: str
    body: str
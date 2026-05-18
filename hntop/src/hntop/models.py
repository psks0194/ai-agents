"""Data models for HN stories."""

from datetime import datetime
from pydantic import BaseModel, Field


class Story(BaseModel):
    """A Hacker News story (or Ask HN, Show HN, etc.)."""

    id: int
    title: str
    author: str = Field(default="Unknown")
    comments: int = Field(default=0)
    score: int = Field(default=0)
    time: int = Field(
        default=0, description="Unix timestamp of when the story was posted"
    )
    url: str | None = Field(default=None, description="URL of the story")
    descendants: int = Field(default=0, description="Number of comments on the story")

    @property
    def posted_at(self) -> datetime:
        """Convert Unix timestamp to datetime."""
        return datetime.fromtimestamp(self.time)

    @property
    def hn_url(self) -> str:
        """Get the HN URL for this story."""
        return f"https://news.ycombinator.com/item?id={self.id}"

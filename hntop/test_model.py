"""Quick smoke test for the Story model."""


from hntop.models import Story


def main() -> None:
    """Test the Story model."""
    raw_story = {
        "id": 123456789,
        "title": "Test Story",
        "by": "testuser",
        "score": 10,
        "time": 1234567890,
        "url": "https://www.google.com",
        "descendants": 5,
    }

    story = Story.model_validate(raw_story)
    print(f"{story.id}: {story.title}")
    print(f"{story.by} posted at {story.posted_at}")
    print(f"{story.score} points and {story.descendants} comments")
    print(f"URL: {story.url}")
    print(f"HN URL: {story.hn_url}")

    # Test missing URL (Ask HN style)
    raw2 = {
        "id": 12346,
        "title": "Ask HN: How do you stay focused?",
        "by": "someone",
        "score": 50,
        "descendants": 12,
        "time": 1747800000,
        # no url
    }
    story2 = Story.model_validate(raw2)
    print(f"\nStory 2 URL: {story2.url}")  # None


if __name__ == "__main__":
    main()

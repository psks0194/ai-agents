"""Pydantic models that flow through the content pipeline."""

from pydantic import BaseModel, Field


class Angle(BaseModel):
    """The output of Stage 1: a specific, contrarian angle on the topic."""

    angle: str = Field(
        description=(
            "A specific, sharp angle on the topic. Not 'X is interesting' — "
            "something like 'most people use X wrong' or 'the real win of X is Y'. "
            "Should be a single declarative sentence."
        )
    )
    why_it_lands: str = Field(
        description="One sentence explaining why this angle is non-obvious."
    )


class OutlineBeat(BaseModel):
    """One beat of the outline."""

    claim: str = Field(description="The single claim of this beat, one sentence.")
    example: str = Field(
        description="A concrete, specific example or detail that supports the claim."
    )


class Outline(BaseModel):
    """The output of Stage 2: a structured outline for the post."""

    hook: str = Field(description="The opening line. Should be punchy and specific.")
    beats: list[OutlineBeat] = Field(
        description="Three beats developing the angle.",
        min_length=3,
        max_length=3,
    )
    close: str = Field(
        description="The final line. Memorable and pithy. Often the post's takeaway."
    )


class Draft(BaseModel):
    """The output of Stage 3: the final post."""

    post: str = Field(description="The full post text, ready to publish. ~250 words.")
    word_count: int = Field(description="Number of words in the post.")


class Critique(BaseModel):
    """The output of the Critic stage."""

    verdict: str = Field(
        description="Either 'ship' or 'revise'. Ship means the post is publishable as-is."
    )
    reasons: list[str] = Field(
        description=(
            "If verdict is 'revise', the specific issues. If 'ship', what's working well. "
            "Should be concrete and actionable — not 'could be better', but 'beat 2 is "
            "abstract — needs a specific example'."
        ),
        min_length=1,
        max_length=6,
    )

"""LLM-as-judge for IntellAIgent thread quality.

A judge is a noisy, biased instrument. This module builds it carefully:
- an ANCHORED rubric (each score level described) to fight clustering
- REASONING BEFORE SCORE (the model must justify before committing)
- structured output (parse the verdict, keep the 'why')
- temperature 0 (minimize, though not eliminate, run-to-run noise)
"""

from __future__ import annotations

import json

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from evals.config import settings


class JudgeVerdict(BaseModel):
    """Structured judge output. Reasoning first, then a committed score."""

    reasoning: str = Field(description="2-3 sentences justifying the score.")
    score: int = Field(description="Integer 1-5 per the rubric.", ge=1, le=5)
    on_voice: bool = Field(description="True if it clearly reads as IntellAIgent.")


_RUBRIC = """You are grading an X thread for the IntellAIgent voice. IntellAIgent
is practitioner-contrarian: concrete over abstract, no hype words, picks a
defensible side, measures honestly (states costs and failures, not just wins),
short punchy sentences.

Score 1-5 using THESE ANCHORS. Use the full range — do not default to 3 or 4:
- 5: Sharp, specific angle. Fully concrete (names tools/numbers/tradeoffs). Zero
     hype. Takes a clear, defensible side. Honest about cost. Reads unmistakably
     as a builder who measured something.
- 4: Strong and on-voice, with minor softness (one generic line or mild hedge).
- 3: Serviceable but generic in places, or hedges the central claim, or leans
     abstract more than concrete.
- 2: Mostly generic/abstract, OR contains hype words, OR has no real angle.
- 1: Hype-filled, vague, listicle-flavored, no defensible point of view.

First write 2-3 sentences of reasoning citing SPECIFIC lines. THEN give the score.
Respond ONLY with JSON: {"reasoning": "...", "score": N, "on_voice": true/false}
"""


async def judge_thread(thread_text: str, angle: str = "") -> JudgeVerdict:
    """Judge one thread. Returns a structured verdict."""
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    context = f"Intended angle: {angle}\n\n" if angle else ""
    resp = await client.messages.create(
        model=settings.judge_model,
        max_tokens=400,
        temperature=0,  # minimize noise — but Phase 3 shows it's not zero
        system=_RUBRIC,
        messages=[{"role": "user", "content": f"{context}Thread:\n{thread_text}"}],
    )

    raw = resp.content[0].text.strip()
    # Defensive: strip accidental markdown fences before parsing.
    if raw.startswith("```"):
        raw = raw.split("```")[1].removeprefix("json").strip()

    try:
        return JudgeVerdict.model_validate_json(raw)
    except Exception:
        # Last-resort salvage so one malformed response doesn't kill a run.
        data = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])
        return JudgeVerdict(**data)

"""Smallest Gemini call — parallel to Day 1 (Anthropic) and Day 3 (OpenAI)."""

from google import genai

from week1_tri_provider_agent.config import settings


def main() -> None:
    client = genai.Client(api_key=settings.google_api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="In one sentence: what is async I/O good for?",
    )

    # Extract the text
    text = response.text
    print(text)

    # Token usage — Gemini's terminology again
    usage = response.usage_metadata
    print(
        f"\n[input tokens: {usage.prompt_token_count}, "
        f"output tokens: {usage.candidates_token_count}]"
    )


if __name__ == "__main__":
    main()

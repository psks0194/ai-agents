"""Smallest OpenAI call — direct parallel to Day 1's first_call.py."""

from week1_tri_provider_agent.config import settings
from openai import OpenAI
from rich import print


def main() -> None:
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "In one sentence: what is async I/O good for?"}
        ],
    )

    # Extract the text response
    text = response.choices[0].message.content
    print(text)

    # Token usage
    print(
        f"\nInput tokens: {response.usage.prompt_tokens}, "
        f"\nOutput tokens: {response.usage.completion_tokens}"
    )


if __name__ == "__main__":
    main()

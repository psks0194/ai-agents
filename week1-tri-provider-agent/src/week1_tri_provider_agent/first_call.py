"""The smallest working call to Claude. Just one prompt, one response."""

from week1_tri_provider_agent.config import settings
from anthropic import Anthropic


def main() -> None:
    client = Anthropic(api_key=settings.anthropic_api_key)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "In one sentence: what is async I/O good for?"}
        ],
    )

    print(f"Claude says: {message.content[0].text}")

    print(
        f"Input tokens: {message.usage.input_tokens} | Output tokens: {message.usage.output_tokens}"
    )


if __name__ == "__main__":
    main()

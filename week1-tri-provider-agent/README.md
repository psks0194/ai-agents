# week1-tri-provider-agent

Building the same agent across Anthropic, OpenAI, and Gemini SDKs — feeling the protocol underneath every framework.

## Status (Day 1)

- ✅ Anthropic SDK — basic call, multi-turn conversation, system prompts, streaming
- ⏳ Anthropic SDK — tool use (Day 2)
- ⏳ OpenAI SDK — port (Day 3)
- ⏳ Gemini SDK — port (Day 4)
- ⏳ Streaming and structured outputs polish (Day 5)

## Run

\`\`\`bash
# Streaming chat with Claude
uv run python -m week1_tri_provider_agent.streaming_chat

# Non-streaming chat
uv run python -m week1_tri_provider_agent.chat
\`\`\`

## Architecture (so far)

\`\`\`
src/week1_tri_provider_agent/
├── config.py            # pydantic-settings config
├── first_call.py        # smallest possible LLM call
├── chat.py              # multi-turn conversation
└── streaming_chat.py    # multi-turn + streaming
\`\`\`

Part of the IntellAIgent Agent Builder Curriculum, Week 1.
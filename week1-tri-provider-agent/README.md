# week1-tri-provider-agent

Building the same agent across Anthropic, OpenAI, and Gemini SDKs — feeling the protocol underneath every framework.

## Status (Day 3 — 2026-05-21)

- ✅ Anthropic SDK — basic call, multi-turn conversation, system prompts, streaming (Day 1)
- ✅ Anthropic SDK — tool use loop, calculator + time + web fetch (Day 2)
- ✅ OpenAI SDK — full port of the tool-using agent (Day 3)
- ⏳ Gemini SDK — port (Day 4)
- ⏳ Streaming and structured outputs polish (Day 5)

## Run

\`\`\`bash
# --- Anthropic ---
# Tool-using agent (calculator, current time, web fetch)
uv run python -m week1_tri_provider_agent.agent

# Streaming chat with Claude
uv run python -m week1_tri_provider_agent.streaming_chat

# Non-streaming chat
uv run python -m week1_tri_provider_agent.chat

# --- OpenAI ---
# Tool-using agent (same tools, OpenAI schema + loop)
uv run python -m week1_tri_provider_agent.openai_agent

# Multi-turn chat with GPT-4o-mini
uv run python -m week1_tri_provider_agent.openai_chat

# Smallest possible OpenAI call
uv run python -m week1_tri_provider_agent.openai_first_call
\`\`\`

## Architecture (so far)

\`\`\`
src/week1_tri_provider_agent/
├── config.py              # pydantic-settings config (Anthropic + OpenAI keys)
├── tools.py               # provider-agnostic tool implementations (calculator, time, fetch)
│
├── first_call.py          # Anthropic: smallest possible LLM call
├── chat.py                # Anthropic: multi-turn conversation
├── streaming_chat.py      # Anthropic: multi-turn + streaming
├── agent.py               # Anthropic: agent loop — call → tool_use → tool_result → repeat
│
├── openai_first_call.py   # OpenAI: smallest possible LLM call
├── openai_chat.py         # OpenAI: multi-turn conversation
├── openai_tools.py        # OpenAI: tool schema wrappers (reuses tools.py implementations)
└── openai_agent.py        # OpenAI: agent loop — direct port of agent.py
\`\`\`

The tool *implementations* in `tools.py` are shared across providers — only the
schema wrapper and the agent loop's API vocabulary differ between SDKs.

Part of the IntellAIgent Agent Builder Curriculum, Week 1.
# week4-mastra

The agent patterns one more time — a **fourth** framework: **Mastra** (TypeScript).
Same throughline as the rest of the curriculum: *an agent is a loop* (`call → tool
→ result → call → final answer`). Each framework just hides or exposes that loop
differently. Mastra's stance: **you declare an `Agent` with its `tools`, and the
framework runs the loop for you** — much like the OpenAI Agents SDK, but in TS and
with a built-in model router, Studio UI, scorers, and observability.

Day 1 builds the canonical tool-use agent. Day 2 goes past a single agent into
Mastra's **workflows** — multi-step pipelines with typed contracts between steps,
sequential chaining and parallel fan-out/fan-in — plus a **RAG** retrieval demo
(chunking → embeddings → vector search).

## Status (Day 1 — 2026-06-24)

- ✅ Tool-using agent — calculator / current-time / fetch-url, the canonical tool-use loop in Mastra (`agents/tool-agent.ts`)
- ✅ Three utility tools defined with `createTool` + Zod schemas (`tools/utility-tool.ts`)
- ✅ Standalone runner that drives the agent over a few prompts (`run-tool-agent.ts`)
- ✅ Agent registered in the Mastra instance (`mastra/index.ts`)
- ✅ Debugged it end-to-end — four separate fixes (see **Issues fixed today**)

This sits alongside the bootstrapped weather example (`weather-agent`,
`weather-tool`, `weather-workflow`, `weather-scorer`) that ships with a new Mastra
project. Day 1's work is the **tool agent** and getting it to actually run.

## Status (Day 2 — 2026-06-25)

Workflows and RAG.

- ✅ Content agents — four single-purpose agents: scout, outliner, drafter, critic (`agents/content-agent.ts`)
- ✅ Content pipeline — a **sequential** workflow chaining them with typed step contracts (`workflows/content-workflow.ts` + `run-content-workflow.ts`)
- ✅ Parallel critics — a **fan-out/fan-in** workflow running two critics concurrently (`workflows/parallel-critic-workflow.ts` + `run-parallel-critic.ts`)
- ✅ RAG demo — chunking, OpenAI embeddings, LibSQL vector store, similarity retrieval (`rag-demo.ts`)
- ✅ All agents/workflows registered in the Mastra instance; whole project typechecks clean

## The tool agent

The same calculator / time / fetch-url loop built in Week 1 (raw Anthropic SDK),
Week 3 (Pydantic AI), and Week 4's OpenAI SDK — now in Mastra:

- **Week 1**: raw Anthropic SDK — *you* write the ~80-line loop.
- **Week 3**: Pydantic AI — `@agent.tool`, loop hidden.
- **Week 4 / OpenAI SDK**: `@function_tool`, `Runner` manages the loop.
- **Week 4 / Mastra**: `createTool(...)`, attach via `tools: {…}`, the `Agent`
  runs the loop. `agent.generate(prompt)` returns the final text plus usage.

### Tools — `tools/utility-tool.ts`

Each tool is a `createTool({ id, description, inputSchema, outputSchema, execute })`.
The `description` + Zod `inputSchema` become the schema the model sees. Three tools:

| Tool | id | What it does |
|---|---|---|
| `calculatorTool` | `calculator` | Evaluates a math expression via a restricted `Function(...)` |
| `currentTimeTool` | `get-current-time` | Current time for an IANA timezone |
| `fetchUrlTool` | `fetch-url` | Fetches a URL, returns the first 5000 chars |

> **API note:** in this Mastra version (`@mastra/core` ^1.46), `execute` receives
> the validated input **directly** — `execute: async ({ expression }) => …` — *not*
> wrapped in a `{ context }` object. This matches the bootstrapped `weather-tool.ts`.

### Agent — `agents/tool-agent.ts`

```ts
export const toolAgent = new Agent({
  id: "tool-agent",
  name: "Tool Using Assistant",
  instructions: "… use the appropriate tool … give a clear, concise final answer.",
  model: "anthropic/claude-haiku-4-5",
  tools: { calculatorTool, currentTimeTool, fetchUrlTool },
});
```

Two Mastra-specific things to notice:

1. **Model router string.** `model: "anthropic/claude-haiku-4-5"` — Mastra resolves
   the provider/model through its built-in **models.dev gateway**. No per-agent
   `api_key=` and no `@ai-sdk/anthropic` import; the gateway reads
   `process.env.ANTHROPIC_API_KEY` *lazily, at request time*.
2. **Registration.** Every agent must be registered in the Mastra instance
   (`mastra/index.ts`) to be reachable via `mastra.getAgent('toolAgent')` and to
   show up in Studio.

### Runner — `run-tool-agent.ts`

A standalone script (run with `tsx`) that fetches the agent and loops over three
prompts — one per tool — printing the answer, elapsed time, and token usage.

> **`import 'dotenv/config'` is required at the top.** Running a script directly
> with `tsx` does **not** load `.env`. The model router reads
> `process.env.ANTHROPIC_API_KEY` at request time, so without dotenv the gateway
> throws *"Could not find API key process.env.ANTHROPIC_API_KEY"* even though the
> key is sitting in `.env`. (`mastra dev`/`mastra build` load `.env` on their own;
> a raw `tsx` invocation does not.)

## Issues fixed (Day 1)

Getting the tool agent from "written" to "running" took these fixes:

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | Model import wouldn't resolve | `import { anthropic } from "@mastra/core/llm"` + `anthropic(...)` — not a usable API here, and no `@ai-sdk/anthropic` installed | Use the model-router string `model: "anthropic/claude-haiku-4-5"` |
| 2 | Tools import failed | Imported from `../tools/utility-tools` (plural) | File is `utility-tool.ts` (singular) |
| 3 | Agent unreachable | Not registered in the Mastra instance | Add to `agents: { weatherAgent, toolAgent }` in `index.ts` |
| 4 | `tsc` errors on `context` | Tools used the old `execute: async ({ context }) => …` signature | Destructure input directly: `async ({ expression }) => …` |
| 5 | Runtime: *Could not find API key* | Raw `tsx` doesn't load `.env`; gateway reads `process.env` lazily | Add `import 'dotenv/config'` to the runner |

After these, `npx tsx src/run-tool-agent.ts` runs all three prompts and the agent
calls the right tool each time.

---

# Day 2 — Workflows

A Mastra **workflow** is a graph of typed **steps**. Each step is a
`createStep({ id, inputSchema, outputSchema, execute })` — a unit with a Zod
contract on its input and output. You wire steps together with combinators
(`.then(...)`, `.parallel([...])`, `.branch(...)`, …) and `.commit()` the result.
The engine validates the contract between every step, so a type mismatch in the
chain is a compile error, not a runtime surprise.

Inside a step, `execute` receives `{ inputData }` (validated against `inputSchema`)
and returns a value matching `outputSchema`. Steps call agents via
`agent.generate(prompt, { structuredOutput: { schema } })`, and read the typed
result off `result.object`.

## The content pipeline — sequential (`content-workflow.ts`)

Four single-purpose agents from `agents/content-agent.ts`, chained in order:

```
topic → scout → outline → drafter → critic → verdict
```

| Agent | Role |
|---|---|
| `scoutAgent` | Finds one sharp, specific angle on the topic |
| `outlineAgent` | Turns the angle into a hook + 3 beats + close |
| `drafterAgent` | Writes a ~250-word post from the outline |
| `criticAgent` | Editor verdict: ship or revise, with reasons |

Each step's `outputSchema` is the next step's `inputSchema` — the typed contract is
literally the handoff. The workflow is `.then(scout).then(outline).then(drafter)
.then(critic).commit()`. Run it with `npx tsx src/run-content-workflow.ts`; the
runner reads each step's output from `result.steps[id]` and the final verdict from
`result.result`.

## Parallel critics — fan-out / fan-in (`parallel-critic-workflow.ts`)

Same draft, but judged on two independent dimensions **at once**:

```
topic → scout → outline → drafter ─┬─→ voice-critic ──┐
                                   └─→ accuracy-critic ┘ → combine → verdict
```

- `.parallel([voiceCriticStep, accuracyCriticStep])` runs both critics
  concurrently against the same draft. Each is its own dedicated `Agent`
  (`voiceCritic`, `accuracyCritic`) scoring 1–10.
- `.parallel(...)` produces a record **keyed by each step's `id`** — so the
  `combine` step's input is `{ 'voice-critic': …, 'accuracy-critic': … }`, and it
  ships only if **both** scores are ≥ 7.

> **Typing gotcha worth remembering:** because the critic steps use *inline literal*
> ids (`id: 'voice-critic'`), `.parallel(...)` preserves those exact keys, so a
> fixed-key `z.object({ 'voice-critic', 'accuracy-critic' })` input typechecks. If
> the step id were a `string` variable instead, the parallel output collapses to an
> index signature (`Record<string, …>`) and the combine input must be a
> `z.record(...)`. Literal ids are the nicer pattern.

Run it with `npx tsx src/run-parallel-critic.ts`.

## RAG — retrieval over notes (`rag-demo.ts`)

A from-scratch **retrieval** demo (the "R" in RAG) over a few curriculum notes.
Two phases:

**Indexing** (`buildIndex`)
1. **Chunk** — `MDocument.fromMarkdown(notes).chunk({ strategy: 'recursive',
   maxSize: 256, overlap: 30 })`. Markdown-aware recursive splitting into ~256-unit
   chunks that overlap by 30 so facts straddling a cut aren't orphaned.
2. **Embed** — `embedMany({ model: openai.embedding('text-embedding-3-small') })`
   turns each chunk into a 1536-dim vector capturing its *meaning*.
3. **Store** — `LibSQLVector` (file-based, no external service): `createIndex({
   dimension: 1536 })` then `upsert({ vectors, metadata })`, keeping each chunk's
   text in `metadata` so retrieval can return readable passages.

**Querying** (`query`)
1. **Embed the question** with the *same* model (must share the vector space).
2. **Search** — `store.query({ queryVector, topK: 2 })` returns the 2 nearest
   chunks by cosine similarity, each with a `score` and its `metadata.text`.

> This file stops at retrieval — the retrieved chunks are printed, not yet fed to
> an LLM. To make it full RAG, add a generation step that stuffs the top chunks
> into a prompt and asks an agent to answer grounded in them.
>
> **Different provider:** embeddings come from **OpenAI** (`@ai-sdk/openai`), so
> this demo needs `OPENAI_API_KEY` — not the Anthropic key the agents use. It also
> has no `dotenv` import, so run it as `npx tsx --env-file=.env src/rag-demo.ts`.

## Recurring version-drift fixes (Day 2)

Most of Day 2 was reconciling code written against older API shapes with the
installed versions. The same handful of fixes kept recurring:

| Symptom | Cause | Fix |
|---|---|---|
| `anthropic(...)` from `@mastra/core/llm` won't resolve, `model` is `any` | Old per-model import; not installed | Model-router string `"anthropic/claude-haiku-4-5"` |
| `Property 'id' is missing` on `new Agent({...})` | `id` is now required on `AgentConfig` | Add `id: '…'` (distinct from display `name`) |
| `Cannot find module '../agents/content-agents'` | Wrong path/filename | `'../agents/content-agent'` (singular) |
| `'size' does not exist` on `chunk(...)` | Renamed chunk option | `maxSize` (with `overlap`) |
| `'connectionUrl' does not exist` on `LibSQLVector` | Config renamed + `id` now required | `{ id, url: 'file:./rag-demo.db' }` |
| `verdict` typed `string`, not `'ship'\|'revise'` | Ternary literals widen to `string` | `('ship' as const) : ('revise' as const)` |
| *Missing API key* when run via `tsx` | Raw `tsx` doesn't load `.env` | `import 'dotenv/config'` (or `--env-file=.env`) |

## Run

```shell
# Tool agent — calculator / time / fetch-url over 3 prompts
npx tsx src/run-tool-agent.ts

# Content pipeline — scout → outline → drafter → critic (sequential)
npx tsx src/run-content-workflow.ts

# Parallel critics — voice + accuracy critics run concurrently, then combine
npx tsx src/run-parallel-critic.ts

# RAG retrieval demo — needs OPENAI_API_KEY; has no dotenv import, so pass --env-file
npx tsx --env-file=.env src/rag-demo.ts

# Mastra dev server + Studio UI (auto-loads .env)
npm run dev    # → http://localhost:4111
```

Needs `ANTHROPIC_API_KEY` (agents/workflows) and `OPENAI_API_KEY` (RAG embeddings)
in `week4-mastra/.env`. `npm run dev` loads `.env` automatically; the agent/workflow
runners load it via `import 'dotenv/config'`; `rag-demo.ts` relies on `--env-file`.

## Architecture

```
src/
├── run-tool-agent.ts                  # Runner — tool agent over 3 prompts (Day 1)
├── run-content-workflow.ts            # Runner — sequential content pipeline (Day 2)
├── run-parallel-critic.ts             # Runner — parallel-critic workflow (Day 2)
├── rag-demo.ts                        # Standalone RAG retrieval demo (Day 2)
└── mastra/
    ├── index.ts                       # Mastra instance — registers everything
    ├── agents/
    │   ├── tool-agent.ts              # Tool-using agent (Day 1)
    │   ├── content-agent.ts           # scout / outliner / drafter / critic (Day 2)
    │   └── weather-agent.ts           # Bootstrapped example
    ├── tools/
    │   ├── utility-tool.ts            # calculator / current-time / fetch-url (Day 1)
    │   └── weather-tool.ts            # Bootstrapped example
    ├── workflows/
    │   ├── content-workflow.ts        # Sequential: scout→outline→drafter→critic (Day 2)
    │   ├── parallel-critic-workflow.ts# Fan-out/fan-in: 2 critics in parallel (Day 2)
    │   └── weather-workflow.ts        # Bootstrapped example
    └── scorers/weather-scorer.ts
```

## Conventions (see `AGENTS.md`)

- Load the `mastra` skill before any Mastra work — APIs change between versions; don't rely on cached knowledge.
- Register all agents, tools, workflows, and scorers in `src/mastra/index.ts`.
- Use the `dev` / `build` scripts from `package.json` rather than calling `mastra dev` / `mastra build` directly.

## Getting started (bootstrapped Mastra)

Start the development server:

```shell
npm run dev
```

Open [http://localhost:4111](http://localhost:4111) for [Mastra Studio](https://mastra.ai/docs/studio/overview) — an interactive UI for building and testing agents, plus a local REST API. Edit files in `src/mastra` and the dev server reloads automatically.

## Learn more

To learn more about Mastra, visit the [documentation](https://mastra.ai/docs/) — [agents](https://mastra.ai/docs/agents/overview), [tools](https://mastra.ai/docs/agents/using-tools), [workflows](https://mastra.ai/docs/workflows/overview), [scorers](https://mastra.ai/docs/evals/overview), and [observability](https://mastra.ai/docs/observability/overview).

Part of the IntellAIgent Agent Builder Curriculum, Week 4.

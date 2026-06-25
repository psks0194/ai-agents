import { createStep, createWorkflow } from "@mastra/core/workflows";
import { z } from "zod";
import {
  scoutAgent,
  outlineAgent,
  drafterAgent,
  criticAgent,
} from "../agents/content-agent";

// ============================================================
// Schemas — the typed contracts between steps
// ============================================================

const angleSchema = z.object({
  angle: z.string().describe("A sharp, specific declarative sentence."),
  reasoning: z.string().describe("One sentence on why this angle lands."),
});

const outlineSchema = z.object({
  hook: z.string(),
  beats: z
    .array(z.object({ claim: z.string(), example: z.string() }))
    .length(3),
  close: z.string(),
});

const draftSchema = z.object({
  post: z.string().describe("The full post, ~250 words."),
  wordCount: z.number(),
});

const critiqueSchema = z.object({
  verdict: z.enum(["ship", "revise"]),
  reasons: z.array(z.string()),
});

// Inferred types — handy for consumers that read step outputs by id, where
// the string-keyed `getWorkflow(...)` loses the per-step generics.
export type Angle = z.infer<typeof angleSchema>;
export type Outline = z.infer<typeof outlineSchema>;
export type Draft = z.infer<typeof draftSchema>;
export type Critique = z.infer<typeof critiqueSchema>;

// ============================================================
// Steps — each one wraps an agent call with typed I/O
// ============================================================

const scoutStep = createStep({
  id: "scout",
  inputSchema: z.object({ topic: z.string() }),
  outputSchema: angleSchema,
  execute: async ({ inputData }) => {
    console.log("  → scout");
    const result = await scoutAgent.generate(
      `Topic: ${inputData.topic}\n\nGenerate one sharp angle.`,
      { structuredOutput: { schema: angleSchema } }
    );
    return result.object;
  },
});

const outlineStep = createStep({
  id: "outline",
  inputSchema: angleSchema,
  outputSchema: outlineSchema,
  execute: async ({ inputData }) => {
    console.log("  → outline");
    const result = await outlineAgent.generate(
      `Angle: ${inputData.angle}\n\nBuild the outline.`,
      { structuredOutput: { schema: outlineSchema } }
    );
    return result.object;
  },
});

const drafterStep = createStep({
  id: "drafter",
  inputSchema: outlineSchema,
  outputSchema: draftSchema,
  execute: async ({ inputData }) => {
    console.log("  → drafter");
    const beatsText = inputData.beats
      .map((b) => `- ${b.claim}\n  Example: ${b.example}`)
      .join("\n");
    const result = await drafterAgent.generate(
      `Hook: ${inputData.hook}\n\nBeats:\n${beatsText}\n\n` +
        `Close: ${inputData.close}\n\nWrite the post as flowing prose.`,
      { structuredOutput: { schema: draftSchema } }
    );
    return result.object;
  },
});

const criticStep = createStep({
  id: "critic",
  inputSchema: draftSchema,
  outputSchema: critiqueSchema,
  execute: async ({ inputData }) => {
    console.log("  → critic");
    const result = await criticAgent.generate(
      `Post:\n\n${inputData.post}\n\nEvaluate.`,
      { structuredOutput: { schema: critiqueSchema } }
    );
    return result.object;
  },
});

// ============================================================
// The workflow — chain the steps
// ============================================================

export const contentWorkflow = createWorkflow({
  id: "content-pipeline",
  inputSchema: z.object({ topic: z.string() }),
  outputSchema: critiqueSchema,
})
  .then(scoutStep)
  .then(outlineStep)
  .then(drafterStep)
  .then(criticStep)
  .commit();
import { createStep, createWorkflow } from '@mastra/core/workflows';
import { z } from 'zod';
import { Agent } from '@mastra/core/agent';
import { scoutAgent, outlineAgent, drafterAgent } from '../agents/content-agent';

// Two specialized critics
export const voiceCritic = new Agent({
    id: 'voice-critic',
    name: 'VoiceCritic',
    instructions:
        'You evaluate writing ONLY for voice: is it punchy, concrete, free of ' +
        'hedging and AI-thought-leader cliches? Give a score 1-10 and one note.',
    model: 'anthropic/claude-haiku-4-5',
});

export const accuracyCritic = new Agent({
    id: 'accuracy-critic',
    name: 'AccuracyCritic',
    instructions:
        'You evaluate writing ONLY for technical accuracy: are the claims ' +
        'correct, are examples real, is anything misleading? Score 1-10 + one note.',
    model: 'anthropic/claude-haiku-4-5',
});

// Schemas
const angleSchema = z.object({ angle: z.string(), reasoning: z.string() });
const outlineSchema = z.object({
    hook: z.string(),
    beats: z.array(z.object({ claim: z.string(), example: z.string() })).length(3),
    close: z.string(),
});
const draftSchema = z.object({ post: z.string(), wordCount: z.number() });
const scoreSchema = z.object({ score: z.number(), note: z.string() });

// Reuse scout/outline/drafter steps (abbreviated — same as before)
const scoutStep = createStep({
    id: 'scout',
    inputSchema: z.object({ topic: z.string() }),
    outputSchema: angleSchema,
    execute: async ({ inputData }) => {
        console.log('  → scout');
        const r = await scoutAgent.generate(
            `Topic: ${inputData.topic}\n\nGenerate one sharp angle.`,
            { structuredOutput: { schema: angleSchema } },
        );
        return r.object;
    },
});

const outlineStep = createStep({
    id: 'outline',
    inputSchema: angleSchema,
    outputSchema: outlineSchema,
    execute: async ({ inputData }) => {
        console.log('  → outline');
        const r = await outlineAgent.generate(`Angle: ${inputData.angle}\n\nBuild the outline.`, {
            structuredOutput: { schema: outlineSchema },
        });
        return r.object;
    },
});

const drafterStep = createStep({
    id: 'drafter',
    inputSchema: outlineSchema,
    outputSchema: draftSchema,
    execute: async ({ inputData }) => {
        console.log('  → drafter');
        const beatsText = inputData.beats.map((b) => `- ${b.claim}: ${b.example}`).join('\n');
        const r = await drafterAgent.generate(
            `Hook: ${inputData.hook}\nBeats:\n${beatsText}\nClose: ${inputData.close}\n\nWrite the post.`,
            { structuredOutput: { schema: draftSchema } },
        );
        return r.object;
    },
});

// Two critic steps — these will run in PARALLEL
const voiceCriticStep = createStep({
    id: 'voice-critic',
    inputSchema: draftSchema,
    outputSchema: scoreSchema,
    execute: async ({ inputData }) => {
        console.log('  → voice critic');
        const r = await voiceCritic.generate(`Evaluate the voice of:\n\n${inputData.post}`, {
            structuredOutput: { schema: scoreSchema },
        });
        return r.object;
    },
});

const accuracyCriticStep = createStep({
    id: 'accuracy-critic',
    inputSchema: draftSchema,
    outputSchema: scoreSchema,
    execute: async ({ inputData }) => {
        console.log('  → accuracy critic');
        const r = await accuracyCritic.generate(`Evaluate the accuracy of:\n\n${inputData.post}`, {
            structuredOutput: { schema: scoreSchema },
        });
        return r.object;
    },
});

// Combine step — reads BOTH parallel critics' outputs
const combineStep = createStep({
    id: 'combine',
    inputSchema: z.object({
        'voice-critic': scoreSchema,
        'accuracy-critic': scoreSchema,
    }),
    outputSchema: z.object({
        verdict: z.enum(['ship', 'revise']),
        voiceScore: z.number(),
        accuracyScore: z.number(),
    }),
    execute: async ({ inputData }) => {
        const voice = inputData['voice-critic'].score;
        const accuracy = inputData['accuracy-critic'].score;
        console.log(`  → combine (voice=${voice}, accuracy=${accuracy})`);
        // Ship only if BOTH critics score >= 7
        const verdict = voice >= 7 && accuracy >= 7 ? ('ship' as const) : ('revise' as const);
        return { verdict, voiceScore: voice, accuracyScore: accuracy };
    },
});

// The workflow with a parallel section
export const parallelCriticWorkflow = createWorkflow({
    id: 'parallel-critic-pipeline',
    inputSchema: z.object({ topic: z.string() }),
    outputSchema: z.object({
        verdict: z.enum(['ship', 'revise']),
        voiceScore: z.number(),
        accuracyScore: z.number(),
    }),
})
    .then(scoutStep)
    .then(outlineStep)
    .then(drafterStep)
    .parallel([voiceCriticStep, accuracyCriticStep])
    .then(combineStep)
    .commit();

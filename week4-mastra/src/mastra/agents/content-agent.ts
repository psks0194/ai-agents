import { Agent } from '@mastra/core/agent';

export const scoutAgent = new Agent({
    id: 'scout-agent',
    name: 'Scout',
    instructions:
        'You find sharp, specific angles on technical topics. Avoid generic ' +
        "'X is the future' hype. Look for what people miss, what's overrated, " +
        'what the real win actually is. Return one sharp angle as a single ' +
        'declarative sentence, plus one sentence on why it lands.',
    model: 'anthropic/claude-haiku-4-5',
});

export const outlineAgent = new Agent({
    id: 'outline-agent',
    name: 'Outliner',
    instructions:
        'Given an angle, produce a tight outline: a hook, three beats, and a ' +
        'close. Each beat is one specific claim with one concrete example. ' +
        'Examples must be concrete — code patterns, product names, numbers.',
    model: 'anthropic/claude-haiku-4-5',
});

export const drafterAgent = new Agent({
    id: 'drafter-agent',
    name: 'Drafter',
    instructions:
        "You're a senior engineer-turned-writer. Short sentences, no hedging, " +
        "concrete details over abstractions. Never use 'unlock', 'leverage', " +
        "'revolutionize'. ~250 words, prose only, no headings.",
    model: 'anthropic/claude-haiku-4-5',
});

export const criticAgent = new Agent({
    id: 'critic-agent',
    name: 'Critic',
    instructions:
        "You're a tough editor for an engineer-builder audience. The bar: would " +
        'a senior engineer screenshot this? Give a verdict (ship or revise) and ' +
        'specific, actionable feedback.',
    model: 'anthropic/claude-haiku-4-5',
});

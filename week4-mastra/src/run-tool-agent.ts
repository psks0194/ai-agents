import 'dotenv/config';
import { mastra } from './mastra';

async function main() {
    const agent = mastra.getAgent('toolAgent');

    const prompts = [
        'What is 47 * 83 + 199?',
        "What time is it in Mumbai and Tokyo? What's the time difference in hours?",
        'Fetch https://hacker-news.firebaseio.com/v0/topstories.json and tell me the first 3 IDs.',
    ];

    for (const prompt of prompts) {
        console.log(`\nYou: ${prompt}`);

        const start = performance.now();
        const result = await agent.generate(prompt);
        const elapsed = (performance.now() - start) / 1000;

        console.log(`\nAgent: ${result.text}`);
        console.log(
            `[${elapsed.toFixed(2)}s | ` +
                `tokens: ${result.usage?.inputTokens ?? '?'} in / ` +
                `${result.usage?.outputTokens ?? '?'} out]`,
        );
        console.log('='.repeat(60));
    }
}

main().catch(console.error);

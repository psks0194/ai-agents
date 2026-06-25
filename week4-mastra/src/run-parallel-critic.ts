import 'dotenv/config';
import { mastra } from './mastra';

async function main() {
    const workflow = mastra.getWorkflow('parallelCriticWorkflow');
    const run = await workflow.createRun();

    const topic = 'why most agent demos fail in production';
    console.log(`\nTopic: ${topic}\n`);

    const result = await run.start({ inputData: { topic } });

    if (result.status === 'success') {
        console.log('\n=== Result ===');
        console.log(`Verdict: ${result.result.verdict}`);
        console.log(`Voice score: ${result.result.voiceScore}/10`);
        console.log(`Accuracy score: ${result.result.accuracyScore}/10`);
    }
}

main().catch(console.error);

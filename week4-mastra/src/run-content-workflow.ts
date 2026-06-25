import 'dotenv/config';
import { mastra } from './mastra';

async function main() {
    const workflow = mastra.getWorkflow('contentWorkflow');
    const run = await workflow.createRun();

    const topic = 'the gap between using agent frameworks and building the patterns inside them';

    console.log(`\nTopic: ${topic}\n`);

    const result = await run.start({ inputData: { topic } });

    if (result.status === 'success') {
        console.log('\n=== Final critique ===');
        console.log(`Verdict: ${result.result.verdict}`);
        console.log('Reasons:');
        result.result.reasons.forEach((r: string) => console.log(`  • ${r}`));
    } else {
        console.log('Workflow did not complete:', result.status);
    }
}

main().catch(console.error);

import { MDocument } from '@mastra/rag';
import { LibSQLVector } from '@mastra/libsql';
import { embedMany, embed } from 'ai';
import { openai } from '@ai-sdk/openai';

const embedder = openai.embedding('text-embedding-3-small');
const INDEX_NAME = 'curriculum_notes';

// Some sample "notes" to index — pretend these are your curriculum notes
const SAMPLE_NOTES = `
# Week 1: The agent loop
The agent loop is: send messages, check the stop reason, if there's a tool
call then execute it and send the result back, otherwise you're done. It's
about 80 lines of code. Every agent framework wraps this same loop.

# Week 2: The five patterns
The five canonical agent patterns are prompt chaining, routing, parallelization,
orchestrator-workers, and evaluator-optimizer. Three are workflows where your
code controls flow. Two shade toward agentic where the LLM controls flow.

# Week 2: Memory and cost
Naive conversation accumulation grows token cost quadratically. Summarization
keeps recent turns and compresses old ones. Scratchpad memory holds structured
notes the agent maintains across steps. RAG handles knowledge-level memory.

# Week 3: Framework choice
The framework choice is about workflow shape, not agent capabilities. Pydantic
AI for single typed agents. LangGraph for stateful workflows with branches,
cycles, persistence, human-in-the-loop. They're complementary, not competing.
`;

async function buildIndex(): Promise<LibSQLVector> {
    console.log('Chunking document...');
    const doc = MDocument.fromMarkdown(SAMPLE_NOTES);
    const chunks = await doc.chunk({
        strategy: 'recursive',
        maxSize: 256,
        overlap: 30,
    });
    console.log(`  ${chunks.length} chunks created`);

    console.log('Embedding chunks...');
    const { embeddings } = await embedMany({
        model: embedder,
        values: chunks.map((c) => c.text),
    });
    console.log(`  ${embeddings.length} embeddings created`);

    // LibSQL vector store — file-based, no external service
    const store = new LibSQLVector({
        id: 'rag-demo-vector',
        url: 'file:./rag-demo.db',
    });

    // Create the index (dimension 1536 for text-embedding-3-small)
    await store.createIndex({ indexName: INDEX_NAME, dimension: 1536 });

    // Store the vectors with their text as metadata
    await store.upsert({
        indexName: INDEX_NAME,
        vectors: embeddings,
        metadata: chunks.map((c) => ({ text: c.text })),
    });

    console.log('  Index built.\n');
    return store;
}

async function query(store: LibSQLVector, question: string): Promise<void> {
    console.log(`Q: ${question}`);

    // Embed the question
    const { embedding } = await embed({ model: embedder, value: question });

    // Retrieve top 2 most similar chunks
    const results = await store.query({
        indexName: INDEX_NAME,
        queryVector: embedding,
        topK: 2,
    });

    console.log('Retrieved chunks:');
    results.forEach((r, i) => {
        console.log(
            `  ${i + 1}. (score=${r.score.toFixed(3)}) ${r.metadata?.text?.slice(0, 100)}...`,
        );
    });
    console.log();
}

async function main() {
    const store = await buildIndex();

    await query(store, 'How does the agent loop work?');
    await query(store, 'What are the five patterns?');
    await query(store, 'Which framework for stateful workflows?');
    await query(store, 'How do I stop token costs from exploding?');
}

main().catch(console.error);

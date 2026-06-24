import { createTool } from '@mastra/core/tools';
import { z } from 'zod';

// ============================================================
// Calculator tool
// ============================================================

export const calculatorTool = createTool({
    id: 'calculator',
    description:
        'Evaluate a basic mathematical expression. Supports +, -, *, /, **, ' +
        'and parentheses. Use whenever you need to compute a numeric result.',
    inputSchema: z.object({
        expression: z.string().describe("A math expression like '47 * 83 + 199' or '(5 + 3) ** 2'"),
    }),
    outputSchema: z.object({
        result: z.string(),
    }),
    execute: async ({ expression }) => {
        try {
            // Restricted eval — Function constructor with no access to scope.
            // Still not safe for untrusted input in production; use a parser there.
            const result = Function(`"use strict"; return (${expression})`)();
            console.log(`  → calculator(${expression}) = ${result}`);
            return { result: String(result) };
        } catch (e) {
            return { result: `Error: ${(e as Error).message}` };
        }
    },
});

// ============================================================
// Current time tool
// ============================================================

export const currentTimeTool = createTool({
    id: 'get-current-time',
    description:
        'Get the current date and time in a specified IANA timezone. Use when ' +
        'the user asks about the current time or anything time-sensitive.',
    inputSchema: z.object({
        timezone: z
            .string()
            .describe("IANA timezone, e.g. 'Asia/Kolkata', 'America/New_York', 'UTC'"),
    }),
    outputSchema: z.object({
        datetime: z.string(),
    }),
    execute: async ({ timezone }) => {
        try {
            const now = new Date().toLocaleString('en-US', { timeZone: timezone });
            console.log(`  → get_current_time(${timezone}) = ${now}`);
            return { datetime: now };
        } catch (e) {
            return { datetime: `Error: ${(e as Error).message}` };
        }
    },
});

// ============================================================
// Web fetch tool
// ============================================================

export const fetchUrlTool = createTool({
    id: 'fetch-url',
    description:
        'Fetch the contents of a web page. Returns the first 5000 characters. ' +
        'Use when you need current information from a specific URL.',
    inputSchema: z.object({
        url: z.string().describe('The full URL to fetch, including https://'),
    }),
    outputSchema: z.object({
        content: z.string(),
    }),
    execute: async ({ url }) => {
        console.log(`  → fetch_url(${url})`);
        try {
            const response = await fetch(url, {
                headers: { 'User-Agent': 'week4-mastra-agent/0.1' },
            });
            const text = (await response.text()).slice(0, 5000);
            console.log(`  ← ${text.length} chars`);
            return {
                content: `URL: ${url}\nStatus: ${response.status}\n\n${text}`,
            };
        } catch (e) {
            return { content: `Error fetching ${url}: ${(e as Error).message}` };
        }
    },
});

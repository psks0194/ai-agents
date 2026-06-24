import { Agent } from "@mastra/core/agent";
import {
  calculatorTool,
  currentTimeTool,
  fetchUrlTool,
} from "../tools/utility-tool";

export const toolAgent = new Agent({
  id: "tool-agent",
  name: "Tool Using Assistant",
  instructions:
    "You are a helpful assistant with access to tools. When a question " +
    "requires computation or external information, use the appropriate tool. " +
    "After receiving results, give a clear, concise final answer.",
  model: "anthropic/claude-haiku-4-5",
  tools: {
    calculatorTool,
    currentTimeTool,
    fetchUrlTool,
  },
});
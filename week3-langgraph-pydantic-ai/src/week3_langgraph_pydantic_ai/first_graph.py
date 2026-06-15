"""The smallest possible LangGraph — three nodes, linear flow.

This isn't an agent. It's a state machine that:
  1. Reads input from state
  2. Transforms it in node A
  3. Transforms it more in node B
  4. Returns final state

The point: see what state, nodes, edges, and execution look like
before we add LLMs.
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# Step 1: Define the state schema.
# Every node reads from this and writes to this.
class State(TypedDict):
    text: str
    count: int


# Step 2: Define nodes.
# Each node is a function: (state) -> dict of partial updates
def add_greeting(state: State) -> dict:
    """Prepend a greeting to the text."""
    return {"text": f"Hello, {state['text']}"}


def count_words(state: State) -> dict:
    """Count words in the current text."""
    return {"count": len(state["text"].split())}


# Step 3: Wire the graph.
graph_builder = StateGraph(State)

graph_builder.add_node("greeting", add_greeting)
graph_builder.add_node("counter", count_words)

# Edges define the flow:
# START → greeting → counter → END
graph_builder.add_edge(START, "greeting")
graph_builder.add_edge("greeting", "counter")
graph_builder.add_edge("counter", END)

# Step 4: Compile the graph.
graph = graph_builder.compile()


def main() -> None:
    # Step 5: Execute. Initial state is whatever you pass in.
    initial = {"text": "world", "count": 0}

    print("Initial:", initial)

    result = graph.invoke(initial)

    print("Final:  ", result)


if __name__ == "__main__":
    main()

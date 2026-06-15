"""The RAG agent: ask questions about your own curriculum notes.

Pattern: query → retrieve top-K chunks → construct prompt → generate answer.
This is the substrate of every 'chat with your docs' product.
"""

import argparse

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from week2_agent_patterns.llm import call_text_anthropic
from week2_agent_patterns.rag_retrieve import retrieve, RetrievedChunk


console = Console()


RAG_SYSTEM = (
    "You are a personal study assistant. The user is going through the IntellAIgent "
    "Agent Builder Curriculum and you have access to their actual notes from each "
    "day of learning. \n\n"
    "When you answer:\n"
    " - Ground your answer in the provided context chunks\n"
    " - Cite which day or note the context came from (e.g., 'in your Week 1 Day 2 notes...')\n"
    " - If the context doesn't contain enough information to answer confidently, "
    "say so explicitly rather than guessing or relying on general knowledge\n"
    " - Be specific and concrete — quote brief snippets when relevant\n"
    " - Keep answers focused. ≤300 words unless the question genuinely needs more."
)


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks as context for the LLM."""
    if not chunks:
        return "(no relevant context found in your notes)"

    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(
            f"--- Chunk {i} (from {c.source} → {c.heading}, distance={c.distance:.3f}) ---\n"
            f"{c.text}"
        )
    return "\n\n".join(parts)


def answer_with_rag(
    question: str,
    n_results: int = 4,
    show_retrieval: bool = True,
) -> str:
    """Full RAG pipeline: retrieve context, then generate an answer."""
    console.print(f"\n[bold]Question:[/bold] {question}\n")

    console.print(f"[dim]Retrieving top {n_results} chunks...[/dim]")
    chunks = retrieve(question, n_results=n_results)

    if show_retrieval:
        for i, c in enumerate(chunks, start=1):
            snippet = c.text[:200] + ("..." if len(c.text) > 200 else "")
            console.print(
                Panel(
                    snippet,
                    title=f"#{i} | {c.source} → {c.heading} | distance={c.distance:.3f}",
                    border_style="cyan",
                )
            )

    # Construct the prompt
    context = format_context(chunks)
    prompt = (
        f"Context retrieved from the user's curriculum notes:\n\n{context}\n\n"
        f"User's question: {question}\n\n"
        "Answer using ONLY the context above. If insufficient, say so."
    )

    console.print("\n[dim]Generating answer...[/dim]")
    answer = call_text_anthropic(
        prompt=prompt,
        system=RAG_SYSTEM,
        max_tokens=1024,
    )

    console.print(Panel(Markdown(answer), title="Answer", border_style="green"))
    return answer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask a question about your IntellAIgent curriculum notes."
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="What did I learn about async Python in Week 0?",
        help="The question to ask.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=4,
        help="Number of chunks to retrieve (default 4).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Don't show retrieved chunks, just the answer.",
    )
    args = parser.parse_args()

    answer_with_rag(args.question, n_results=args.n, show_retrieval=not args.quiet)


if __name__ == "__main__":
    main()

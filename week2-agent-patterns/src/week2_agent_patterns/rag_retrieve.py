"""Retrieval layer: query the ChromaDB index for relevant chunks."""

from dataclasses import dataclass

import chromadb
from chromadb.config import Settings as ChromaSettings
from rich.console import Console
from rich.panel import Panel

from week2_agent_patterns.rag_index import CHROMA_DIR, COLLECTION_NAME


console = Console()


@dataclass
class RetrievedChunk:
    """One chunk retrieved from the vector DB."""

    text: str
    source: str
    heading: str
    distance: float  # smaller = more similar


def get_collection():
    """Get a handle to the curriculum notes collection."""
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return client.get_collection(name=COLLECTION_NAME)


def retrieve(query: str, n_results: int = 4) -> list[RetrievedChunk]:
    """Retrieve the top N most relevant chunks for a query."""
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=n_results)

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            RetrievedChunk(
                text=doc,
                source=meta.get("source", "unknown"),
                heading=meta.get("heading", "unknown"),
                distance=dist,
            )
        )
    return chunks


def main() -> None:
    """Demo: show what gets retrieved for a few sample queries."""
    queries = [
        "What did I learn about async Python?",
        "How does the agent loop work?",
        "What are the canonical agent patterns?",
        "How do I handle conversation memory?",
    ]

    for q in queries:
        console.print(f"\n[bold]Query:[/bold] {q}")
        chunks = retrieve(q, n_results=3)
        for i, c in enumerate(chunks, start=1):
            console.print(
                Panel(
                    c.text[:400] + ("..." if len(c.text) > 400 else ""),
                    title=f"#{i} | {c.source} → {c.heading} | distance={c.distance:.3f}",
                    border_style="cyan",
                )
            )


if __name__ == "__main__":
    main()

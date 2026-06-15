"""Index curriculum notes into ChromaDB.

Reads notes.md files from across the ai-agents/ umbrella repo, chunks them,
embeds them, stores in a local ChromaDB collection.

Run once to (re)build the index. The index persists on disk.
"""

from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from rich.console import Console


console = Console()


# Where ChromaDB stores its data on disk
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CHROMA_DIR = REPO_ROOT / ".chroma"
COLLECTION_NAME = "curriculum_notes"


def find_notes_files(root: Path) -> list[Path]:
    """Find all notes.md files in the umbrella repo."""
    return sorted(root.rglob("notes.md"))


def chunk_markdown(text: str, source: str) -> list[dict]:
    """Split a markdown file into chunks at heading boundaries.

    Returns a list of {id, text, metadata} dicts.
    """
    lines = text.split("\n")
    chunks = []
    current_chunk_lines: list[str] = []
    current_heading = "intro"

    def flush() -> None:
        if not current_chunk_lines:
            return
        body = "\n".join(current_chunk_lines).strip()
        if len(body) < 30:
            return  # skip tiny chunks (less than ~30 chars rarely have meaning)
        chunks.append(
            {
                "id": f"{source}#{current_heading}#{len(chunks)}",
                "text": body,
                "metadata": {
                    "source": source,
                    "heading": current_heading,
                },
            }
        )

    for line in lines:
        if line.startswith("#"):
            # Save the previous chunk before starting a new heading
            flush()
            current_heading = line.lstrip("#").strip()[:80]
            current_chunk_lines = [line]
        else:
            current_chunk_lines.append(line)

    flush()  # last chunk
    return chunks


def build_index() -> None:
    """Build (or rebuild) the curriculum notes index in ChromaDB."""
    console.print(f"[dim]Searching for notes.md files under {REPO_ROOT}...[/dim]")
    notes_files = find_notes_files(REPO_ROOT)
    console.print(f"Found {len(notes_files)} notes files:")
    for nf in notes_files:
        console.print(f"  • {nf.relative_to(REPO_ROOT)}")

    if not notes_files:
        console.print(
            "\n[red]No notes.md files found! Make sure you've been writing "
            "Day reflections in notes.md files inside each week's project.[/red]"
        )
        return

    # Collect all chunks
    all_chunks = []
    for nf in notes_files:
        text = nf.read_text(encoding="utf-8")
        source = str(nf.relative_to(REPO_ROOT))
        chunks = chunk_markdown(text, source)
        all_chunks.extend(chunks)
        console.print(f"  • {source}: {len(chunks)} chunks")

    console.print(f"\n[bold]Total chunks to index:[/bold] {len(all_chunks)}")

    # Create ChromaDB client (persistent, on disk)
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # Recreate the collection from scratch each time we index
    try:
        client.delete_collection(COLLECTION_NAME)
    except (ValueError, Exception):
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "IntellAIgent curriculum notes"},
    )

    # Add chunks in batches (ChromaDB handles embedding automatically)
    BATCH = 100
    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i : i + BATCH]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        console.print(
            f"  [dim]Indexed {min(i + BATCH, len(all_chunks))}/{len(all_chunks)}...[/dim]"
        )

    # Verify
    count = collection.count()
    console.print(f"\n[green]Index built. {count} chunks indexed.[/green]")
    console.print(f"[dim]Storage: {CHROMA_DIR}[/dim]")


def main() -> None:
    build_index()


if __name__ == "__main__":
    main()

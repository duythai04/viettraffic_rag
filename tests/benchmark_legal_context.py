import json
from pathlib import Path
from collections import Counter

from src.context.legal_chunk_index import LegalChunkIndex
from src.context.legal_context_reconstructor import (
    LegalContextReconstructor,
)


CHUNKS_PATH = Path(
    "data/processed/chunks/legal_chunks.json"
)


def main():

    chunks = json.loads(
        CHUNKS_PATH.read_text(
            encoding="utf-8"
        )
    )

    index = LegalChunkIndex(chunks)

    reconstructor = LegalContextReconstructor(
        index
    )

    stats = Counter()

    suspicious_examples = []

    for chunk in chunks:

        result = reconstructor.reconstruct(
            chunk["chunk_id"]
        )

        stats["total"] += 1

        if result["parent_found"]:
            stats["parent_found"] += 1

        if result["clause_preamble"]:
            stats["has_clause_preamble"] += 1

        if result["fine"] is not None:
            stats["fine_extracted"] += 1
        elif result["clause_preamble"]:
            stats["preamble_without_fine"] += 1

            if len(suspicious_examples) < 10:
                suspicious_examples.append({
                    "chunk_id": result["chunk_id"],
                    "preamble": result["clause_preamble"],
                })

    total = stats["total"]

    print("\n" + "=" * 60)
    print("LEGAL CONTEXT BENCHMARK")
    print("=" * 60)

    for key, value in stats.items():
        percentage = (
            value / total * 100
            if total else 0
        )

        print(
            f"{key:25}: "
            f"{value:5} ({percentage:.2f}%)"
        )

    print("\nExamples requiring inspection:")

    for example in suspicious_examples:
        print("\n", example["chunk_id"])
        print(example["preamble"])


if __name__ == "__main__":
    main()
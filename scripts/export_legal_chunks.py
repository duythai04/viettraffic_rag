import json
from pathlib import Path

from qdrant_client import QdrantClient


COLLECTION = "viettraffic_legal"

OUTPUT = Path(
    "data/processed/chunks/legal_chunks.json"
)


def main():
    client = QdrantClient(
        url="http://localhost:6333"
    )

    chunks = []
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = dict(point.payload or {})

            if not payload.get("chunk_id"):
                raise ValueError(
                    f"Missing chunk_id: {point.id}"
                )

            if not payload.get("content"):
                raise ValueError(
                    f"Missing content: {point.id}"
                )

            chunks.append({
                **payload,
                "text": payload["content"],
            })

        if offset is None:
            break

    chunks.sort(
        key=lambda x: x["chunk_id"]
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            chunks,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Exported: {len(chunks)} chunks")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
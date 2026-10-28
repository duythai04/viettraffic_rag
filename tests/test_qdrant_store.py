import json
from pathlib import Path

import numpy as np

from src.vectordb.qdrant_store import QdrantStore


def main():
    print("=" * 60)
    print("QDRANT STORE TEST")
    print("=" * 60)

    cache_dir = Path("data/processed/embeddings")

    # Chỉ dùng khi thư mục cache chứa đúng một bộ dữ liệu.
    vector_files = sorted(cache_dir.glob("*.npy"))

    if len(vector_files) != 1:
        raise RuntimeError(
            "Expected exactly one embedding cache. "
            f"Found {len(vector_files)}. "
            "Select the intended cache explicitly."
        )

    vector_path = vector_files[0]
    metadata_path = vector_path.with_suffix(".json")

    if not metadata_path.exists():
        raise FileNotFoundError(metadata_path)

    vectors = np.load(vector_path, allow_pickle=False)

    with metadata_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    print("Vectors:", vectors.shape)
    print("Metadata:", len(metadata))

    assert vectors.shape == (1036, 1024)
    assert len(metadata) == 1036

    store = QdrantStore(
        collection_name="viettraffic_legal",
        vector_size=vectors.shape[1],
    )

    store.create_collection()

    store.upsert(
        vectors=vectors,
        metadata=metadata,
        batch_size=64,
    )

    collection = store.client.get_collection(
        "viettraffic_legal"
    )

    print("Stored points:", collection.points_count)

    assert collection.points_count == 1036

    print("=" * 60)
    print("QDRANT STORE TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
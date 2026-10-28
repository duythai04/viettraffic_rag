import json
from pathlib import Path

from src.embeddings.embedder import LegalEmbedder
from src.lexical.bm25_index import BM25Index
from src.preprocessing.vehicle_metadata import VehicleMetadataEnricher
from src.query.vehicle_detector import VehicleDetector
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.vector_retriever import VectorRetriever
from src.retrieval.vehicle_aware_retriever import VehicleAwareRetriever
from src.vectordb.qdrant_store import QdrantStore


METADATA_PATH = Path(
    "data/processed/embeddings/dbc075dd322c83ac.json"
)

EXPECTED_CHUNK_ID = "168-2024-ND-CP_dieu-7_khoan-7_diem-c"


def load_chunks() -> list[dict]:
    """
    Load cached chunks and enrich vehicle metadata.
    """
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_PATH}"
        )

    with METADATA_PATH.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    if not isinstance(chunks, list):
        raise ValueError("Metadata JSON must contain a list of chunks")

    print("=" * 70)
    print("LOADING LEGAL CHUNKS")
    print("=" * 70)

    print(f"Loaded chunks: {len(chunks)}")

    chunks = VehicleMetadataEnricher().enrich(chunks)

    print("Vehicle metadata enrichment completed")

    return chunks


def build_vehicle_metadata(chunks: list[dict]) -> dict:
    """
    Build chunk_id -> vehicle_type mapping.
    """
    vehicle_metadata = {
        chunk["chunk_id"]: chunk.get("vehicle_type")
        for chunk in chunks
    }

    print(f"Vehicle metadata entries: {len(vehicle_metadata)}")

    assert len(vehicle_metadata) == len(chunks), (
        "Duplicate chunk IDs detected"
    )

    assert EXPECTED_CHUNK_ID in vehicle_metadata, (
        f"Expected chunk not found: {EXPECTED_CHUNK_ID}"
    )

    assert vehicle_metadata[EXPECTED_CHUNK_ID] == "motorcycle", (
        "Incorrect vehicle type for motorcycle traffic-light chunk"
    )

    print("Target vehicle:", vehicle_metadata[EXPECTED_CHUNK_ID])
    print("Vehicle metadata validation: PASSED")

    return vehicle_metadata


def test_vehicle_detector():
    """
    Verify vehicle detection for common traffic queries.
    """
    print("\n" + "=" * 70)
    print("VEHICLE DETECTOR TEST")
    print("=" * 70)

    detector = VehicleDetector()

    test_cases = [
        ("Xe máy vượt đèn đỏ", "motorcycle"),
        ("Ô tô vượt tốc độ", "car"),
        ("Xe máy chuyên dùng", "specialized_vehicle"),
        ("Xe đạp vượt đèn đỏ", "bicycle"),
        ("Người đi bộ vượt đèn đỏ", "pedestrian"),
    ]

    for query, expected in test_cases:
        actual = detector.detect(query)

        print(f"Query: {query}")
        print(f"Expected: {expected}")
        print(f"Actual: {actual}")
        print("-" * 50)

        assert actual == expected, (
            f"Vehicle detection failed: {query}. "
            f"Expected {expected}, got {actual}"
        )

    print("Vehicle detector test: PASSED")


def build_retriever(
    chunks: list[dict],
    vehicle_metadata: dict,
) -> VehicleAwareRetriever:
    """
    Initialize BM25, BGE-M3, Qdrant and VehicleAwareRetriever.
    """
    print("\n" + "=" * 70)
    print("BUILDING RETRIEVAL PIPELINE")
    print("=" * 70)

    print("Building BM25 index...")

    bm25 = BM25Index(chunks)

    print("BM25 index ready")

    print("Loading BGE-M3 embedding model...")

    embedder = LegalEmbedder(
        model_name="BAAI/bge-m3",
        batch_size=8,
    )

    print("BGE-M3 loaded")
    print(f"Embedding dimension: {embedder.dimension}")

    print("Connecting to Qdrant...")

    store = QdrantStore(
        collection_name="viettraffic_legal",
        vector_size=embedder.dimension,
    )

    vector_retriever = VectorRetriever(
        embedder=embedder,
        store=store,
    )

    hybrid = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_index=bm25,
    )

    # IMPORTANT:
    # Pass verified vehicle metadata to the retriever.
    retriever = VehicleAwareRetriever(
        hybrid_retriever=hybrid,
        vehicle_metadata=vehicle_metadata,
        vehicle_boost=0.005,
        mismatch_penalty=0.005,
    )

    assert retriever.vehicle_metadata[EXPECTED_CHUNK_ID] == "motorcycle"

    print("VehicleAwareRetriever initialized successfully")
    print("Retriever metadata validation: PASSED")

    return retriever


def run_retrieval_tests(retriever: VehicleAwareRetriever):
    """
    Test vehicle-aware hybrid retrieval.
    """
    questions = [
        {
            "query": "Đi xe máy vượt đèn đỏ bị phạt bao nhiêu tiền?",
            "expected_chunk_id": EXPECTED_CHUNK_ID,
        },
        {
            "query": "Không đội mũ bảo hiểm bị xử phạt thế nào?",
            "expected_chunk_id": None,
        },
        {
            "query": "Điều khiển ô tô vượt quá tốc độ bị phạt bao nhiêu?",
            "expected_chunk_id": None,
        },
    ]

    print("\n" + "=" * 70)
    print("VEHICLE-AWARE RETRIEVAL TEST")
    print("=" * 70)

    for test_case in questions:
        question = test_case["query"]
        expected_chunk_id = test_case["expected_chunk_id"]

        print("\n" + "=" * 70)
        print(f"QUESTION: {question}")
        print("=" * 70)

        results = retriever.retrieve(
            query=question,
            top_k=10,
            candidate_k=30,
        )

        if not results:
            print("No retrieval results found")
            continue

        for rank, result in enumerate(results, start=1):
            print(f"\nRank: {rank}")
            print(f"Chunk ID: {result['chunk_id']}")
            print(f"Vehicle: {result.get('vehicle_type')}")
            print(
                f"Adjusted Score: "
                f"{result.get('adjusted_score', 0.0):.5f}"
            )
            print(
                f"Original RRF Score: "
                f"{result.get('rrf_score', 0.0):.5f}"
            )
            print(f"Citation: {result.get('citation')}")

            content = result.get("content") or ""
            print(f"Content: {content[:250]}")

            print("-" * 70)

        if expected_chunk_id is not None:
            ranks = [
                rank
                for rank, result in enumerate(results, start=1)
                if result["chunk_id"] == expected_chunk_id
            ]

            expected_rank = ranks[0] if ranks else None

            print("\nEXPECTED CHUNK EVALUATION")
            print(f"Expected chunk: {expected_chunk_id}")
            print(
                f"Expected rank: "
                f"{expected_rank if expected_rank else 'NOT IN TOP 10'}"
            )

            if expected_rank == 1:
                print("RESULT: PASSED - Expected chunk ranked #1")

            elif expected_rank is not None:
                print(
                    "RESULT: PARTIAL - "
                    "Expected chunk retrieved but not ranked #1"
                )

            else:
                print(
                    "RESULT: FAILED - "
                    "Expected chunk not found in Top 10"
                )


def main():
    print("\n" + "=" * 70)
    print("VIETTRAFFIC RAG - VEHICLE-AWARE RETRIEVAL")
    print("=" * 70)

    # Step 1: Load and enrich chunks.
    chunks = load_chunks()

    # Step 2: Build and validate vehicle metadata.
    vehicle_metadata = build_vehicle_metadata(chunks)

    # Step 3: Test vehicle detection.
    test_vehicle_detector()

    # Step 4: Initialize retrieval pipeline.
    retriever = build_retriever(
        chunks=chunks,
        vehicle_metadata=vehicle_metadata,
    )

    # Step 5: Run retrieval tests.
    run_retrieval_tests(retriever)

    print("\n" + "=" * 70)
    print("RETRIEVAL TEST EXECUTION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.context.legal_chunk_index import LegalChunkIndex
from src.context.legal_context_reconstructor import LegalContextReconstructor
from src.evidence.legal_evidence_selector import LegalEvidenceSelector
from src.embeddings.embedder import LegalEmbedder
from src.lexical.bm25_index import BM25Index
from src.pipelines.query_pipeline import QueryPipeline
from src.preprocessing.vehicle_metadata import VehicleMetadataEnricher
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.vector_retriever import VectorRetriever
from src.retrieval.vehicle_aware_retriever import VehicleAwareRetriever
from src.vectordb.qdrant_store import QdrantStore


BASE_DIR = Path(__file__).resolve().parents[1]

CHUNKS_PATH = (
    BASE_DIR / "data/processed/chunks/legal_chunks.json"
)

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "viettraffic_legal"
EMBEDDING_MODEL = "BAAI/bge-m3"

TOP_K = 5
MAX_EVIDENCE = 3


def load_chunks(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file chunks: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        data = data.get("chunks", [])

    if not isinstance(data, list) or not data:
        raise ValueError(
            "File legal_chunks.json phải chứa danh sách chunks."
        )

    chunks = [
        chunk
        for chunk in data
        if isinstance(chunk, dict)
        and chunk.get("chunk_id")
    ]

    if not chunks:
        raise ValueError("Không tìm thấy chunk hợp lệ.")

    chunk_ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("Phát hiện chunk_id trùng lặp.")

    return chunks


def load_vehicle_metadata(
    chunks: list[dict],
) -> dict[str, str | None]:
    enricher = VehicleMetadataEnricher()

    enriched_chunks = enricher.enrich(chunks)

    return {
        chunk["chunk_id"]: chunk.get("vehicle_type")
        for chunk in enriched_chunks
    }


def print_vehicle_statistics(
    vehicle_metadata: dict[str, str | None],
) -> None:
    counts = Counter(vehicle_metadata.values())

    print("\nVehicle metadata distribution:")

    for vehicle, count in sorted(
        counts.items(),
        key=lambda item: str(item[0]),
    ):
        label = vehicle if vehicle is not None else "unknown"
        print(f"  {label}: {count}")

    total = sum(counts.values())
    classified = total - counts.get(None, 0)

    print(f"\nTotal chunks: {total}")
    print(f"Classified chunks: {classified}")
    print(f"Unclassified chunks: {counts.get(None, 0)}")


def build_pipeline():
    print("\n[1/9] Loading legal chunks...")

    chunks = load_chunks(CHUNKS_PATH)

    print(f"Loaded {len(chunks)} chunks")

    print("\n[2/9] Building Legal Chunk Index...")

    chunk_index = LegalChunkIndex(chunks)

    context_reconstructor = LegalContextReconstructor(
        chunk_index=chunk_index,
    )

    print(f"Indexed {len(chunk_index.chunks)} legal chunks")

    print("\n[3/9] Initializing BGE-M3...")

    embedder = LegalEmbedder(
        model_name=EMBEDDING_MODEL,
        batch_size=16,
    )

    print(f"Embedding dimension: {embedder.dimension}")

    print("\n[4/9] Connecting Qdrant...")

    store = QdrantStore(
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    if not store.client.collection_exists(
        store.collection_name
    ):
        raise RuntimeError(
            f"Qdrant collection '{COLLECTION_NAME}' không tồn tại."
        )

    info = store.client.get_collection(
        store.collection_name
    )

    print(f"Qdrant points: {info.points_count}")

    if info.points_count != len(chunks):
        print(
            "WARNING: Số lượng Qdrant points "
            "khác số lượng legal chunks."
        )

    print("\n[5/9] Initializing VectorRetriever...")

    vector_retriever = VectorRetriever(
        embedder=embedder,
        store=store,
    )

    print("\n[6/9] Building BM25 Index...")

    bm25_index = BM25Index(chunks)

    print("\n[7/9] Building Hybrid + Vehicle-aware...")

    hybrid_retriever = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_index=bm25_index,
    )

    vehicle_metadata = load_vehicle_metadata(chunks)

    print_vehicle_statistics(vehicle_metadata)

    vehicle_retriever = VehicleAwareRetriever(
        hybrid_retriever=hybrid_retriever,
        vehicle_metadata=vehicle_metadata,
        vehicle_boost=0.005,
        mismatch_penalty=0.005,
    )

    print("\n[8/9] Building Legal Evidence Selector...")

    evidence_selector = LegalEvidenceSelector(
        max_evidence=MAX_EVIDENCE,
        min_score=0.0,
    )

    print(f"Maximum selected evidence: {MAX_EVIDENCE}")

    print("\n[9/9] Building Query Pipeline...")

    pipeline = QueryPipeline(
        retriever=vehicle_retriever,
        context_reconstructor=context_reconstructor,
        evidence_selector=evidence_selector,
    )

    print("\nVietTraffic RAG initialized successfully!")

    return pipeline


def print_rag_answer(result: dict) -> None:
    print("\n========== RAG ANSWER ==========")

    print(result.get("answer", ""))

    print("\nIntent:", result.get("intent"))
    print("Verified:", result.get("verified"))

    print(
        "Retrieved chunks:",
        result.get("retrieved_chunks", 0),
    )

    print(
        "Selected evidence:",
        result.get("selected_evidence_count", 0),
    )

    print("\nCitations:")

    citations = result.get("citations", [])

    if not citations:
        print("Không có citations.")
    else:
        for citation in citations:
            print("-", citation)


def print_retrieval_debug(
    results: list[dict],
) -> None:
    print("\n========== RETRIEVAL DEBUG ==========")

    if not results:
        print("Không tìm thấy kết quả Retrieval.")
        return

    for index, item in enumerate(results, start=1):
        metadata = item.get("metadata") or {}

        print(f"\n[{index}] {item.get('chunk_id')}")

        print("Citation:", item.get("citation"))
        print("Article:", metadata.get("article"))
        print("Clause:", metadata.get("clause"))
        print("Point:", metadata.get("point"))
        print("Vehicle:", item.get("vehicle_type"))
        print("RRF Score:", item.get("rrf_score"))
        print("Adjusted Score:", item.get("adjusted_score"))

        content = item.get("content") or ""

        print("\nContent:")
        print(content[:400])


def print_legal_context_debug(
    contexts: list[dict],
) -> None:
    print("\n========== LEGAL CONTEXT DEBUG ==========")

    if not contexts:
        print("Không có Legal Context.")
        return

    for index, context in enumerate(contexts, start=1):
        print(f"\n[{index}] {context.get('citation')}")

        print("Chunk ID:", context.get("chunk_id"))
        print("Clause ID:", context.get("clause_id"))
        print("Article:", context.get("article"))
        print("Clause:", context.get("clause"))
        print("Point:", context.get("point"))
        print("Vehicle:", context.get("vehicle_type"))

        print("\nViolation:")
        print(
            context.get("violation")
            or "Không có dữ liệu."
        )

        print("\nClause preamble:")
        print(
            context.get("clause_preamble")
            or "Không có dữ liệu."
        )

        print("\nParent found:", context.get("parent_found"))
        print("Fine source:", context.get("fine_source"))

        fine = context.get("fine")

        if fine:
            print("\nOCR Fine (UNVERIFIED):")

            print(
                json.dumps(
                    fine,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print("\nOCR Fine: Not extracted")

        print(
            "\nRetrieval Score:",
            context.get("retrieval_score"),
        )


def print_evidence_debug(
    evidence_result: dict,
) -> None:
    print("\n========== EVIDENCE SELECTION ==========")

    if not evidence_result:
        print("Không có kết quả Evidence Selection.")
        return

    print(
        "Query Vehicle:",
        evidence_result.get("query_vehicle"),
    )

    print(
        "Query Role:",
        evidence_result.get("query_role"),
    )

    print(
        "Requires Clarification:",
        evidence_result.get("requires_clarification"),
    )

    selected = evidence_result.get(
        "selected_evidence",
        [],
    )

    print("Selected Evidence Count:", len(selected))

    if not selected:
        print("\nKhông tìm thấy evidence phù hợp.")
        return

    for index, evidence in enumerate(selected, start=1):
        print(f"\n[{index}] {evidence.get('citation')}")

        print(
            "Chunk ID:",
            evidence.get("chunk_id"),
        )

        print(
            "Clause ID:",
            evidence.get("clause_id"),
        )

        print(
            "Vehicle:",
            evidence.get("vehicle_type"),
        )

        print(
            "Role:",
            evidence.get("evidence_role"),
        )

        print(
            "Retrieval Score:",
            evidence.get("retrieval_score"),
        )

        print(
            "Evidence Score:",
            evidence.get("evidence_score"),
        )

        print(
            "Score Breakdown:",
            json.dumps(
                evidence.get("score_breakdown", {}),
                ensure_ascii=False,
                indent=2,
            ),
        )

        print("\nViolation:")
        print(
            evidence.get("violation")
            or "Không có dữ liệu."
        )

        print("\nClause preamble:")
        print(
            evidence.get("clause_preamble")
            or "Không có dữ liệu."
        )

        fine = evidence.get("fine")

        if fine:
            print("\nOCR Fine (UNVERIFIED):")
            print(
                json.dumps(
                    fine,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print("\nOCR Fine: Not extracted")


def main():
    pipeline = build_pipeline()

    while True:
        print("\n" + "=" * 60)

        try:
            question = input(
                "\nNhập câu hỏi (exit để thoát): "
            ).strip()

        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát VietTraffic RAG.")
            break

        if question.lower() in {"exit", "quit", "q"}:
            print("Đã thoát VietTraffic RAG.")
            break

        if not question:
            continue

        try:
            result = pipeline.run(
                question=question,
                top_k=TOP_K,
                debug=True,
            )

            print_rag_answer(result)

            if result.get("intent") not in {
                "legal_fine",
                "legal_general",
            }:
                continue

            retrieval_results = result.get(
                "retrieval_results",
                [],
            )

            legal_contexts = result.get(
                "legal_contexts",
                [],
            )

            evidence_result = result.get(
                "evidence_selection",
                {},
            )

            print_retrieval_debug(
                retrieval_results
            )

            print_legal_context_debug(
                legal_contexts
            )

            print_evidence_debug(
                evidence_result
            )

        except Exception as error:
            print(
                f"\nERROR: {type(error).__name__}: {error}"
            )


if __name__ == "__main__":
    main()
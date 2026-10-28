import numpy as np

from src.embeddings.embedder import LegalEmbedder
from src.schemas.chunk import LegalChunk


def main():
    print("=" * 60)
    print("LEGAL EMBEDDING TEST")
    print("=" * 60)

    embedder = LegalEmbedder(
        model_name="BAAI/bge-m3",
        batch_size=8,
    )

    print("Model:", embedder.model_name)
    print("Dimension:", embedder.dimension)

    assert embedder.dimension == 1024

    texts = [
        "Đi xe máy vượt đèn đỏ bị phạt bao nhiêu tiền?",
        "Người điều khiển xe mô tô không chấp hành hiệu lệnh của đèn tín hiệu giao thông.",
        "Quy định về trừ điểm giấy phép lái xe.",
    ]

    embeddings = embedder.embed_texts(texts)

    print("Embedding shape:", embeddings.shape)

    assert embeddings.shape == (3, 1024)
    assert np.isfinite(embeddings).all()

    norms = np.linalg.norm(embeddings, axis=1)

    print("Vector norms:", norms)

    assert np.allclose(norms, 1.0, atol=1e-5)

    query_vector = embedder.embed_query(texts[0])

    assert query_vector.shape == (1024,)

    chunk = LegalChunk(
        chunk_id="test_dieu-1_khoan-1_diem-a",
        document_id="test-document",
        article="1",
        article_title="Quy định thử nghiệm",
        clause="1",
        point="a",
        content=texts[1],
        citation="Điểm a Khoản 1 Điều 1",
        source="test.pdf",
        embedding_text=(
            "Điều 1. Quy định thử nghiệm\n"
            "Khoản 1.\n"
            f"Điểm a. {texts[1]}"
        ),
    )

    results = embedder.embed_chunks([chunk])

    assert len(results) == 1
    assert len(results[0]["vector"]) == 1024

    assert (
        results[0]["metadata"]["citation"]
        == "Điểm a Khoản 1 Điều 1"
    )

    print("Chunk embedding: PASS")
    print("Citation preservation: PASS")

    print("=" * 60)
    print("ALL EMBEDDING TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
import numpy as np

from src.pipelines.index_pipeline import LegalIndexPipeline


def main():
    print("=" * 60)
    print("LEGAL INDEX PIPELINE TEST")
    print("=" * 60)

    pipeline = LegalIndexPipeline(
        model_name="BAAI/bge-m3",
        batch_size=8,
    )

    result = pipeline.run(
        pdf_path="data/processed/ocr/168-nd-cp.ocr.pdf",
        document_id="168-2024-ND-CP",
    )

    chunks = result["chunks"]
    vectors = result["vectors"]
    metadata = result["metadata"]

    assert len(chunks) == 1036
    assert vectors.shape == (1036, 1024)
    assert len(metadata) == 1036

    assert np.isfinite(vectors).all()

    norms = np.linalg.norm(vectors, axis=1)

    assert np.allclose(norms, 1.0, atol=1e-4)

    for chunk, item in zip(chunks, metadata):
        assert chunk.chunk_id == item["chunk_id"]
        assert chunk.citation == item["citation"]

    print("Chunk count: PASS")
    print("Embedding dimension: PASS")
    print("Vector validation: PASS")
    print("Metadata mapping: PASS")
    print("Citation preservation: PASS")

    print("=" * 60)
    print("ALL INDEX PIPELINE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

from collections import Counter

from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser
from src.chunking.legal_chunker import LegalChunker


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"

REQUIRED_FIELDS = {
    "chunk_id",
    "document_id",
    "article",
    "article_title",
    "clause",
    "point",
    "content",
    "citation",
    "source",
    "clause_preamble",
    "embedding_text",
}


def main():
    print("=" * 70)
    print("LEGAL CHUNK QUALITY TEST")
    print("=" * 70)

    # 1. Đọc và xử lý tài liệu
    raw_text = PDFLoader().load_document_text(PDF_PATH)
    clean_text = LegalTextCleaner().clean(raw_text)
    articles = LegalParser().parse_articles(clean_text)

    # 2. Tạo chunks
    chunker = LegalChunker()

    chunks = chunker.chunk_document(
        articles=articles,
        document_id="168-2024-ND-CP",
        source="168-nd-cp.ocr.pdf",
    )

    print(f"\nArticles: {len(articles)}")
    print(f"Chunks: {len(chunks)}")

    # 3. Kiểm tra trường bắt buộc
    missing_fields = []

    for index, chunk in enumerate(chunks):
        missing = REQUIRED_FIELDS - chunk.keys()

        if missing:
            missing_fields.append(
                {
                    "index": index,
                    "chunk_id": chunk.get("chunk_id"),
                    "missing": sorted(missing),
                }
            )

    print("\n[1] Required fields")
    if missing_fields:
        print(f"FAIL: {len(missing_fields)} chunks thiếu trường")

        for item in missing_fields[:10]:
            print(item)
    else:
        print("PASS: Tất cả chunks có đủ trường")

    # 4. Kiểm tra chunk_id trùng lặp
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    counts = Counter(chunk_ids)

    duplicated_ids = [
        chunk_id
        for chunk_id, count in counts.items()
        if count > 1
    ]

    print("\n[2] Duplicate chunk IDs")
    if duplicated_ids:
        print(f"FAIL: Có {len(duplicated_ids)} chunk_id trùng")

        for chunk_id in duplicated_ids[:10]:
            print(chunk_id)
    else:
        print("PASS: Không có chunk_id trùng")

    # 5. Kiểm tra content và embedding_text
    empty_content = [
        chunk["chunk_id"]
        for chunk in chunks
        if not chunk.get("content", "").strip()
    ]

    empty_embeddings = [
        chunk["chunk_id"]
        for chunk in chunks
        if not chunk.get("embedding_text", "").strip()
    ]

    print("\n[3] Empty content")
    print(f"Chunks with empty content: {len(empty_content)}")

    print("\n[4] Empty embedding_text")
    print(f"Chunks with empty embedding_text: {len(empty_embeddings)}")

    # 6. Kiểm tra các điểm có đủ ngữ cảnh
    point_chunks = [
        chunk
        for chunk in chunks
        if chunk.get("point") is not None
    ]

    missing_article_context = [
        chunk["chunk_id"]
        for chunk in point_chunks
        if f"Điều {chunk['article']}." not in chunk["embedding_text"]
    ]

    missing_point_context = [
        chunk["chunk_id"]
        for chunk in point_chunks
        if f"Điểm {chunk['point']}." not in chunk["embedding_text"]
    ]

    print("\n[5] Point context")
    print(f"Point chunks: {len(point_chunks)}")
    print(
        "Missing article context:",
        len(missing_article_context),
    )
    print(
        "Missing point context:",
        len(missing_point_context),
    )

    # 7. Kiểm tra chunk mẫu
    print("\n[6] Sample chunk")

    target = next(
        (
            chunk
            for chunk in chunks
            if chunk["article"] == "2"
            and chunk["clause"] == "2"
            and chunk["point"] == "a"
        ),
        None,
    )

    if target:
        print("Citation:", target["citation"])
        print("Preamble:", target["clause_preamble"])
        print("Content:", target["content"])
        print("Embedding text:")
        print(target["embedding_text"])
    else:
        print("WARNING: Không tìm thấy chunk Điều 2, Khoản 2, Điểm a")

    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
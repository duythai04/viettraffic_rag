from __future__ import annotations

from src.context.fine_extractor import FineExtractor
from src.context.legal_chunk_index import LegalChunkIndex


class LegalContextReconstructor:

    def __init__(
        self,
        chunk_index: LegalChunkIndex,
    ):
        self.index = chunk_index
        self.fine_extractor = FineExtractor()

    def reconstruct(self, chunk_id: str) -> dict:

        chunk = self.index.get(chunk_id)

        if chunk is None:
            raise KeyError(
                f"Chunk not found: {chunk_id}"
            )

        parent = self.index.get_parent_clause(chunk)

        violation = chunk.get("text", "")

        preamble = chunk.get(
            "clause_preamble"
        ) or ""

        fine_source = None

        # Prefer the preamble stored in the
        # retrieved point itself.
        if preamble:
            fine = self.fine_extractor.extract(
                preamble
            )

            if fine:
                fine_source = (
                    f"{chunk_id}:clause_preamble"
                )
        else:
            fine = None

        # Fallback to explicit parent clause.
        if fine is None and parent is not None:
            fine = self.fine_extractor.extract(
                parent.get("text", "")
            )

            if fine:
                fine_source = parent["chunk_id"]

        citation = chunk.get("citation")

        if not citation:
            citation = self._build_citation(chunk)

        context_parts = [
            f"Căn cứ pháp lý: {citation}",
            f"Văn bản: {chunk['document_id']}",
            f"Tiêu đề điều: {chunk.get('article_title', '')}",
            f"Hành vi vi phạm: {violation}",
        ]

        if preamble:
            context_parts.append(
                f"Nội dung khoản: {preamble}"
            )

        if fine:
            context_parts.append(
                "Mức phạt trích xuất từ OCR "
                "(chưa xác minh): "
                f"{fine['min_vnd']:,} - "
                f"{fine['max_vnd']:,} đồng"
            )
        else:
            context_parts.append(
                "Mức phạt: Chưa xác định "
                "được từ dữ liệu OCR"
            )

        return {
            "chunk_id": chunk_id,
            "document_id": chunk["document_id"],
            "article": chunk["article"],
            "clause": chunk["clause"],
            "point": chunk["point"],
            "citation": citation,
            "violation": violation,
            "clause_preamble": preamble,
            "fine": fine,
            "fine_source": fine_source,
            "parent_found": parent is not None,
            "context_text": "\n".join(
                context_parts
            ),
        }

    @staticmethod
    def _build_citation(chunk: dict) -> str:
        article = chunk["article"]
        clause = chunk["clause"]
        point = chunk["point"]

        if point is not None:
            return (
                f"Điểm {point} Khoản {clause} "
                f"Điều {article}"
            )

        if clause is not None:
            return f"Khoản {clause} Điều {article}"

        return f"Điều {article}"

    def reconstruct_many(
        self,
        retrieved_chunks: list[dict],
    ) -> list[dict]:

        results = []

        for item in retrieved_chunks:
            result = self.reconstruct(
                item["chunk_id"]
            )

            result["retrieval_score"] = (
                item.get("adjusted_score")
                if item.get("adjusted_score") is not None
                else item.get("rrf_score")
            )

            results.append(result)

        return results
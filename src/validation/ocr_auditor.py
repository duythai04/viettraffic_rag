

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from src.context.legal_chunk_index import LegalChunkIndex
from src.validation.fine_validator import FineValidator


class OCRAuditor:
    """
    Audit dữ liệu OCR ở cấp khoản pháp luật.

    Không tự động sửa OCR và không xác minh mức phạt.
    """

    def __init__(self):
        self.validator = FineValidator()

    @staticmethod
    def _get_text(chunk: dict) -> str:
        return chunk.get("text") or chunk.get("content") or ""

    @staticmethod
    def _normalize_for_compare(text: str) -> str:
        return " ".join(text.split())

    def audit(self, chunks: list[dict]) -> dict[str, Any]:
        groups = defaultdict(list)
        skipped = []

        for chunk in chunks:
            chunk_id = chunk.get("chunk_id")

            if not chunk_id:
                skipped.append({
                    "chunk_id": None,
                    "reason": "missing_chunk_id",
                })
                continue

            try:
                parsed = LegalChunkIndex.parse_chunk_id(chunk_id)
            except (ValueError, TypeError, AttributeError):
                skipped.append({
                    "chunk_id": chunk_id,
                    "reason": "invalid_chunk_id",
                })
                continue

            if not parsed or parsed.get("article") is None:
                skipped.append({
                    "chunk_id": chunk_id,
                    "reason": "unrecognized_chunk_id",
                })
                continue

            if parsed.get("clause") is None:
                # Article-level chunks are outside clause-level audit.
                skipped.append({
                    "chunk_id": chunk_id,
                    "reason": "article_level_chunk",
                })
                continue

            clause_id = (
                f"{parsed['document_id']}"
                f"_dieu-{parsed['article']}"
                f"_khoan-{parsed['clause']}"
            )

            groups[clause_id].append(chunk)

        records = []

        for clause_id, members in sorted(groups.items()):
            preambles = []
            parent_texts = []

            for chunk in members:
                preamble = chunk.get("clause_preamble")

                if preamble and preamble.strip():
                    preambles.append(preamble.strip())

                if chunk.get("chunk_id") == clause_id:
                    text = self._get_text(chunk)
                    if text.strip():
                        parent_texts.append(text.strip())

            # Ưu tiên clause_preamble vì đây là phần mở đầu
            # chứa mức xử phạt của khoản.
            candidates = preambles or parent_texts

            unique_texts = {}

            for text in candidates:
                key = self._normalize_for_compare(text)
                unique_texts.setdefault(key, text)

            variants = list(unique_texts.values())

            if not variants:
                validation = self.validator.validate("")
                validation["issues"].append(
                    "missing_clause_preamble"
                )
                source_text = ""
            elif len(variants) > 1:
                # Không chọn tùy tiện giữa các phiên bản OCR
                # khác nhau của cùng một khoản.
                validation = {
                    "status": "suspicious_ocr",
                    "fine_ranges": [],
                    "issues": [
                        "conflicting_clause_preambles"
                    ],
                    "requires_manual_review": True,
                    "verified": False,
                }
                source_text = variants[0]
            else:
                source_text = variants[0]
                validation = self.validator.validate(source_text)

            records.append({
                "clause_id": clause_id,
                "chunk_count": len(members),
                "chunk_ids": [
                    c.get("chunk_id") for c in members
                ],
                "source_text": source_text,
                "variant_count": len(variants),
                "status": validation["status"],
                "fine_ranges": validation["fine_ranges"],
                "issues": validation["issues"],
                "requires_manual_review": (
                    validation["requires_manual_review"]
                ),
                "verified": False,
            })

        counts = Counter(
            record["status"] for record in records
        )

        return {
            "summary": {
                "total_chunks": len(chunks),
                "total_clauses": len(records),
                "skipped_chunks": len(skipped),
                "status_counts": dict(counts),
            },
            "records": records,
            "skipped": skipped,
        }
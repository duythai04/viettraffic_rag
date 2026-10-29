from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


class LegalChunkIndex:
    """
    Index legal chunks by document, article, clause and point.

    Supported IDs:
        168-2024-ND-CP_dieu-7_khoan-7_diem-c
        168-2024-ND-CP_dieu-7_khoan-7
        168-2024-ND-CP_dieu-7
    """

    ID_PATTERN = re.compile(
        r"^(?P<document_id>.+?)"
        r"_dieu-(?P<article>\d+)"
        r"(?:_khoan-(?P<clause>\d+))?"
        r"(?:_diem-(?P<point>[a-zA-ZđĐ]))?$"
    )

    def __init__(self, chunks: list[dict]):
        self.chunks = []
        self.by_id = {}
        self.by_clause = defaultdict(list)

        for raw_chunk in chunks:
            chunk = self._normalize_chunk(raw_chunk)

            chunk_id = chunk["chunk_id"]

            if chunk_id in self.by_id:
                raise ValueError(
                    f"Duplicate chunk_id: {chunk_id}"
                )

            self.chunks.append(chunk)
            self.by_id[chunk_id] = chunk

            key = (
                chunk["document_id"],
                chunk["article"],
                chunk["clause"],
            )

            if chunk["clause"] is not None:
                self.by_clause[key].append(chunk)

    @classmethod
    def parse_chunk_id(cls, chunk_id: str) -> dict:
        match = cls.ID_PATTERN.match(chunk_id)

        if not match:
            raise ValueError(
                f"Unsupported legal chunk ID: {chunk_id}"
            )

        data = match.groupdict()

        return {
            "document_id": data["document_id"],
            "article": int(data["article"]),
            "clause": (
                int(data["clause"])
                if data["clause"] is not None
                else None
            ),
            "point": data["point"],
        }

    @classmethod
    def _normalize_chunk(cls, raw: dict) -> dict:
        chunk = raw.copy()

        chunk_id = chunk.get("chunk_id")

        if not chunk_id:
            raise ValueError("Chunk is missing chunk_id")

        parsed = cls.parse_chunk_id(chunk_id)

        chunk.update(parsed)

        text = (
            chunk.get("text")
            or chunk.get("content")
            or ""
        )

        chunk["text"] = str(text).strip()

        return chunk

    def get(self, chunk_id: str) -> dict | None:
        return self.by_id.get(chunk_id)

    def get_clause_chunks(
        self,
        document_id: str,
        article: int,
        clause: int,
    ) -> list[dict]:
        return self.by_clause.get(
            (document_id, article, clause),
            [],
        )

    def get_parent_clause(
        self,
        chunk: dict,
    ) -> dict | None:
        """
        Find an explicit parent clause chunk.

        If no clause-level chunk exists, return None.
        """
        clause = chunk.get("clause")

        if clause is None:
            return None

        parent_id = (
            f"{chunk['document_id']}"
            f"_dieu-{chunk['article']}"
            f"_khoan-{clause}"
        )

        return self.get(parent_id)
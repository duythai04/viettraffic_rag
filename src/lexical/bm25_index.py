from __future__ import annotations

import re
import unicodedata

from rank_bm25 import BM25Okapi


class BM25Index:
    def __init__(self, chunks: list[dict]):
        if not chunks:
            raise ValueError("BM25 requires at least one chunk")

        self.chunks = chunks

        self.documents = [
            self._build_search_text(chunk)
            for chunk in chunks
        ]

        self.tokenized_corpus = [
            self.tokenize(text)
            for text in self.documents
        ]

        self.index = BM25Okapi(self.tokenized_corpus)

    @staticmethod
    def tokenize(text: str) -> list[str]:
        text = unicodedata.normalize("NFC", text.lower())

        # Basic Vietnamese tokenization.
        # A Vietnamese word segmenter can be added later.
        return re.findall(r"\w+", text, flags=re.UNICODE)

    @staticmethod
    def _build_search_text(chunk: dict) -> str:
        return " ".join(
            str(value or "")
            for value in [
                chunk.get("article_title"),
                chunk.get("content"),
                chunk.get("clause_preamble"),
                chunk.get("embedding_text"),
            ]
        )

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[dict]:
        if not query.strip():
            raise ValueError("Query must not be empty")

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        tokens = self.tokenize(query)

        scores = self.index.get_scores(tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )

        results = []

        for index in ranked_indices[:top_k]:
            score = float(scores[index])

            if score <= 0:
                continue

            chunk = self.chunks[index]

            results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "citation": chunk.get("citation"),
                    "content": chunk.get("content"),
                    "score": score,
                    "metadata": chunk,
                }
            )

        return results
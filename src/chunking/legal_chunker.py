import re

from src.schemas.chunk import LegalChunk


class LegalChunker:
    POINT_MARKER_PATTERN = re.compile(
        r"(?mi)^[ \t]*[“”\"*#]*[ \t]*"
        r"([a-zđø©¢])[\)\.][ \t]*"
    )

    def __init__(self, max_chars: int = 1800):
        if max_chars < 200:
            raise ValueError("max_chars must be at least 200")

        self.max_chars = max_chars

    def chunk_document(
        self,
        articles: list[dict],
        document_id: str,
        source: str,
    ) -> list[dict]:
        chunks = []

        for article in articles:
            article_number = str(
                article.get("article_number", "")
            ).strip()

            article_title = str(
                article.get("article_title", "")
            ).strip()

            clauses = article.get("clauses", [])

            if clauses:
                for clause in clauses:
                    chunks.extend(
                        self._chunk_clause(
                            article_number=article_number,
                            article_title=article_title,
                            clause=clause,
                            document_id=document_id,
                            source=source,
                        )
                    )
            else:
                chunk = self._create_article_chunk(
                    article=article,
                    document_id=document_id,
                    source=source,
                )

                if chunk:
                    chunks.extend(
                        self._split_chunk(chunk)
                    )

        return chunks

    def _extract_clause_preamble(
        self,
        clause_content: str,
        points: list[dict],
    ) -> str:
        if not clause_content or not points:
            return ""

        match = self.POINT_MARKER_PATTERN.search(
            clause_content
        )

        if not match:
            return clause_content.strip()

        return clause_content[:match.start()].strip()

    def _chunk_clause(
        self,
        article_number: str,
        article_title: str,
        clause: dict,
        document_id: str,
        source: str,
    ) -> list[dict]:
        clause_number = str(
            clause.get("clause_number", "")
        ).strip()

        clause_content = str(
            clause.get("content", "")
        ).strip()

        points = clause.get("points", [])

        if not points:
            chunk = self._create_clause_chunk(
                document_id=document_id,
                article_number=article_number,
                article_title=article_title,
                clause_number=clause_number,
                content=clause_content,
                source=source,
            )

            return self._split_chunk(chunk) if chunk else []

        preamble = self._extract_clause_preamble(
            clause_content,
            points,
        )

        chunks = []

        for point in points:
            chunk = self._create_point_chunk(
                document_id=document_id,
                article_number=article_number,
                article_title=article_title,
                clause_number=clause_number,
                point=point,
                clause_preamble=preamble,
                source=source,
            )

            if chunk:
                chunks.extend(
                    self._split_chunk(chunk)
                )

        return chunks

    def _create_point_chunk(
        self,
        document_id: str,
        article_number: str,
        article_title: str,
        clause_number: str,
        point: dict,
        clause_preamble: str,
        source: str,
    ) -> dict | None:
        point_letter = str(
            point.get("point", "")
        ).strip()

        content = str(
            point.get("content", "")
        ).strip()

        if not content:
            return None

        chunk_id = (
            f"{document_id}_dieu-{article_number}"
            f"_khoan-{clause_number}"
            f"_diem-{point_letter}"
        )

        citation = (
            f"Điểm {point_letter} Khoản {clause_number}"
            f" Điều {article_number}"
        )

        context = [
            f"Điều {article_number}. {article_title}",
            f"Khoản {clause_number}. {clause_preamble}"
            if clause_preamble else "",
            f"Điểm {point_letter}. {content}",
        ]

        embedding_text = "\n".join(
            item for item in context if item
        )

        return LegalChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            article=article_number,
            article_title=article_title,
            clause=clause_number,
            point=point_letter,
            content=content,
            citation=citation,
            source=source,
            clause_preamble=clause_preamble,
            embedding_text=embedding_text,
        ).to_dict()

    def _create_clause_chunk(
        self,
        document_id: str,
        article_number: str,
        article_title: str,
        clause_number: str,
        content: str,
        source: str,
    ) -> dict | None:
        if not content:
            return None

        chunk_id = (
            f"{document_id}_dieu-{article_number}"
            f"_khoan-{clause_number}"
        )

        citation = (
            f"Khoản {clause_number} Điều {article_number}"
        )

        embedding_text = (
            f"Điều {article_number}. {article_title}\n"
            f"Khoản {clause_number}. {content}"
        )

        return LegalChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            article=article_number,
            article_title=article_title,
            clause=clause_number,
            point=None,
            content=content,
            citation=citation,
            source=source,
            clause_preamble="",
            embedding_text=embedding_text,
        ).to_dict()

    def _create_article_chunk(
        self,
        article: dict,
        document_id: str,
        source: str,
    ) -> dict | None:
        article_number = str(
            article.get("article_number", "")
        ).strip()

        article_title = str(
            article.get("article_title", "")
        ).strip()

        content = str(
            article.get("content", "")
        ).strip()

        if not content:
            return None

        chunk_id = (
            f"{document_id}_dieu-{article_number}"
        )

        citation = f"Điều {article_number}"

        embedding_text = (
            f"Điều {article_number}. {article_title}\n"
            f"{content}"
        )

        return LegalChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            article=article_number,
            article_title=article_title,
            clause=None,
            point=None,
            content=content,
            citation=citation,
            source=source,
            clause_preamble="",
            embedding_text=embedding_text,
        ).to_dict()

    def _split_text(self, text: str) -> list[str]:
        text = text.strip()

        if len(text) <= self.max_chars:
            return [text] if text else []

        parts = []
        remaining = text

        while len(remaining) > self.max_chars:
            split_at = remaining.rfind(
                "\n",
                0,
                self.max_chars + 1,
            )

            if split_at < self.max_chars // 2:
                split_at = remaining.rfind(
                    " ",
                    0,
                    self.max_chars + 1,
                )

            if split_at < self.max_chars // 2:
                split_at = self.max_chars

            part = remaining[:split_at].strip()

            if not part:
                part = remaining[:self.max_chars].strip()
                split_at = self.max_chars

            parts.append(part)
            remaining = remaining[split_at:].strip()

        if remaining:
            parts.append(remaining)

        return parts

    def _split_chunk(self, chunk: dict) -> list[dict]:
        content_parts = self._split_text(
            chunk["content"]
        )

        if not content_parts:
            return []

        if len(content_parts) == 1:
            return [chunk]

        result = []

        for index, content_part in enumerate(
            content_parts,
            start=1,
        ):
            part = chunk.copy()

            part["chunk_id"] = (
                f'{chunk["chunk_id"]}_part-{index}'
            )
            part["content"] = content_part

            if part["point"] is not None:
                context = [
                    f'Điều {part["article"]}. '
                    f'{part["article_title"]}',
                    (
                        f'Khoản {part["clause"]}. '
                        f'{part["clause_preamble"]}'
                    ) if part["clause_preamble"] else "",
                    (
                        f'Điểm {part["point"]}. '
                        f'{content_part}'
                    ),
                ]

                part["embedding_text"] = "\n".join(
                    item for item in context if item
                )
            elif part["clause"] is not None:
                part["embedding_text"] = (
                    f'Điều {part["article"]}. '
                    f'{part["article_title"]}\n'
                    f'Khoản {part["clause"]}. '
                    f'{content_part}'
                )
            else:
                part["embedding_text"] = (
                    f'Điều {part["article"]}. '
                    f'{part["article_title"]}\n'
                    f'{content_part}'
                )

            result.append(part)

        return result
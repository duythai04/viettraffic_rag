from src.schemas.chunk import LegalChunk


class LegalChunker:

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
            )

            article_title = article.get(
                "article_title",
                "",
            )

            clauses = article.get("clauses", [])

            if clauses:
                chunks.extend(
                    self._chunk_clauses(
                        clauses=clauses,
                        document_id=document_id,
                        article_number=article_number,
                        article_title=article_title,
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
                    chunks.append(chunk)

        return chunks

    def _chunk_clauses(
        self,
        clauses: list[dict],
        document_id: str,
        article_number: str,
        article_title: str,
        source: str,
    ) -> list[dict]:

        chunks = []

        for clause in clauses:
            clause_number = str(
                clause.get("clause_number", "")
            )

            points = clause.get("points", [])

            if points:
                for point in points:
                    chunk = self._create_point_chunk(
                        point=point,
                        document_id=document_id,
                        article_number=article_number,
                        article_title=article_title,
                        clause_number=clause_number,
                        source=source,
                    )

                    if chunk:
                        chunks.append(chunk)

            else:
                chunk = self._create_clause_chunk(
                    clause=clause,
                    document_id=document_id,
                    article_number=article_number,
                    article_title=article_title,
                    source=source,
                )

                if chunk:
                    chunks.append(chunk)

        return chunks

    def _create_point_chunk(
        self,
        point: dict,
        document_id: str,
        article_number: str,
        article_title: str,
        clause_number: str,
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
            f"{document_id}"
            f"_dieu-{article_number}"
            f"_khoan-{clause_number}"
            f"_diem-{point_letter}"
        )

        citation = (
            f"Điểm {point_letter} "
            f"Khoản {clause_number} "
            f"Điều {article_number}"
        )

        chunk = LegalChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            article=article_number,
            article_title=article_title,
            clause=clause_number,
            point=point_letter,
            content=content,
            citation=citation,
            source=source,
        )

        return chunk.to_dict()

    def _create_clause_chunk(
        self,
        clause: dict,
        document_id: str,
        article_number: str,
        article_title: str,
        source: str,
    ) -> dict | None:

        clause_number = str(
            clause.get("clause_number", "")
        ).strip()

        content = str(
            clause.get("content", "")
        ).strip()

        if not content:
            return None

        chunk_id = (
            f"{document_id}"
            f"_dieu-{article_number}"
            f"_khoan-{clause_number}"
        )

        citation = (
            f"Khoản {clause_number} "
            f"Điều {article_number}"
        )

        chunk = LegalChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            article=article_number,
            article_title=article_title,
            clause=clause_number,
            point=None,
            content=content,
            citation=citation,
            source=source,
        )

        return chunk.to_dict()

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
            f"{document_id}"
            f"_dieu-{article_number}"
        )

        citation = f"Điều {article_number}"

        chunk = LegalChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            article=article_number,
            article_title=article_title,
            clause=None,
            point=None,
            content=content,
            citation=citation,
            source=source,
        )

        return chunk.to_dict()
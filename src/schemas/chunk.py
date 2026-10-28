from dataclasses import asdict, dataclass


@dataclass
class LegalChunk:
    chunk_id: str
    document_id: str
    article: str
    article_title: str
    clause: str | None
    point: str | None
    content: str
    citation: str
    source: str
    clause_preamble: str = ""
    embedding_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
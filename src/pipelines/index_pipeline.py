from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser
from src.chunking.legal_chunker import LegalChunker
from src.embeddings.embedder import LegalEmbedder
from src.schemas.chunk import LegalChunk


class LegalIndexPipeline:
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        batch_size: int = 8,
        cache_dir: str = "data/processed/embeddings",
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.loader = PDFLoader()
        self.cleaner = LegalTextCleaner()
        self.parser = LegalParser()
        self.chunker = LegalChunker()

        self.embedder = None

    def load_chunks(
        self,
        pdf_path: str,
        document_id: str,
    ) -> list[LegalChunk]:
        print("[1/4] Loading PDF...")

        text = self.loader.load_document_text(pdf_path)
        clean_text = self.cleaner.clean(text)

        print("[2/4] Parsing legal document...")

        articles = self.parser.parse_articles(clean_text)

        print(f"Articles: {len(articles)}")

        print("[3/4] Creating legal chunks...")

        raw_chunks = self.chunker.chunk_document(
            articles=articles,
            document_id=document_id,
            source=Path(pdf_path).name,
        )

        chunks = [
            LegalChunk(**chunk)
            for chunk in raw_chunks
        ]

        print(f"Chunks: {len(chunks)}")

        return chunks

    def _cache_key(
        self,
        chunks: list[LegalChunk],
    ) -> str:
        hasher = hashlib.sha256()

        hasher.update(self.model_name.encode("utf-8"))

        for chunk in chunks:
            hasher.update(chunk.chunk_id.encode("utf-8"))
            hasher.update(chunk.embedding_text.encode("utf-8"))

        return hasher.hexdigest()[:16]

    def run(
        self,
        pdf_path: str,
        document_id: str,
    ) -> dict:
        start = time.perf_counter()

        chunks = self.load_chunks(
            pdf_path=pdf_path,
            document_id=document_id,
        )

        if not chunks:
            raise ValueError("No chunks generated")

        cache_key = self._cache_key(chunks)

        vector_path = self.cache_dir / f"{cache_key}.npy"
        metadata_path = self.cache_dir / f"{cache_key}.json"

        if vector_path.exists() and metadata_path.exists():
            print("[4/4] Loading cached embeddings...")

            vectors = np.load(
                vector_path,
                allow_pickle=False,
            )

            with metadata_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                metadata = json.load(file)

            if (
                vectors.ndim != 2
                or vectors.shape[0] != len(chunks)
                or len(metadata) != len(chunks)
            ):
                raise ValueError("Invalid embedding cache")

            if [
                item["chunk_id"] for item in metadata
            ] != [
                chunk.chunk_id for chunk in chunks
            ]:
                raise ValueError("Cached chunk IDs do not match")

        else:
            print("[4/4] Generating embeddings...")

            if self.embedder is None:
                self.embedder = LegalEmbedder(
                    model_name=self.model_name,
                    batch_size=self.batch_size,
                )

            vectors = self.embedder.embed_texts(
                [
                    chunk.embedding_text
                    for chunk in chunks
                ]
            )

            metadata = [
                chunk.to_dict()
                for chunk in chunks
            ]

            np.save(vector_path, vectors)

            with metadata_path.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    metadata,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

        if not np.isfinite(vectors).all():
            raise ValueError("Invalid vector values")

        elapsed = time.perf_counter() - start

        print("=" * 60)
        print("INDEXING COMPLETED")
        print("=" * 60)
        print("Chunks:", len(chunks))
        print("Vectors:", vectors.shape)
        print("Time:", round(elapsed, 2), "seconds")
        print("Vector cache:", vector_path)
        print("Metadata cache:", metadata_path)

        return {
            "chunks": chunks,
            "vectors": vectors,
            "metadata": metadata,
            "vector_path": str(vector_path),
            "metadata_path": str(metadata_path),
            "elapsed_seconds": elapsed,
        }
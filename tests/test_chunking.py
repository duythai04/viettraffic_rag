from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser
from src.chunking.legal_chunker import LegalChunker


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"


loader = PDFLoader()
cleaner = LegalTextCleaner()
parser = LegalParser()
chunker = LegalChunker()


text = loader.load_document_text(PDF_PATH)

clean_text = cleaner.clean(text)

articles = parser.parse_articles(clean_text)

chunks = chunker.chunk_document(
    articles=articles,
    document_id="168-2024-ND-CP",
    source="168-nd-cp.ocr.pdf",
)


print("=" * 80)
print("LEGAL CHUNKING TEST")
print("=" * 80)

print("Articles:", len(articles))
print("Chunks:", len(chunks))


point_chunks = [
    chunk
    for chunk in chunks
    if chunk["point"] is not None
]

clause_chunks = [
    chunk
    for chunk in chunks
    if (
        chunk["clause"] is not None
        and chunk["point"] is None
    )
]

article_chunks = [
    chunk
    for chunk in chunks
    if chunk["clause"] is None
]


print("Point chunks:", len(point_chunks))
print("Clause chunks:", len(clause_chunks))
print("Article chunks:", len(article_chunks))


print("\n" + "=" * 80)
print("SAMPLE CHUNKS")
print("=" * 80)

for chunk in chunks[:10]:
    print("\nChunk ID:", chunk["chunk_id"])
    print("Citation:", chunk["citation"])
    print("Article title:", chunk["article_title"])
    print("Content:", chunk["content"][:300])
    print("-" * 80)
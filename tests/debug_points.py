from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"

TARGETS = [
    (3, 3),
    (6, 3),
    (6, 4),
    (6, 5),
    (7, 3),
    (8, 6),
    (9, 1),
    (20, 5),
    (26, 2),
    (26, 7),
    (32, 7),
    (32, 9),
    (32, 14),
    (41, 3),
    (41, 4),
    (47, 3),
    (48, 1),
    (52, 8),
]


loader = PDFLoader()
cleaner = LegalTextCleaner()
parser = LegalParser()

text = cleaner.clean(
    loader.load_document_text(PDF_PATH)
)

articles = parser.parse_articles(text)


for article_number, clause_number in TARGETS:

    article = parser.get_article(
        articles,
        article_number,
    )

    if article is None:
        continue

    clause = None

    for item in article["clauses"]:
        if item["clause_number"] == str(clause_number):
            clause = item
            break

    if clause is None:
        continue

    print()
    print("=" * 100)
    print(
        f"ĐIỀU {article_number} "
        f"- KHOẢN {clause_number}"
    )
    print("=" * 100)

    lines = clause["content"].splitlines()

    for index, line in enumerate(lines):
        stripped = line.strip()

        is_marker = (
            len(stripped) >= 2
            and stripped[1] == ")"
        )

        prefix = ">>" if is_marker else "  "

        print(
            f"{prefix} {index:03d}: {line}"
        )

    print()
    print(
        "PARSED POINTS:",
        [
            point["point"]
            for point in clause["points"]
        ],
    )
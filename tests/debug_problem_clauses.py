from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"

PROBLEM_ARTICLES = [
    12,
    26,
    31,
    32,
    35,
    39,
    47,
    49,
    55,
]


loader = PDFLoader()
cleaner = LegalTextCleaner()
parser = LegalParser()


text = cleaner.clean(
    loader.load_document_text(
        PDF_PATH
    )
)

articles = parser.parse_articles(
    text
)


for article_number in PROBLEM_ARTICLES:

    article = parser.get_article(
        articles,
        article_number
    )

    if article is None:
        continue

    print()
    print("=" * 90)

    print(
        f"ĐIỀU {article_number}"
    )

    print("=" * 90)

    clauses = article["clauses"]

    if not clauses:

        print(
            "NO CLAUSES DETECTED"
        )

        print(
            article["content"][:1500]
        )

        continue

    for index, clause in enumerate(
        clauses
    ):

        number = clause[
            "clause_number"
        ]

        content = (
            clause["content"]
            .replace("\n", " ")
        )

        content = " ".join(
            content.split()
        )

        preview = content[:220]

        print(
            f"{index:02d} | "
            f"Khoản {number:<4} | "
            f"{preview}"
        )
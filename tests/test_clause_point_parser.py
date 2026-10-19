from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"

TEST_ARTICLES = [6, 7, 10]


loader = PDFLoader()
cleaner = LegalTextCleaner()
parser = LegalParser()


# =========================================================
# LOAD + CLEAN
# =========================================================

raw_text = loader.load_document_text(
    PDF_PATH
)

cleaned_text = cleaner.clean(
    raw_text
)


# =========================================================
# PARSE DOCUMENT
# =========================================================

articles = parser.parse_articles(
    cleaned_text
)


# =========================================================
# TEST ARTICLES
# =========================================================

for article_number in TEST_ARTICLES:

    article = parser.get_article(
        articles,
        article_number,
    )

    if article is None:

        print(
            f"\nKhông tìm thấy Điều "
            f"{article_number}"
        )

        continue

    print()
    print("=" * 80)

    print(
        f"Điều {article['article_number']}. "
        f"{article['article_title']}"
    )

    print("=" * 80)

    clauses = article["clauses"]

    print(
        f"TOTAL CLAUSES: {len(clauses)}"
    )

    print()

    # =====================================================
    # CLAUSE SUMMARY
    # =====================================================

    for clause in clauses:

        clause_number = (
            clause["clause_number"]
        )

        points = clause["points"]

        point_letters = [
            point["point"]
            for point in points
        ]

        print(
            f"Khoản {clause_number:<3}"
            f" | Points: {len(points):<3}"
            f" | {point_letters}"
        )

    # =====================================================
    # VALIDATE CLAUSE SEQUENCE
    # =====================================================

    validation = (
        parser.validate_clause_sequence(
            clauses
        )
    )

    print()
    print("-" * 80)
    print("CLAUSE VALIDATION")
    print("-" * 80)

    print(
        "Total clauses :",
        validation["total_clauses"],
    )

    print(
        "Missing       :",
        validation["missing_clauses"],
    )

    print(
        "Duplicates    :",
        validation["duplicate_clauses"],
    )

    print(
        "Out of order  :",
        validation["out_of_order"],
    )

    # =====================================================
    # POINT DETAILS
    # =====================================================

    print()
    print("-" * 80)
    print("POINT DETAILS")
    print("-" * 80)

    for clause in clauses:

        print(
            f"\nKhoản "
            f"{clause['clause_number']}"
        )

        if not clause["points"]:

            print(
                "  Không có Điểm."
            )

            continue

        for point in clause["points"]:

            preview = (
                point["content"]
                .replace("\n", " ")
            )

            preview = " ".join(
                preview.split()
            )

            if len(preview) > 100:
                preview = (
                    preview[:100]
                    + "..."
                )

            print(
                f"  {point['point']}) "
                f"{preview}"
            )

    print()
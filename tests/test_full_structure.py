from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"


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


print("=" * 90)
print("FULL LEGAL STRUCTURE VALIDATION")
print("=" * 90)

print(
    f"\nTotal articles: {len(articles)}"
)


problem_articles = []


for article in articles:

    article_number = article[
        "article_number"
    ]

    clauses = article[
        "clauses"
    ]

    validation = (
        parser.validate_clause_sequence(
            clauses
        )
    )

    clause_numbers = [
        clause["clause_number"]
        for clause in clauses
    ]

    problems = []


    # ==========================================
    # Missing clauses
    # ==========================================

    if validation["missing_clauses"]:

        problems.append(
            "missing="
            + str(
                validation[
                    "missing_clauses"
                ]
            )
        )


    # ==========================================
    # Duplicate clauses
    # ==========================================

    if validation["duplicate_clauses"]:

        problems.append(
            "duplicates="
            + str(
                validation[
                    "duplicate_clauses"
                ]
            )
        )


    # ==========================================
    # Out of order
    # ==========================================

    if validation["out_of_order"]:

        problems.append(
            "out_of_order="
            + str(
                validation[
                    "out_of_order"
                ]
            )
        )


    # ==========================================
    # Suspicious large clause number
    # ==========================================

    suspicious_large = []

    for clause in clauses:

        number = str(
            clause["clause_number"]
        )

        if (
            number.isdigit()
            and int(number) > 30
        ):

            suspicious_large.append(
                int(number)
            )


    if suspicious_large:

        problems.append(
            "large="
            + str(
                suspicious_large
            )
        )


    # ==========================================
    # Print
    # ==========================================

    status = (
        "⚠️"
        if problems
        else "OK"
    )

    print(
        f"\nĐiều {article_number:<4}"
        f" | Clauses: {len(clauses):<3}"
        f" | {status}"
    )

    print(
        "  Numbers:",
        clause_numbers,
    )


    if problems:

        problem_articles.append(
            article_number
        )

        for problem in problems:

            print(
                "  ->",
                problem
            )


print()
print("=" * 90)
print("SUMMARY")
print("=" * 90)

print(
    "Total articles:",
    len(articles)
)

print(
    "Problem articles:",
    problem_articles
)

print(
    "Total problem articles:",
    len(problem_articles)
)
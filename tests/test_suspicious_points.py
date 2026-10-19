import re

from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"


# Những ký tự OCR thường nhầm với chữ cái của Điểm
SUSPICIOUS_POINT_PATTERN = re.compile(
    r"(?m)^[ \t]*"
    r"([01Il])"
    r"[ \t]*\)"
    r"[ \t]*(.+)$"
)


loader = PDFLoader()
cleaner = LegalTextCleaner()
parser = LegalParser()


# =========================================================
# LOAD DOCUMENT
# =========================================================

raw_text = loader.load_document_text(
    PDF_PATH
)

cleaned_text = cleaner.clean(
    raw_text
)

articles = parser.parse_articles(
    cleaned_text
)


# =========================================================
# SCAN SUSPICIOUS POINTS
# =========================================================

total_suspicious = 0

print("=" * 80)
print("SUSPICIOUS POINT SCANNER")
print("=" * 80)


for article in articles:

    article_number = article[
        "article_number"
    ]

    for clause in article["clauses"]:

        clause_number = clause[
            "clause_number"
        ]

        content = clause[
            "content"
        ]

        matches = list(
            SUSPICIOUS_POINT_PATTERN.finditer(
                content
            )
        )

        if not matches:
            continue

        for match in matches:

            total_suspicious += 1

            suspicious_char = (
                match.group(1)
            )

            suspicious_content = (
                match.group(2)
                .strip()
            )

            suspicious_content = (
                " ".join(
                    suspicious_content.split()
                )
            )

            if len(suspicious_content) > 150:
                suspicious_content = (
                    suspicious_content[:150]
                    + "..."
                )

            print()
            print(
                f"Điều {article_number}"
                f" - Khoản {clause_number}"
            )

            print(
                f"Suspicious: "
                f"{suspicious_char})"
            )

            print(
                f"Content: "
                f"{suspicious_content}"
            )


# =========================================================
# SUMMARY
# =========================================================

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)

print(
    "Total articles:",
    len(articles)
)

print(
    "Suspicious points:",
    total_suspicious
)
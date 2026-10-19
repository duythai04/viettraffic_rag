from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"


loader = PDFLoader()
cleaner = LegalTextCleaner()
parser = LegalParser()


# =========================================================
# LOAD
# =========================================================

raw_text = loader.load_document_text(
    PDF_PATH
)


# =========================================================
# CLEAN
# =========================================================

cleaned_text = cleaner.clean(
    raw_text
)


# =========================================================
# PARSE
# =========================================================

articles = parser.parse_articles(
    cleaned_text
)


# =========================================================
# BASIC RESULT
# =========================================================

print("=" * 70)
print(
    f"TOTAL ARTICLES: {len(articles)}"
)
print("=" * 70)


for article in articles[:10]:

    print()

    print("=" * 70)

    print(
        f"Điều "
        f"{article['article_number']}. "
        f"{article['article_title']}"
    )

    print("-" * 70)

    print(
        article["content"][:500]
    )


# =========================================================
# ARTICLE NUMBERS
# =========================================================

print()
print("=" * 70)
print("ARTICLE NUMBERS")
print("=" * 70)

numbers = [
    article["article_number"]
    for article in articles
]

print(numbers)


# =========================================================
# VALIDATION
# =========================================================

validation = (
    parser.validate_article_sequence(
        articles
    )
)

print()
print("=" * 70)
print("VALIDATION")
print("=" * 70)

print(
    "Total articles :",
    validation["total_articles"],
)

print(
    "First article  :",
    validation["first_article"],
)

print(
    "Last article   :",
    validation["last_article"],
)

print(
    "Missing        :",
    validation["missing_articles"],
)

print(
    "Duplicates     :",
    validation["duplicate_articles"],
)


# =========================================================
# CHECK ARTICLE 10
# =========================================================

print()
print("=" * 70)
print("CHECK ARTICLE 10")
print("=" * 70)

article_10 = parser.get_article(
    articles,
    10,
)

if article_10:

    print(
        f"Điều "
        f"{article_10['article_number']}. "
        f"{article_10['article_title']}"
    )

    print("-" * 70)

    print(
        article_10["content"][:1000]
    )

else:

    print(
        "Không tìm thấy Điều 10."
    )

    print(
    "Out of order  :",
    validation["out_of_order"],
)
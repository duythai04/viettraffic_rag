from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"


loader = PDFLoader()
cleaner = LegalTextCleaner()


pages = loader.load(PDF_PATH)


print(f"Total pages: {len(pages)}")


for page in pages[:5]:

    raw_text = page["text"]

    cleaned_text = cleaner.clean(raw_text)

    print("\n")
    print("=" * 70)

    print(f"PAGE {page['page_number']}")

    print("=" * 70)

    print(cleaned_text[:3000])
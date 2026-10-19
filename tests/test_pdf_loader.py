from pathlib import Path

from src.ingestion.pdf_loader import PDFLoader


DATA_DIR = Path("data/raw")

loader = PDFLoader()

pdf_files = sorted(DATA_DIR.rglob("*.pdf"))

print(f"\nFound {len(pdf_files)} PDF files.\n")


for pdf_path in pdf_files:
    try:
        result = loader.analyze(pdf_path)

        print("=" * 70)

        print(f"File       : {pdf_path}")
        print(f"Pages      : {result['total_pages']}")
        print(f"Text pages : {result['text_pages']}")
        print(f"Empty pages: {result['empty_pages']}")
        print(f"Characters : {result['total_chars']}")
        print(f"Text ratio : {result['text_ratio']}")
        print(f"Needs OCR  : {result['needs_ocr']}")

    except Exception as error:
        print("=" * 70)
        print(f"ERROR: {pdf_path}")
        print(error)
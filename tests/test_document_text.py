from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"


loader = PDFLoader()
cleaner = LegalTextCleaner()


raw_text = loader.load_document_text(PDF_PATH)

cleaned_text = cleaner.clean(raw_text)


print("Raw characters:", len(raw_text))
print("Clean characters:", len(cleaned_text))

print("\n===== DOCUMENT PREVIEW =====\n")

print(cleaned_text[:5000])
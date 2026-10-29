
import pymupdf
from pathlib import Path


def extract_pdf_pages(pdf_path):
    """Extract text while preserving page numbers and source."""

    path = Path(pdf_path)

    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    pages = []

    with pymupdf.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            if text:
                pages.append({
                    "source": path.name,
                    "page": page_number,
                    "text": text
                })

    if not pages:
        raise ValueError(
            "No selectable text found. This PDF may be scanned "
            "and require OCR."
        )

    return pages


if __name__ == "__main__":
    pdf_path = input("Enter the PDF file path: ").strip().strip('"')

    try:
        pages = extract_pdf_pages(pdf_path)

        print(f"\nSuccessfully extracted {len(pages)} pages.\n")

        for item in pages[:3]:
            print(f"Source: {item['source']}")
            print(f"Page: {item['page']}")
            print(f"Text preview: {item['text'][:300]}")
            print("-" * 50)

    except (FileNotFoundError, ValueError, Exception) as error:
        print(f"PDF extraction failed: {error}")

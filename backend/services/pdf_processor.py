# pdf_processor.py — Now using pypdf instead of PyMuPDF
# pypdf is pure Python — no compilation, works on any Python version

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List


def extract_and_chunk_pdf(file_path: str, filename: str) -> List[dict]:
    """
    Reads a PDF and returns chunked text with metadata.
    Uses pypdf instead of PyMuPDF — same result, no compilation needed.
    """

    # Open the PDF
    reader = PdfReader(file_path)

    # Check if it's encrypted
    if reader.is_encrypted:
        raise ValueError(
            f"'{filename}' is password-protected. "
            "Please upload an unencrypted PDF."
        )

    # Extract text page by page
    pages_text = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()

        # Some pages might be images with no extractable text — skip those
        if text and text.strip():
            pages_text.append({
                "text": text,
                "page_number": page_num + 1  # Human-readable page number
            })

    if not pages_text:
        raise ValueError(
            f"No extractable text found in '{filename}'. "
            "The PDF may contain only scanned images."
        )

    # Split each page's text into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    all_chunks = []

    for page_data in pages_text:
        page_chunks = text_splitter.split_text(page_data["text"])

        for chunk_text in page_chunks:
            all_chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source": filename,
                    "page": page_data["page_number"]
                }
            })

    print(f"'{filename}': {len(all_chunks)} chunks from"
          f"{len(pages_text)} pages")
    return all_chunks
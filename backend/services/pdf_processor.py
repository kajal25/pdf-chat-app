# This file reads PDF files and splits them into chunks
# PyMuPDF (imported as "fitz") handles the PDF reading
# LangChain's text splitter handles the chunking
import fitz  # This is PyMuPDF — the import name is "fitz"
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List


def extract_and_chunk_pdf(file_path: str, filename: str) -> List[dict]:
    """
    Reads a PDF file and returns a list of text chunks with metadata.
    Each chunk looks like:
    {
        "text": "some text from the PDF...",
        "metadata": {
            "source": "myfile.pdf",
            "page": 3
        }
    }
    """
    # Open the PDF using PyMuPDF
    doc = fitz.open(file_path)

    # First, collect all text organized by page
    pages_text = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # Get the page
        text = page.get_text()  # Extract all text from that page
        if text.strip():  # Only keep pages that have text
            pages_text.append({
                "text": text,
                "page_number": page_num + 1,  # Pages start at 1, not 0
            })

    doc.close()  # Always close the file when done

    # Now split each page's text into smaller chunks
    # Why? Because sending a full 50-page PDF to OpenAI would be very expensive
    # and exceed the token limit. We only send the RELEVANT chunks.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Each chunk is max 1000 characters
        chunk_overlap=200,  # Chunks overlap by 200 chars so context isn't lost
        length_function=len,  # Measure size by character count
    )

    all_chunks = []
    for page_data in pages_text:
        # Split this page's text into multiple small chunks
        page_chunks = text_splitter.split_text(page_data["text"])
        for chunk_text in page_chunks:
            all_chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source": filename,  # Which PDF file
                    "page": page_data["page_number"],  # Which page
                },
            })

        print(
            f"📄 Processed '{filename}': {len(all_chunks)} chunks "
            f"from {len(pages_text)} pages"
        )
    return all_chunks
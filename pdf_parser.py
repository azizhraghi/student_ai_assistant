"""
PDF Parser Tool — extracts text from uploaded PDF files using PyMuPDF.
"""

import fitz  # PyMuPDF


def parse_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF given its raw bytes.
    Returns a single string with all pages joined.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            pages_text.append(f"--- Page {page_num} ---\n{text}")
    doc.close()
    return "\n\n".join(pages_text) if pages_text else "No text found in PDF."

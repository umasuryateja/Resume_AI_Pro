"""
PDF Reader Module
Extracts text from PDF files using pdfplumber.
"""

import io
import pdfplumber
import re


def extract_text_from_pdf(file_obj) -> str:
    """
    Extract raw text from a PDF file object (BytesIO or file path).
    Returns extracted text as a string.
    """
    text_parts = []

    try:
        if isinstance(file_obj, (str, bytes)):
            # File path
            with pdfplumber.open(file_obj) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        else:
            # BytesIO or file-like object
            if hasattr(file_obj, 'read'):
                raw = file_obj.read()
                file_obj = io.BytesIO(raw)
            with pdfplumber.open(file_obj) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

    except Exception as e:
        return f"[Error reading PDF: {e}]"

    full_text = '\n'.join(text_parts)
    return post_process_extracted_text(full_text)


def post_process_extracted_text(text: str) -> str:
    """Fix common PDF extraction artifacts."""
    if not text:
        return ""
    # Fix hyphenated line breaks
    text = re.sub(r'-\n', '', text)
    # Normalize line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove form feeds and other control chars
    text = re.sub(r'[\x0c\x0b]', '\n', text)
    # Remove leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    text = '\n'.join(lines)
    return text.strip()


def get_pdf_metadata(file_obj) -> dict:
    """Extract metadata from PDF (author, title, etc.)."""
    meta = {}
    try:
        if hasattr(file_obj, 'read'):
            raw = file_obj.read()
            file_obj = io.BytesIO(raw)
        with pdfplumber.open(file_obj) as pdf:
            meta = pdf.metadata or {}
            meta['pages'] = len(pdf.pages)
    except Exception:
        pass
    return meta

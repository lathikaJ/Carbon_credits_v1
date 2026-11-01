"""
Knowledge Base Package
======================
Document storage, PDF parsing, text extraction, and deduplication utilities.
"""

from .parser import (
    compute_file_hash,
    is_duplicate_document,
    extract_text_from_pdf,
    clean_extracted_text,
)

__all__ = [
    "compute_file_hash",
    "is_duplicate_document",
    "extract_text_from_pdf",
    "clean_extracted_text",
]


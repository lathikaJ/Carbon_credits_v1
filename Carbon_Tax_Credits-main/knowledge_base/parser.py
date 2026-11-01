"""
Knowledge Base Document Parser & Deduplication Module
======================================================
Provides cryptographic hashing (SHA-256), lineage deduplication checking,
and robust text extraction from PDF documents using pdfplumber, pypdf,
and stream fallbacks with text cleaning.
"""

import os
import sys
import re
import csv
import json
import zlib
import hashlib
import unicodedata
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger("KnowledgeBaseParser")


def compute_file_hash(file_bytes: bytes) -> str:
    """
    Computes and returns the deterministic SHA-256 hex digest of the document bytes.
    """
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise TypeError("file_bytes must be bytes or bytearray.")
    return hashlib.sha256(file_bytes).hexdigest()


def _resolve_path(path: str) -> str:
    """Resolves relative paths against current directory and known project roots."""
    if os.path.exists(path):
        return path
    alt = os.path.join(os.path.dirname(__file__), "..", path)
    if os.path.exists(alt):
        return alt
    alt2 = os.path.join("Carbon_Tax_Credits-main", path)
    if os.path.exists(alt2):
        return alt2
    return path


def is_duplicate_document(
    file_hash: str,
    lineage_csv_path: str = "input_data/Data_Lineage.csv",
    lineage_json_path: str = "knowledge_base/document_lineage.json",
) -> bool:
    """
    Checks if a document with the given SHA-256 hash has already been ingested.
    Scans the JSON document lineage registry and CSV audit log.
    """
    if not file_hash:
        return False

    target_hash = file_hash.strip().lower()

    # 1. Check local JSON registry if available
    json_path = _resolve_path(lineage_json_path)
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        if entry.get("sha256_hash", "").strip().lower() == target_hash:
                            return True
                elif isinstance(data, dict):
                    if target_hash in [h.lower() for h in data.keys()]:
                        return True
        except Exception as e:
            logger.warning(f"Failed to read document lineage JSON ({json_path}): {e}")

    # 2. Check Data_Lineage.csv
    csv_path = _resolve_path(lineage_csv_path)
    if os.path.exists(csv_path):
        try:
            with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Check any column that might store hash
                    for val in row.values():
                        if val and str(val).strip().lower() == target_hash:
                            return True
        except Exception as e:
            logger.warning(f"Failed to check duplicate document in CSV ({csv_path}): {e}")

    return False


def clean_extracted_text(text: str) -> str:
    """
    Cleans raw extracted text:
    - Normalizes Unicode characters (NFKD)
    - Removes common page headers and footers (e.g., 'Page X of Y')
    - Repairs broken hyphenated line wraps (e.g., 'informa-\\ntion' -> 'information')
    - Collapses excessive blank lines and whitespace while preserving paragraph flow.
    """
    if not text:
        return ""

    # 1. Unicode normalization
    text = unicodedata.normalize("NFKD", text)

    # 2. Remove standard page headers/footers
    text = re.sub(r'(?i)\bPage\s+\d+\s+(?:of\s+\d+)?\b', '', text)
    text = re.sub(r'^\s*[-—]\s*\d+\s*[-—]\s*$', '', text, flags=re.MULTILINE)

    # 3. Join hyphenated words split across lines
    text = re.sub(r'(\w+)-\n\s*(\w+)', r'\1\2', text)

    # 4. Normalize line breaks: collapse single newlines in sentences, preserve double newlines
    paragraphs = re.split(r'\n\s*\n', text)
    cleaned_paras = []
    for para in paragraphs:
        # Collapse intra-paragraph whitespace
        cleaned = " ".join(para.split())
        if cleaned:
            cleaned_paras.append(cleaned)

    return "\n\n".join(cleaned_paras).strip()


def _extract_text_from_raw_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Fallback regex stream parser for minimal test/mock PDFs and raw PDF byte streams.
    Extracts text enclosed in Tj / TJ text operators or content streams.
    """
    texts: List[str] = []

    # Search for stream ... endstream blocks
    streams = re.findall(rb'stream\r?\n(.*?)\r?\nendstream', pdf_bytes, re.DOTALL)
    if not streams:
        streams = [pdf_bytes]

    for stream in streams:
        decompressed = stream
        try:
            decompressed = zlib.decompress(stream)
        except Exception:
            pass

        # Match text in parenthesis before Tj or in TJ array
        # e.g., (Hello World) Tj
        tj_matches = re.findall(rb'\((.*?)\)\s*Tj', decompressed)
        for m in tj_matches:
            texts.append(m.decode("latin1", errors="ignore"))

        # Match text arrays: [(Hello) 20 (World)] TJ
        array_matches = re.findall(rb'\[(.*?)\]\s*TJ', decompressed, re.DOTALL)
        for arr in array_matches:
            sub_matches = re.findall(rb'\((.*?)\)', arr)
            for sm in sub_matches:
                texts.append(sm.decode("latin1", errors="ignore"))

    # Fallback to plain printable strings if no standard operators found
    if not texts:
        matches = re.findall(rb'\(([a-zA-Z0-9\s\.,;:_\-\(\)/]+)\)', pdf_bytes)
        for m in matches:
            decoded = m.decode("latin1", errors="ignore").strip()
            if len(decoded) > 3 and not decoded.startswith("/"):
                texts.append(decoded)

    return " ".join(texts)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF file using pdfplumber, with fallback to pypdf,
    and fallback to raw PDF stream parsing. Cleans and normalizes the extracted text.
    """
    resolved_path = _resolve_path(pdf_path)
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    raw_text = ""

    # Attempt 1: pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(resolved_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            raw_text = "\n".join(pages)
            if raw_text.strip():
                logger.info(f"Extracted {len(raw_text)} chars from {os.path.basename(resolved_path)} using pdfplumber.")
    except Exception as e:
        logger.debug(f"pdfplumber extraction failed or not available for {resolved_path}: {e}")

    # Attempt 2: pypdf fallback
    if not raw_text.strip():
        try:
            from pypdf import PdfReader
            reader = PdfReader(resolved_path)
            pages = [page.extract_text() or "" for page in reader.pages]
            raw_text = "\n".join(pages)
            if raw_text.strip():
                logger.info(f"Extracted {len(raw_text)} chars from {os.path.basename(resolved_path)} using pypdf.")
        except Exception as e:
            logger.debug(f"pypdf extraction failed or not available for {resolved_path}: {e}")

    # Attempt 3: Raw PDF stream fallback
    if not raw_text.strip():
        try:
            with open(resolved_path, "rb") as f:
                pdf_bytes = f.read()
            raw_text = _extract_text_from_raw_pdf_bytes(pdf_bytes)
            if raw_text.strip():
                logger.info(f"Extracted {len(raw_text)} chars from {os.path.basename(resolved_path)} using stream fallback.")
        except Exception as e:
            logger.warning(f"All PDF text extraction strategies failed for {resolved_path}: {e}")

    return clean_extracted_text(raw_text)


"""
Automated Web Scraper & Policy Ingestion Engine (scraper.py)
============================================================
Crawls regulatory authorities (CEA, Verra, MOEF), discovers official carbon credit rules,
grid baselines, and green tax policies, downloads PDFs, and logs lineage metadata.
"""

import os
import sys
import re
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

import requests

# Resolve helper parser from knowledge_base
try:
    from knowledge_base.parser import (
        compute_file_hash,
        is_duplicate_document,
        extract_text_from_pdf,
        clean_extracted_text,
    )
except ImportError:
    # Path fallback when invoked from different working directory
    KB_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    sys.path.insert(0, os.path.abspath(KB_DIR))
    from parser import (
        compute_file_hash,
        is_duplicate_document,
        extract_text_from_pdf,
        clean_extracted_text,
    )

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:
    # Pure-Python fallback DOM parser for anchor tags when bs4 is not yet installed
    class Tag:
        def __init__(self, href: str = "", text: str = ""):
            self.attrs = {"href": href}
            self.text = text

        def get(self, key: str, default: Any = None) -> Any:
            return self.attrs.get(key, default)

    class BeautifulSoup:  # type: ignore
        def __init__(self, html: str, parser: str = "html.parser"):
            self.html = html or ""

        def find_all(self, tag: str, **kwargs) -> List[Tag]:
            if tag == "a":
                links = []
                for m in re.finditer(r'<a\s+([^>]*?)>(.*?)</a>', self.html, re.DOTALL | re.IGNORECASE):
                    attrs_str, inner_text = m.groups()
                    href_m = re.search(r'href=[\'"]([^\'"]+)[\'"]', attrs_str, re.IGNORECASE)
                    href = href_m.group(1) if href_m else ""
                    clean_inner = re.sub(r'<[^>]+>', '', inner_text).strip()
                    links.append(Tag(href=href, text=clean_inner))
                return links
            return []

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PolicyWebScraper")

# Target Seed Configurations (Exact requirements)
TARGET_SOURCES: List[Dict[str, Any]] = [
    {
        "name": "CEA Grid Baseline",
        "url": "https://cea.nic.in/",
        "keywords": ["grid emission factor", "baseline database", "co2 baseline"],
        "fallback_document": "cea_grid_baseline_2026.txt",
    },
    {
        "name": "Verra / CDM Registry Rules",
        "url": "https://verra.org/",
        "keywords": ["carbon credit registry", "methodology", "additionality rules"],
        "fallback_document": "carbon_credit_registry_rules.txt",
    },
    {
        "name": "National Green Tax & Manufacturing Acts",
        "url": "https://moef.gov.in/",
        "keywords": ["green tax incentives", "manufacturing act", "rebate eligibility", "oee benchmark"],
        "fallback_document": "green_tax_incentives_act.txt",
    },
]

GLOBAL_KEYWORDS: List[str] = [
    "grid emission factor",
    "cea baseline",
    "carbon credit rules",
    "green tax rebate",
    "additionality",
    "oee benchmark",
    "baseline database",
    "co2 baseline",
    "methodology",
    "manufacturing act",
    "rebate eligibility",
]

DEFAULT_USER_AGENT: str = (
    "EcoPulse-AI-PolicyComplianceAgent/2.0 (+https://ecopulse.ai/compliance-crawler; industrial-auditing)"
)


def _resolve_dir(path: str) -> str:
    """Finds real existing path for target directories across repo variants."""
    if os.path.exists(path):
        return path
    alt = os.path.join(os.path.dirname(__file__), "..", path)
    if os.path.exists(alt):
        return alt
    alt2 = os.path.join("Carbon_Tax_Credits-main", path)
    if os.path.exists(alt2):
        return alt2
    return path


def log_ingestion_lineage(
    document_meta: Dict[str, Any],
    lineage_file: str = "input_data/Data_Lineage.csv",
    lineage_json_file: str = "knowledge_base/document_lineage.json",
) -> None:
    """
    Appends document ingestion audit records containing:
    timestamp, document_name, source_url, sha256_hash, chunk_count, status ('INGESTED' / 'SKIPPED').
    """
    resolved_json = _resolve_dir(lineage_json_file)
    resolved_csv = _resolve_dir(lineage_file)

    os.makedirs(os.path.dirname(resolved_json) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(resolved_csv) or ".", exist_ok=True)

    timestamp = document_meta.get("timestamp") or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    doc_name = document_meta.get("document_name", "unknown_document")
    source_url = document_meta.get("source_url", "local_cache")
    sha256_hash = document_meta.get("sha256_hash", "")
    chunk_count = int(document_meta.get("chunk_count", 1))
    status = document_meta.get("status", "INGESTED")

    record = {
        "timestamp": timestamp,
        "document_name": doc_name,
        "source_url": source_url,
        "sha256_hash": sha256_hash,
        "chunk_count": chunk_count,
        "status": status,
    }

    # 1. Update JSON lineage store
    history: List[Dict[str, Any]] = []
    if os.path.exists(resolved_json):
        try:
            with open(resolved_json, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []

    history.append(record)
    with open(resolved_json, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    # 2. Append to CSV lineage store
    write_header = not os.path.exists(resolved_csv) or os.path.getsize(resolved_csv) == 0
    try:
        with open(resolved_csv, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "timestamp",
                    "document_name",
                    "source_url",
                    "sha256_hash",
                    "chunk_count",
                    "status",
                ])
            writer.writerow([
                timestamp,
                doc_name,
                source_url,
                sha256_hash,
                chunk_count,
                status,
            ])
    except Exception as e:
        logger.warning(f"Failed to append to lineage CSV ({resolved_csv}): {e}")

    logger.info(f"Lineage Audit Logged: {doc_name} -> {status} (hash: {sha256_hash[:12]}...)")


def fetch_latest_policy_documents(
    target_urls: Optional[List[Dict[str, Any]]] = None,
    output_pdf_dir: str = "knowledge_base/pdfs/",
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: int = 8,
) -> List[Dict[str, Any]]:
    """
    Queries live regulatory targets using requests with custom User-Agent,
    identifies relevant policy documents and PDFs matching keyword filters,
    downloads binaries, computes SHA-256 hashes, and logs ingestion lineage.
    Falls back gracefully to cached text documents if endpoints are non-responsive or blocked.
    """
    resolved_pdf_dir = _resolve_dir(output_pdf_dir)
    os.makedirs(resolved_pdf_dir, exist_ok=True)

    sources = target_urls or TARGET_SOURCES
    downloaded_docs: List[Dict[str, Any]] = []

    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})

    for source in sources:
        name = source.get("name", "Unknown Source")
        url = source.get("url", "")
        keywords = [k.lower() for k in source.get("keywords", [])]
        fallback_doc = source.get("fallback_document", "")

        logger.info(f"Checking regulatory endpoint: {name} ({url})")

        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code != 200:
                logger.warning(
                    f"Target regulatory site ({url}) returned HTTP {resp.status_code}. "
                    "Skipped non-responsive endpoint / Requires manual sync. "
                    f"Proceeding with cached local text fallback ({fallback_doc})."
                )
                continue

            html = resp.text
            soup = BeautifulSoup(html, "html.parser")
            anchors = soup.find_all("a")

            found_documents = 0
            for a in anchors:
                href = a.get("href", "")
                text = (a.text or "").strip().lower()

                if not href:
                    continue

                full_url = urljoin(url, href)
                href_lower = href.lower()

                # Filter for PDF or policy documents
                is_doc = any(href_lower.endswith(ext) for ext in [".pdf", ".doc", ".docx"]) or "download" in href_lower
                if not is_doc:
                    continue

                # Filter against source keywords and global compliance keywords
                matches_keyword = any(k in text or k in href_lower for k in keywords + GLOBAL_KEYWORDS)
                if not matches_keyword:
                    continue

                filename = os.path.basename(urlparse(full_url).path) or f"policy_doc_{found_documents + 1}.pdf"
                if not filename.endswith(".pdf"):
                    filename += ".pdf"

                target_pdf_path = os.path.join(resolved_pdf_dir, filename)

                try:
                    # Download document binary
                    doc_resp = session.get(full_url, timeout=timeout)
                    if doc_resp.status_code == 200 and doc_resp.content:
                        file_bytes = doc_resp.content
                        file_hash = compute_file_hash(file_bytes)

                        # Deduplication Check
                        if is_duplicate_document(file_hash):
                            logger.info(f"Document {filename} matches existing SHA-256 hash. SKIPPED.")
                            log_ingestion_lineage({
                                "document_name": filename,
                                "source_url": full_url,
                                "sha256_hash": file_hash,
                                "chunk_count": 0,
                                "status": "SKIPPED",
                            })
                            continue

                        # Save new document binary
                        with open(target_pdf_path, "wb") as f:
                            f.write(file_bytes)

                        found_documents += 1
                        doc_meta = {
                            "document_name": filename,
                            "source_url": full_url,
                            "pdf_path": target_pdf_path,
                            "sha256_hash": file_hash,
                            "chunk_count": 1,
                            "status": "INGESTED",
                            "source_authority": name,
                        }
                        log_ingestion_lineage(doc_meta)
                        downloaded_docs.append(doc_meta)
                except Exception as dl_err:
                    logger.warning(f"Failed to download document from {full_url}: {dl_err}")

            if found_documents == 0:
                logger.info(
                    f"No direct PDF documents matched keywords on {url}. "
                    "Skipped non-responsive endpoint / Requires manual sync. "
                    f"Using cached local text fallback ({fallback_doc})."
                )

        except Exception as e:
            logger.warning(
                f"Connection error to {url}: {e}. "
                "Skipped non-responsive endpoint / Requires manual sync. "
                f"Proceeding with cached local text fallback ({fallback_doc})."
            )

    return downloaded_docs


def convert_pdfs_to_knowledge_text(
    pdf_dir: str = "knowledge_base/pdfs/",
    txt_dir: str = "knowledge_base/",
) -> List[str]:
    """
    Scans PDF directory for downloaded documents, extracts and cleans text,
    and writes standardized .txt files into knowledge_base/ for Agent 3 indexing.
    """
    resolved_pdf_dir = _resolve_dir(pdf_dir)
    resolved_txt_dir = _resolve_dir(txt_dir)

    os.makedirs(resolved_txt_dir, exist_ok=True)
    converted_files: List[str] = []

    if not os.path.exists(resolved_pdf_dir):
        return converted_files

    for fname in sorted(os.listdir(resolved_pdf_dir)):
        if not fname.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(resolved_pdf_dir, fname)
        txt_fname = fname[:-4] + ".txt"
        txt_path = os.path.join(resolved_txt_dir, txt_fname)

        try:
            extracted_text = extract_text_from_pdf(pdf_path)
            if extracted_text.strip():
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)
                converted_files.append(txt_path)
                logger.info(f"Successfully converted PDF -> Knowledge Base text: {txt_fname}")
            else:
                logger.warning(f"Empty text extracted from {fname}; skipping conversion.")
        except Exception as e:
            logger.warning(f"Failed to convert PDF {fname}: {e}")

    return converted_files


def sync_policy_knowledge_base(
    target_urls: Optional[List[Dict[str, Any]]] = None,
    output_pdf_dir: str = "knowledge_base/pdfs/",
    knowledge_dir: str = "knowledge_base/",
    force_reindex: bool = False,
) -> Dict[str, Any]:
    """
    End-to-end execution of automated policy document ingestion:
    1. Fetches and downloads new regulatory PDFs with SHA-256 deduplication.
    2. Converts newly ingested PDFs into clean knowledge base text files.
    3. Re-indexes PolicyComplianceAgent vector and BM25 stores.
    """
    logger.info("==================================================================")
    logger.info("      STARTING AUTOMATED POLICY KNOWLEDGE BASE UPDATE             ")
    logger.info("==================================================================")

    # Step 1: Download latest PDFs with keyword filter and deduplication
    downloaded = fetch_latest_policy_documents(
        target_urls=target_urls,
        output_pdf_dir=output_pdf_dir,
    )

    # Step 2: Convert PDFs to clean text
    converted = convert_pdfs_to_knowledge_text(
        pdf_dir=output_pdf_dir,
        txt_dir=knowledge_dir,
    )

    # Step 3: Trigger Agent 3 dynamic re-indexing
    reindexed_count = 0
    try:
        from agents.policy_compliance_agent import PolicyComplianceAgent
        agent = PolicyComplianceAgent(knowledge_dir=knowledge_dir)
        reindexed_count = agent.reload_knowledge_base(knowledge_dir=knowledge_dir)
        logger.info(f"Agent 3 Re-indexing Complete: {reindexed_count} total policy chunks active in hybrid index.")
    except Exception as e:
        logger.warning(f"PolicyComplianceAgent re-indexing triggered with warning: {e}")

    logger.info("==================================================================")
    logger.info("       POLICY KNOWLEDGE BASE SYNC COMPLETED SUCCESSFULLY          ")
    logger.info("==================================================================")

    return {
        "downloaded_documents": downloaded,
        "converted_files": converted,
        "active_policy_chunks": reindexed_count,
    }


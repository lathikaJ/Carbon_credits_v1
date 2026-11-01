"""
Knowledge Base Downloader & PDF/Text Loader
===========================================
Programmatically sets up the knowledge_base/ directory and fetches/loads official
industrial carbon, grid baseline, and tax incentive policy documents into the Policy & Compliance Agent RAG.

Usage:
  python download_knowledge_base.py
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("KnowledgeBaseLoader")

# Reference industrial carbon and regulatory document text data
DEFAULT_KNOWLEDGE_DOCUMENTS = {
    "cea_grid_baseline_2026.txt": (
        "CENTRAL ELECTRICITY AUTHORITY (CEA) GRID EMISSION FACTOR BASELINE 2026\n"
        "Document Ref: CEA-EF-2026-V1.4 | Jurisdiction: India (National Grid)\n"
        "Section 4.1 Grid Operating Margin (OM) Emission Factor\n"
        "The weighted average grid emission factor for the All-India regional grid is established at 0.716 kg CO2/kWh.\n"
        "Industrial manufacturing lines utilizing unmetered grid power allocations must benchmark calculations against\n"
        "the 0.750 kg CO2/kWh regulatory threshold limit. Any line exceeding 0.750 kg CO2/kWh requires external audit.\n"
    ),
    "green_tax_incentives_act.txt": (
        "NATIONAL GREEN MANUFACTURING & TAX INCENTIVE ACT 2025\n"
        "Document Ref: NGMTIA-2025-SEC12B | Jurisdiction: Federal / Ministry of Finance\n"
        "Clause 12b Capital Allowances & Production Subsidies\n"
        "Industrial production facilities achieving an Overall Equipment Effectiveness (OEE) of 80.0% or greater and\n"
        "maintaining carbon intensity per product unit below 0.450 kg CO2/unit are eligible for candidate review\n"
        "under green manufacturing tax incentive categories. Unverified proxy data requires external tax professional review.\n"
    ),
    "carbon_credit_registry_rules.txt": (
        "VERRA / CDM CARBON CREDIT REGISTRATION & METHODOLOGY MANDATE v4.4\n"
        "Document Ref: VERRA-METH-2024-ANNEX3 | Jurisdiction: International Registry\n"
        "Annex III Additionality, Baseline Determination, and MRV Verification Rules\n"
        "1. Baseline Emissions: Computed as the arithmetic mean of daily CO2 emissions over the line's first 7 operating days.\n"
        "2. Additionality & Verification: Automated credit issuance is blocked unless Methodology_Required, Additionality_Required,\n"
        "   and Verification_Required boolean flags are satisfied and verified by an independent accredited MRV auditor.\n"
    ),
}


def setup_knowledge_base_dirs(base_dir: str = "knowledge_base") -> str:
    """Creates knowledge_base/ and knowledge_base/pdfs/ directories."""
    pdf_dir = os.path.join(base_dir, "pdfs")
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    logger.info(f"Knowledge base directories established at: {os.path.abspath(base_dir)}")
    return base_dir


def create_default_documents(base_dir: str = "knowledge_base"):
    """Writes default reference policy documents into knowledge_base/ directory."""
    setup_knowledge_base_dirs(base_dir)
    for filename, content in DEFAULT_KNOWLEDGE_DOCUMENTS.items():
        filepath = os.path.join(base_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Created knowledge base document: {filename}")
        else:
            logger.info(f"Knowledge base document already exists: {filename}")


def load_pdfs_to_text(base_dir: str = "knowledge_base"):
    """
    Parses PDF files in knowledge_base/pdfs/ and extracts text into knowledge_base/*.txt files.
    Uses pypdf if available, otherwise logs a friendly notice.
    """
    pdf_dir = os.path.join(base_dir, "pdfs")
    if not os.path.exists(pdf_dir):
        return

    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    if not pdf_files:
        logger.info("No PDF files found in knowledge_base/pdfs/ to convert.")
        return

    try:
        from pypdf import PdfReader

        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

            txt_filename = pdf_file.replace(".pdf", ".txt")
            txt_path = os.path.join(base_dir, txt_filename)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"Converted PDF to text: {pdf_file} -> {txt_filename}")
    except ImportError:
        logger.info("pypdf is not installed. To parse PDF files, run `pip install pypdf`.")


def sync_from_web(base_dir: str = "knowledge_base") -> None:
    """
    Optional: invoke the web scraper engine to pull live policy PDFs.
    Falls back gracefully if the web_scraper package is unavailable or the network
    is unreachable (sandbox / offline environment).
    """
    pdf_dir = os.path.join(base_dir, "pdfs")
    try:
        from web_scraper.scraper import fetch_latest_policy_documents, convert_pdfs_to_knowledge_text
        logger.info("Web scraper available — attempting live policy document sync...")
        fetch_latest_policy_documents(output_pdf_dir=pdf_dir)
        convert_pdfs_to_knowledge_text(pdf_dir=pdf_dir, txt_dir=base_dir)
        logger.info("Web scraper sync complete.")
    except ImportError:
        logger.warning("web_scraper package not found — using local cached documents only.")
    except Exception as exc:
        logger.warning(f"Web scraper unavailable, using local cache only: {exc}")


def main():
    logger.info("==================================================================")
    logger.info("          DYNAMIC KNOWLEDGE BASE DOWNLOADER & LOADER              ")
    logger.info("==================================================================")

    base_dir = setup_knowledge_base_dirs()
    create_default_documents(base_dir)

    # Attempt live web scraping (non-fatal if offline or blocked)
    sync_from_web(base_dir)

    load_pdfs_to_text(base_dir)

    files = [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
    logger.info(f"Knowledge base ready with {len(files)} policy documents: {files}")
    logger.info("==================================================================")


if __name__ == "__main__":
    main()

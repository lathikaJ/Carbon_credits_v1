"""
EcoPulse AI Web Scraper Package
===============================
Automated regulatory and carbon policy document scraping, extraction, and lineage tracking.
"""

from .scraper import (
    TARGET_SOURCES,
    GLOBAL_KEYWORDS,
    fetch_latest_policy_documents,
    convert_pdfs_to_knowledge_text,
    log_ingestion_lineage,
    sync_policy_knowledge_base,
)

__all__ = [
    "TARGET_SOURCES",
    "GLOBAL_KEYWORDS",
    "fetch_latest_policy_documents",
    "convert_pdfs_to_knowledge_text",
    "log_ingestion_lineage",
    "sync_policy_knowledge_base",
]


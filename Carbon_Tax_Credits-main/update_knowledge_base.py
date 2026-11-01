"""
Update Knowledge Base CLI (update_knowledge_base.py)
=====================================================
Automated policy document web scraping, PDF downloading, text extraction,
dynamic chunking, and Agent 3 knowledge base re-indexing.

Usage:
    python update_knowledge_base.py --sync
    python update_knowledge_base.py --sync --force-reindex
    python update_knowledge_base.py --force-reindex

Flags:
    --sync           Trigger live web scraping, PDF downloading, text extraction,
                     and lineage logging.
    --force-reindex  Force regeneration of all text files and vector embeddings in
                     knowledge_base/ (can be used alone to re-index cached files).
"""

import os
import sys
import argparse
import logging

# ---------------------------------------------------------------------------
# Path bootstrap — ensure project root is importable regardless of CWD
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("UpdateKnowledgeBase")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_base_documents(knowledge_dir: str = "knowledge_base") -> None:
    """Write default seed policy documents if not already present."""
    try:
        from download_knowledge_base import create_default_documents
        create_default_documents(knowledge_dir)
    except Exception as exc:
        logger.warning(f"Could not create default documents: {exc}")


def _run_sync(force_reindex: bool = False) -> dict:
    """
    Invoke the web scraper pipeline from web_scraper.scraper.

    Returns a dict with keys: downloaded_documents, converted_files, active_policy_chunks.
    """
    try:
        from web_scraper.scraper import TARGET_SOURCES, sync_policy_knowledge_base

        result = sync_policy_knowledge_base(
            target_urls=TARGET_SOURCES,
            output_pdf_dir="knowledge_base/pdfs/",
            knowledge_dir="knowledge_base/",
            force_reindex=force_reindex,
        )
        return result
    except Exception as exc:
        logger.error(f"Sync pipeline encountered an error: {exc}")
        return {"downloaded_documents": [], "converted_files": [], "active_policy_chunks": 0}


def _run_force_reindex(knowledge_dir: str = "knowledge_base/") -> int:
    """
    Force Agent 3 to re-chunk and rebuild its hybrid vector + BM25 index
    from whatever .txt files currently exist in knowledge_base/.

    Returns the count of active policy chunks after re-indexing.
    """
    try:
        from agents.policy_compliance_agent import PolicyComplianceAgent

        agent = PolicyComplianceAgent(knowledge_dir=knowledge_dir)
        count = agent.reload_knowledge_base(knowledge_dir=knowledge_dir)
        logger.info(f"Force re-index complete: {count} active policy chunks in hybrid index.")
        return count
    except Exception as exc:
        logger.error(f"Force re-index failed: {exc}")
        return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="update_knowledge_base.py",
        description="EcoPulse AI — Automated Policy Knowledge Base Updater",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python update_knowledge_base.py --sync\n"
            "  python update_knowledge_base.py --sync --force-reindex\n"
            "  python update_knowledge_base.py --force-reindex\n"
        ),
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Trigger live web scraping, PDF downloading, text extraction, and lineage logging.",
    )
    parser.add_argument(
        "--force-reindex",
        action="store_true",
        dest="force_reindex",
        help="Force regeneration of all text files and vector embeddings in knowledge_base/.",
    )
    args = parser.parse_args()

    if not args.sync and not args.force_reindex:
        logger.info("No action specified. Use --sync or --force-reindex (or both).")
        parser.print_help()
        return

    logger.info("=================================================================")
    logger.info("       EcoPulse AI — Policy Knowledge Base Update Pipeline       ")
    logger.info("=================================================================")

    # Always ensure the baseline seed documents exist
    _ensure_base_documents("knowledge_base")

    if args.sync:
        logger.info(">> Phase 1: Web scraping & document ingestion (--sync)...")
        result = _run_sync(force_reindex=args.force_reindex)
        logger.info(
            f"   Downloaded : {len(result.get('downloaded_documents', []))} document(s)\n"
            f"   Converted  : {len(result.get('converted_files', []))} PDF→TXT conversion(s)\n"
            f"   Chunks     : {result.get('active_policy_chunks', 0)} policy chunks indexed"
        )
    elif args.force_reindex:
        # --force-reindex alone (no network sync)
        logger.info(">> Phase 1 skipped (--sync not specified, using cached files only).")

    if args.force_reindex and not args.sync:
        # Standalone re-index without sync
        logger.info(">> Phase 2: Force re-indexing knowledge_base/ (--force-reindex)...")
        count = _run_force_reindex("knowledge_base/")
        logger.info(f"   Re-index complete: {count} active policy chunks.")

    logger.info("=================================================================")
    logger.info("       Knowledge Base Update Pipeline COMPLETE                   ")
    logger.info("=================================================================")


if __name__ == "__main__":
    main()


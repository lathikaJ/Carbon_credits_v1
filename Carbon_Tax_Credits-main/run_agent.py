"""
CLI Runner Wrapper (run_agent.py)
=================================
Delegates execution to the top-level main.py orchestrator.

Usage:
    python run_agent.py                 # Run the 5-stage pipeline with cached KB
    python run_agent.py --sync-kb       # Sync KB from web first, then run pipeline

Flags:
    --sync-kb   Run automated policy knowledge base update (web scrape + re-index)
                before the 5-stage assessment pipeline. Falls back gracefully if
                network or scraper is unavailable.
"""

import os
import sys
import argparse
import logging

# Path bootstrap
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RunAgent")


def _sync_knowledge_base() -> None:
    """Attempt to sync the KB via web scraper; logs a warning and continues on failure."""
    try:
        from web_scraper.scraper import TARGET_SOURCES, sync_policy_knowledge_base
        logger.info("--sync-kb: Starting automated policy knowledge base sync...")
        result = sync_policy_knowledge_base(
            target_urls=TARGET_SOURCES,
            output_pdf_dir="knowledge_base/pdfs/",
            knowledge_dir="knowledge_base/",
            force_reindex=False,
        )
        logger.info(
            f"--sync-kb: Sync complete — "
            f"{len(result.get('downloaded_documents', []))} downloaded, "
            f"{len(result.get('converted_files', []))} converted, "
            f"{result.get('active_policy_chunks', 0)} chunks indexed."
        )
    except Exception as exc:
        logger.warning(f"--sync-kb: KB sync failed ({exc}). Continuing with cached knowledge base.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="run_agent.py",
        description="EcoPulse AI — Industrial Carbon Assessment Pipeline Runner",
    )
    parser.add_argument(
        "--sync-kb",
        action="store_true",
        dest="sync_kb",
        help="Run automated policy knowledge base update (web scrape + re-index) before pipeline.",
    )
    # Pass remaining unknown args to main.py (grid-ef, prod, energy, etc.)
    args, _ = parser.parse_known_args()

    if args.sync_kb:
        _sync_knowledge_base()

    from main import main as run_pipeline
    run_pipeline()


if __name__ == "__main__":
    main()

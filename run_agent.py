"""
Run Agent — Root-level entry point
===================================
Delegates to Carbon_Tax_Credits-main/run_agent.py so the pipeline can be
started from either the workspace root or the project subdirectory.

Usage (from /home/lathika/Desktop/Carbon_credits/):
    python3 run_agent.py
    python3 run_agent.py --sync-kb
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, "Carbon_Tax_Credits-main")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.chdir(PROJECT_DIR)

from run_agent import main  # noqa: E402

if __name__ == "__main__":
    main()


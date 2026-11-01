"""
Update Knowledge Base — Root-level entry point
===============================================
Delegates to Carbon_Tax_Credits-main/update_knowledge_base.py so the script
can be run from either the workspace root or the project subdirectory.

Usage (from /home/lathika/Desktop/Carbon_credits/):
    python3 update_knowledge_base.py --sync
    python3 update_knowledge_base.py --sync --force-reindex
    python3 update_knowledge_base.py --force-reindex
"""

import os
import sys

# Point imports at the real project directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, "Carbon_Tax_Credits-main")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Change working directory so all relative paths (knowledge_base/, input_data/, etc.)
# resolve correctly inside the project
os.chdir(PROJECT_DIR)

# Delegate entirely to the project-level CLI
from update_knowledge_base import main  # noqa: E402

if __name__ == "__main__":
    main()


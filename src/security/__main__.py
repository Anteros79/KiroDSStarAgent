"""Allow running the security module as a script.

Usage:
    python -m src.security [OPTIONS] [REPO_PATH]
"""

import sys
from src.security.cli import main

if __name__ == "__main__":
    sys.exit(main())

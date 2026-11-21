"""Demo run: one dual-community case, every strategy, oracle regret.

Run: python notebooks/01_demo_run.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contagion_quarantine.cli import demo

if __name__ == "__main__":
    sys.exit(demo())

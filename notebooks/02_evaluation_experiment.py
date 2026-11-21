"""Evaluation experiment: the full 40-case headline grid.

Run: python notebooks/02_evaluation_experiment.py
Prints the headline comparison; writes nothing (use
`python -m contagion_quarantine evaluate` to refresh results/).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contagion_quarantine.evaluate import run_all
from contagion_quarantine.report import summary_markdown

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    results = run_all(os.path.join(ROOT, "data"))
    print(summary_markdown(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Regenerate results/ and guard against headline drift.

Run: python scripts/reproduce_results.py [--out DIR]
Regenerates the evaluation into --out (default: results/) and, when a
committed results/evaluation.json exists, fails if any headline mean
adoption or regret moved by more than 0.005 -- a changed number must
come with a code or data change, not silent drift.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contagion_quarantine.evaluate import run_all
from contagion_quarantine.report import write_results

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data")
COMMITTED = os.path.join(ROOT, "results", "evaluation.json")
TOLERANCE = 0.005


def _check(old, new, label):
    if abs(old - new) > TOLERANCE:
        print("DRIFT: %s %.4f -> %.4f" % (label, old, new))
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(ROOT, "results"))
    args = parser.parse_args()
    committed = None
    if os.path.exists(COMMITTED):
        with open(COMMITTED, encoding="utf-8") as handle:
            committed = json.load(handle)
    results = run_all(DATA)
    if committed is not None:
        failures = 0
        old_h = committed["headline"]
        new_h = results["headline"]
        for strategy, entry in old_h["strategies"].items():
            failures += _check(entry["mean_adoption"],
                               new_h["strategies"][strategy]["mean_adoption"],
                               "mean_adoption[%s]" % strategy)
        if "regret" in old_h:
            for strategy, value in old_h["regret"].items():
                failures += _check(value, new_h["regret"][strategy],
                                   "regret[%s]" % strategy)
        if failures:
            return 1
        print("No headline drift (tolerance %.3f)." % TOLERANCE)
    write_results(results, args.out)
    print("Wrote %s." % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

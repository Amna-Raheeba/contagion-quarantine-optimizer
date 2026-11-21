"""Command line entry point.

Usage:
  python -m contagion_quarantine demo [--case ID]
  python -m contagion_quarantine evaluate [--out DIR]
"""

import argparse
import os
import sys

from .evaluate import load_cases, run_all, run_case
from .networks import build_network
from .quarantine import build_plan, run_plan
from .report import write_results
from .simulation import simulate, genealogy_edges

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data")


def demo(case_id=None):
    cases = load_cases(DATA)
    case = None
    for candidate in cases:
        if case_id is None and candidate["topology"] == "dual_community" and candidate["n"] == 12:
            case = candidate
            break
        if candidate["id"] == case_id:
            case = candidate
            break
    if case is None:
        case = cases[0]
    network = build_network(case["topology"], case["n"], case["network_seed"])
    seed_node = case["seed_node"]
    sim_kwargs = {"rng_seed": case["sim_seed"], "beta": case["beta"],
                  "infectious_period": case["infectious_period"], "max_steps": 40}
    pilot_seeds = [case["sim_seed"] + 1000 + i for i in range(5)]
    print("Case %s: %s network, n=%d, seed node %d, budget k=%d"
          % (case["id"], case["topology"], case["n"], seed_node, case["k"]))
    base = simulate(network, seed_node, **sim_kwargs)
    print("No intervention: adoption %d/%d (%.3f), mean realised R %.2f"
          % (base.adoption_count, base.n, base.adoption_fraction, base.mean_reproduction()))
    print("Genealogy (parent -> child @ step): %s"
          % ", ".join("%d->%d@%d" % edge for edge in genealogy_edges(base)))
    for strategy in ("degree_greedy", "ri_guided", "ri_edges"):
        plan = build_plan(strategy, network, seed_node, case["k"], sim_kwargs, pilot_seeds)
        result = run_plan(network, seed_node, plan, sim_kwargs)
        print("%s -> adoption %d/%d (%.3f)"
              % (plan.describe(), result.adoption_count, result.n, result.adoption_fraction))
    row = run_case(case)
    if "regret" in row:
        print("Oracle adoption %.3f; R_i-guided regret %.3f adoption points"
              % (row["adoption"]["oracle"], row["regret"]["ri_guided"]))
    return 0


def evaluate(out_dir):
    results = run_all(DATA)
    write_results(results, out_dir)
    headline = results["headline"]
    print("Evaluated %d cases (%d oracle-scored)."
          % (headline["cases"], headline["oracle_cases"]))
    print("Mean adoption: none %.4f | degree %.4f | R_i-guided %.4f"
          % (headline["strategies"]["none"]["mean_adoption"],
             headline["strategies"]["degree_greedy"]["mean_adoption"],
             headline["strategies"]["ri_guided"]["mean_adoption"]))
    print("Wrote results to %s" % out_dir)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="contagion_quarantine")
    sub = parser.add_subparsers(dest="command")
    demo_parser = sub.add_parser("demo")
    demo_parser.add_argument("--case", default=None)
    eval_parser = sub.add_parser("evaluate")
    eval_parser.add_argument("--out", default=os.path.join(ROOT, "results"))
    args = parser.parse_args(argv)
    if args.command == "demo":
        return demo(args.case)
    if args.command == "evaluate":
        return evaluate(args.out)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

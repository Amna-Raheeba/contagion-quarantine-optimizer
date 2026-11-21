"""Example: load one case, compare quarantine strategies, print a report.

Run: python examples/run_quarantine.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contagion_quarantine.networks import build_network
from contagion_quarantine.quarantine import build_plan, plan_oracle, run_plan
from contagion_quarantine.simulation import simulate, genealogy_edges

HERE = os.path.dirname(__file__)


def main():
    with open(os.path.join(HERE, "demo_case.json"), encoding="utf-8") as handle:
        case = json.load(handle)
    network = build_network(case["topology"], case["n"], case["network_seed"])
    seed_node = case["seed_node"]
    sim_kwargs = {"rng_seed": case["sim_seed"], "beta": case["beta"],
                  "infectious_period": case["infectious_period"], "max_steps": 40}
    pilot_seeds = [case["sim_seed"] + 1000 + i for i in range(5)]
    base = simulate(network, seed_node, **sim_kwargs)
    print("Case %s (%s, n=%d, seed node %d, budget k=%d)"
          % (case["id"], case["topology"], case["n"], seed_node, case["k"]))
    print("No intervention: adoption %.3f; genealogy %s"
          % (base.adoption_fraction,
             ", ".join("%d->%d@%d" % edge for edge in genealogy_edges(base))))
    for strategy in ("degree_greedy", "ri_guided", "ri_edges"):
        plan = build_plan(strategy, network, seed_node, case["k"], sim_kwargs, pilot_seeds)
        outcome = run_plan(network, seed_node, plan, sim_kwargs)
        print("%s -> adoption %.3f" % (plan.describe(), outcome.adoption_fraction))
    oracle_plan, oracle_adoption = plan_oracle(network, seed_node, case["k"], sim_kwargs)
    print("%s -> adoption %.3f (exhaustive optimum)"
          % (oracle_plan.describe(), oracle_adoption))
    return 0


if __name__ == "__main__":
    sys.exit(main())

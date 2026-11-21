"""The headline experiment.

Cases (data/cases.json) span 4 topologies x 2 sizes. Small networks
(n = 12) are scored against the exhaustive-search oracle; medium
networks (n = 24) are scored against the baselines only. Every case
runs the same evaluation seed for every strategy, so differences are
caused by the quarantine choice, not by luck of the draw. The R_i
estimates come from 5 pilot runs on separate seeds -- the optimiser
never sees the evaluation run it is scored on.

Strategies compared: none, degree_greedy (baseline heuristic),
random (mean of 3 seeded draws), ri_guided (the tool, node muting),
ri_edges (the tool, edge cutting), oracle (small networks only).
"""

import json
import os

from .networks import build_network
from .quarantine import build_plan, plan_oracle, run_plan

PILOT_COUNT = 5
RANDOM_REPLICATES = 3
ORACLE_MAX_N = 14
MAX_STEPS = 40

NODE_STRATEGIES = ("none", "degree_greedy", "random", "ri_guided", "ri_edges")


def load_cases(data_dir):
    path = os.path.join(data_dir, "cases.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def run_case(case):
    network = build_network(case["topology"], case["n"], case["network_seed"])
    seed_node = case["seed_node"]
    k = case["k"]
    sim_kwargs = {
        "rng_seed": case["sim_seed"],
        "beta": case["beta"],
        "infectious_period": case["infectious_period"],
        "max_steps": MAX_STEPS,
    }
    pilot_seeds = [case["sim_seed"] + 1000 + i for i in range(PILOT_COUNT)]
    adoption = {}
    endemic = {}
    plans = {}
    for strategy in NODE_STRATEGIES:
        if strategy == "random":
            fractions = []
            for rep in range(RANDOM_REPLICATES):
                plan = build_plan(strategy, network, seed_node, k, sim_kwargs,
                                  pilot_seeds, rng_seed=case["sim_seed"] + 2000 + rep)
                fractions.append(run_plan(network, seed_node, plan, sim_kwargs).adoption_fraction)
            adoption[strategy] = sum(fractions) / float(len(fractions))
            plans[strategy] = plan.describe()
            continue
        plan = build_plan(strategy, network, seed_node, k, sim_kwargs, pilot_seeds)
        result = run_plan(network, seed_node, plan, sim_kwargs)
        adoption[strategy] = result.adoption_fraction
        endemic[strategy] = result.went_endemic
        plans[strategy] = plan.describe()
    row = {
        "case_id": case["id"],
        "topology": case["topology"],
        "n": case["n"],
        "k": k,
        "seed_node": seed_node,
        "adoption": adoption,
        "endemic_none": endemic.get("none", False),
        "endemic_ri_guided": endemic.get("ri_guided", False),
        "plans": plans,
    }
    base = adoption["none"]
    row["reduction_per_node"] = dict(
        (strategy, (base - adoption[strategy]) / float(k))
        for strategy in NODE_STRATEGIES if strategy != "none")
    if case["n"] <= ORACLE_MAX_N:
        oracle_plan, oracle_adoption = plan_oracle(network, seed_node, k, sim_kwargs)
        row["adoption"]["oracle"] = oracle_adoption
        row["plans"]["oracle"] = oracle_plan.describe()
        row["regret"] = dict(
            (strategy, adoption[strategy] - oracle_adoption)
            for strategy in ("degree_greedy", "random", "ri_guided", "ri_edges"))
        row["reduction_per_node"]["oracle"] = (base - oracle_adoption) / float(k)
    return row


def _mean(values):
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def summarise(rows):
    strategies = list(NODE_STRATEGIES) + ["oracle"]
    headline = {"cases": len(rows), "strategies": {}}
    for strategy in strategies:
        values = [row["adoption"][strategy] for row in rows if strategy in row["adoption"]]
        if values:
            headline["strategies"][strategy] = {"mean_adoption": _mean(values)}
    for strategy in ("degree_greedy", "random", "ri_guided", "ri_edges", "oracle"):
        values = [row["reduction_per_node"][strategy] for row in rows
                  if strategy in row.get("reduction_per_node", {})]
        if values:
            headline["strategies"][strategy]["mean_reduction_per_node"] = _mean(values)
    oracle_rows = [row for row in rows if "regret" in row]
    headline["oracle_cases"] = len(oracle_rows)
    if oracle_rows:
        headline["regret"] = dict(
            (strategy, _mean(row["regret"][strategy] for row in oracle_rows))
            for strategy in ("degree_greedy", "random", "ri_guided", "ri_edges"))
        headline["ri_matches_oracle_fraction"] = _mean(
            1.0 if row["adoption"]["ri_guided"] <= row["adoption"]["oracle"] + 1e-12 else 0.0
            for row in oracle_rows)
        headline["ri_regret_le_degree_fraction"] = _mean(
            1.0 if row["regret"]["ri_guided"] <= row["regret"]["degree_greedy"] + 1e-12 else 0.0
            for row in oracle_rows)
    headline["endemic_rate_none"] = _mean(1.0 if row["endemic_none"] else 0.0 for row in rows)
    headline["endemic_rate_ri_guided"] = _mean(
        1.0 if row["endemic_ri_guided"] else 0.0 for row in rows)
    per_topology = {}
    for topology in sorted(set(row["topology"] for row in rows)):
        subset = [row for row in rows if row["topology"] == topology]
        per_topology[topology] = {
            "cases": len(subset),
            "mean_adoption_none": _mean(row["adoption"]["none"] for row in subset),
            "mean_adoption_degree": _mean(row["adoption"]["degree_greedy"] for row in subset),
            "mean_adoption_ri": _mean(row["adoption"]["ri_guided"] for row in subset),
        }
    headline["per_topology"] = per_topology
    return headline


def run_all(data_dir):
    cases = load_cases(data_dir)
    rows = [run_case(case) for case in cases]
    return {"rows": rows, "headline": summarise(rows)}

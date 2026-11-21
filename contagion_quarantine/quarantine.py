"""Quarantine strategies and the exhaustive-search oracle.

Every strategy answers the same question under the same budget: which
k interventions minimise final adoption of the seeded claim? The seed
node itself can never be muted (it already holds the claim).

Strategies:
- none:           no intervention (the baseline spread).
- degree_greedy:  mute the k highest-degree nodes (the standard
                  heuristic from network epidemiology).
- random:         mute k nodes uniformly at random (seeded).
- ri_guided:      the tool. Sequentially mute the node with the
                  highest mean realised reproduction number R_i,
                  measured from pilot genealogies, re-estimating R_i
                  after every pick with the partial quarantine already
                  in place (ties broken by degree).
- ri_edges:       the edge variant. Cut the k edges with the highest
                  mean pilot transmission count.
- oracle:         exhaustive search over every k-subset of candidate
                  nodes, scored on the actual evaluation run. Only
                  feasible on small networks; it exists so the other
                  strategies can be scored by regret against the true
                  optimum instead of against each other.
"""

import itertools
import random

from .models import QuarantinePlan
from .simulation import simulate, estimate_reproduction, estimate_edge_transmissions


def _candidates(network, seed_node):
    return [node for node in range(network.n) if node != seed_node]


def plan_none(network, seed_node, k):
    return QuarantinePlan("none")


def plan_degree_greedy(network, seed_node, k):
    ranked = sorted(_candidates(network, seed_node),
                    key=lambda node: (-network.degree(node), node))
    return QuarantinePlan("degree_greedy", muted=frozenset(ranked[:k]))


def plan_random(network, seed_node, k, rng_seed):
    rng = random.Random(rng_seed)
    chosen = rng.sample(_candidates(network, seed_node), k)
    return QuarantinePlan("random", muted=frozenset(chosen))


def plan_ri_guided(network, seed_node, k, mean_r):
    ranked = sorted(_candidates(network, seed_node),
                    key=lambda node: (-mean_r[node], -network.degree(node), node))
    return QuarantinePlan("ri_guided", muted=frozenset(ranked[:k]))


def plan_ri_guided_sequential(network, seed_node, k, pilot_seeds, dynamics):
    """Sequential R_i-guided quarantine with re-estimation.

    Muting the top spreader changes who spreads next, so a one-shot
    ranking spends later picks on yesterday's genealogy. This builder
    picks one node, re-runs the pilots with that node already muted,
    and picks the next node from the fresh R_i estimates, k times.
    """
    muted = set()
    for _ in range(k):
        mean_r = estimate_reproduction(network, seed_node, pilot_seeds,
                                       muted=frozenset(muted), **dynamics)
        remaining = [node for node in _candidates(network, seed_node)
                     if node not in muted]
        if not remaining:
            break
        pick = sorted(remaining,
                      key=lambda node: (-mean_r[node], -network.degree(node),
                                        node))[0]
        muted.add(pick)
    return QuarantinePlan("ri_guided", muted=frozenset(muted))


def plan_ri_edges(network, seed_node, k, mean_edge_transmissions):
    ranked = sorted(network.edges,
                    key=lambda edge: (-mean_edge_transmissions.get(edge, 0.0),
                                      -(network.degree(edge[0]) + network.degree(edge[1])),
                                      edge))
    return QuarantinePlan("ri_edges", cut_edges=frozenset(ranked[:k]))


def plan_oracle(network, seed_node, k, sim_kwargs):
    """Exhaustive search: the k-mute set with the lowest final adoption.

    Ties are broken by the lexicographically smallest node tuple so
    the oracle is deterministic. Returns (plan, adoption_fraction).
    """
    best_plan = None
    best_adoption = None
    for combo in itertools.combinations(_candidates(network, seed_node), k):
        result = simulate(network, seed_node, muted=frozenset(combo), **sim_kwargs)
        adoption = result.adoption_fraction
        if best_adoption is None or adoption < best_adoption:
            best_adoption = adoption
            best_plan = QuarantinePlan("oracle", muted=frozenset(combo))
    return best_plan, best_adoption


def build_plan(strategy, network, seed_node, k, sim_kwargs, pilot_seeds,
               rng_seed=0):
    """Build the plan for one strategy. Pilots are only run when needed."""
    if strategy == "none":
        return plan_none(network, seed_node, k)
    if strategy == "degree_greedy":
        return plan_degree_greedy(network, seed_node, k)
    if strategy == "random":
        return plan_random(network, seed_node, k, rng_seed)
    dynamics = dict((key, sim_kwargs[key]) for key in
                    ("beta", "infectious_period", "max_steps") if key in sim_kwargs)
    if strategy == "ri_guided":
        return plan_ri_guided_sequential(network, seed_node, k, pilot_seeds,
                                         dynamics)
    if strategy == "ri_edges":
        mean_edges = estimate_edge_transmissions(
            network, seed_node, pilot_seeds, **dynamics)
        return plan_ri_edges(network, seed_node, k, mean_edges)
    raise ValueError("unknown strategy: %s" % strategy)


def run_plan(network, seed_node, plan, sim_kwargs):
    return simulate(network, seed_node, muted=plan.muted,
                    cut_edges=plan.cut_edges, **sim_kwargs)

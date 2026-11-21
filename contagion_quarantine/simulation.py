"""Seeded claim-contagion simulation with a full claim genealogy.

Model: one false claim is seeded at one node. An adopter stays adopted
(SI dynamics) but only *spreads* for `infectious_period` steps after
adopting -- attention decays, so a claim can genuinely die out instead
of always saturating its connected component. Each step, every
spreading node tries each susceptible neighbour once, in fixed sorted
order, with probability

    p(u -> v) = beta * infectiousness[u] * susceptibility[v]

clipped to [0, 1]. Every adoption records its parent and step, so the
run yields a genealogy tree and a realised per-node reproduction
number R_i (the count of secondary adoptions node i directly caused).
Everything is driven by one random.Random(rng_seed): same seed, same
run, byte for byte.
"""

import random

from .models import SimResult

ENDEMIC_THRESHOLD = 0.5


def transmission_probability(network, source, target, beta):
    p = beta * network.infectiousness[source] * network.susceptibility[target]
    if p < 0.0:
        return 0.0
    if p > 1.0:
        return 1.0
    return p


def simulate(network, seed_node, rng_seed, muted=frozenset(),
             cut_edges=frozenset(), beta=0.30, infectious_period=2,
             max_steps=40):
    """Run one contagion simulation and return a SimResult."""
    if seed_node in muted:
        raise ValueError("the seed node cannot be muted")
    if not (0 <= seed_node < network.n):
        raise ValueError("seed node out of range")
    cut = set()
    for (u, v) in cut_edges:
        cut.add((min(u, v), max(u, v)))
    rng = random.Random(rng_seed)
    adopted = {seed_node: 0}
    parent = {seed_node: None}
    step = 0
    while step < max_steps:
        spreaders = [node for node in sorted(adopted)
                     if adopted[node] <= step < adopted[node] + infectious_period]
        if not spreaders:
            break
        new = {}
        for u in spreaders:
            for v in network.neighbors(u):
                if v in adopted or v in new or v in muted:
                    continue
                if (min(u, v), max(u, v)) in cut:
                    continue
                if rng.random() < transmission_probability(network, u, v, beta):
                    new[v] = u
        if not new:
            # Nobody new adopted this step; later steps can still fire
            # only if some spreader remains in its window next step.
            step += 1
            if not any(adopted[node] <= step < adopted[node] + infectious_period
                       for node in adopted):
                break
            continue
        for v in sorted(new):
            adopted[v] = step + 1
            parent[v] = new[v]
        step += 1
    secondary = [0] * network.n
    for node, par in parent.items():
        if par is not None:
            secondary[par] += 1
    fraction = len(adopted) / float(network.n)
    return SimResult(
        n=network.n,
        seed_node=seed_node,
        adopted=frozenset(adopted),
        parent=parent,
        infection_step=adopted,
        secondary_counts=tuple(secondary),
        steps_run=step,
        went_endemic=fraction >= ENDEMIC_THRESHOLD,
    )


def genealogy_edges(result):
    """The claim genealogy as (parent, child, step) triples, sorted."""
    rows = []
    for node, par in result.parent.items():
        if par is not None:
            rows.append((par, node, result.infection_step[node]))
    rows.sort(key=lambda row: (row[2], row[0], row[1]))
    return rows


def estimate_reproduction(network, seed_node, pilot_seeds, beta=0.30,
                          infectious_period=2, max_steps=40,
                          muted=frozenset()):
    """Mean realised R_i per node over pilot runs.

    This is the measurement the optimiser prescribes from: run the
    contagion a few times, read the genealogy, and average how many
    secondary adoptions each node caused. `muted` lets the estimator
    re-measure on a network where a partial quarantine is already in
    place (the sequential strategy re-estimates after every pick).
    """
    totals = [0.0] * network.n
    counts = [0] * network.n
    for pilot_seed in pilot_seeds:
        result = simulate(network, seed_node, pilot_seed, muted=muted,
                          beta=beta, infectious_period=infectious_period,
                          max_steps=max_steps)
        for node in range(network.n):
            totals[node] += result.secondary_counts[node]
            counts[node] += 1
    return tuple(totals[i] / float(counts[i]) if counts[i] else 0.0
                 for i in range(network.n))


def estimate_edge_transmissions(network, seed_node, pilot_seeds, beta=0.30,
                                infectious_period=2, max_steps=40):
    """Mean per-edge transmission count over un-quarantined pilot runs."""
    totals = dict((edge, 0.0) for edge in network.edges)
    runs = 0
    for pilot_seed in pilot_seeds:
        result = simulate(network, seed_node, pilot_seed, beta=beta,
                          infectious_period=infectious_period,
                          max_steps=max_steps)
        runs += 1
        for node, par in result.parent.items():
            if par is not None:
                edge = (min(par, node), max(par, node))
                totals[edge] += 1.0
    if runs == 0:
        return totals
    return dict((edge, total / float(runs)) for edge, total in totals.items())

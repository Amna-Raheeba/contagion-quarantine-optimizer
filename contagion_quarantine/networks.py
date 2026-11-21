"""Seeded network builders for the four headline topologies.

Every builder takes (n, seed) and is fully deterministic: the same
seed always produces the same edges and the same per-node traits.
Traits are drawn after the edges from the same RNG stream:
susceptibility in [0.40, 1.00], infectiousness in [0.60, 1.20].
"""

import random

from .models import Network

TOPOLOGIES = ("fully_connected", "tree", "dual_community", "scale_free")


def _traits(rng, n):
    susceptibility = tuple(0.40 + 0.60 * rng.random() for _ in range(n))
    infectiousness = tuple(0.60 + 0.60 * rng.random() for _ in range(n))
    return susceptibility, infectiousness


def fully_connected(n, seed):
    rng = random.Random(seed)
    edges = [(u, v) for u in range(n) for v in range(u + 1, n)]
    sus, inf = _traits(rng, n)
    return Network(n, edges, sus, inf, topology="fully_connected")


def tree(n, seed):
    """Random recursive tree: node i attaches to one earlier node."""
    rng = random.Random(seed)
    edges = []
    for node in range(1, n):
        parent = rng.randrange(node)
        edges.append((parent, node))
    sus, inf = _traits(rng, n)
    return Network(n, edges, sus, inf, topology="tree")


def dual_community(n, seed, bridges=2):
    """Two cliques joined by a small number of bridge edges."""
    rng = random.Random(seed)
    half = n // 2
    left = list(range(half))
    right = list(range(half, n))
    edges = []
    for group in (left, right):
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                edges.append((group[i], group[j]))
    seen = set(edges)
    made = 0
    guard = 0
    while made < bridges and guard < 100:
        guard += 1
        u = rng.choice(left)
        v = rng.choice(right)
        edge = (min(u, v), max(u, v))
        if edge not in seen:
            seen.add(edge)
            edges.append(edge)
            made += 1
    sus, inf = _traits(rng, n)
    return Network(n, edges, sus, inf, topology="dual_community")


def scale_free(n, seed, m=2):
    """Barabasi-Albert preferential attachment with m edges per new node."""
    rng = random.Random(seed)
    if n <= m + 1:
        return fully_connected(n, seed)
    edges = set()
    for u in range(m + 1):
        for v in range(u + 1, m + 1):
            edges.add((u, v))
    degree = [0] * n
    for (u, v) in edges:
        degree[u] += 1
        degree[v] += 1
    for node in range(m + 1, n):
        targets = set()
        while len(targets) < m:
            pool = []
            for existing in range(node):
                pool.extend([existing] * degree[existing])
            if not pool:
                targets.add(rng.randrange(node))
            else:
                targets.add(rng.choice(pool))
        for target in targets:
            edge = (min(target, node), max(target, node))
            edges.add(edge)
            degree[target] += 1
            degree[node] += 1
    sus, inf = _traits(rng, n)
    return Network(n, sorted(edges), sus, inf, topology="scale_free")


BUILDERS = {
    "fully_connected": fully_connected,
    "tree": tree,
    "dual_community": dual_community,
    "scale_free": scale_free,
}


def build_network(topology, n, seed):
    if topology not in BUILDERS:
        raise ValueError("unknown topology: %s" % topology)
    return BUILDERS[topology](n, seed)

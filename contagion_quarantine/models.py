"""Core data types for the contagion-quarantine optimiser.

A Network is a fixed set of agents with undirected contact edges and
per-node traits (susceptibility, infectiousness) drawn once, seeded,
when the network is built. A SimResult is the full record of one
contagion run: who adopted, who infected whom (the claim genealogy),
when, and how many secondary adoptions each node caused.
"""


class Network(object):
    """An agent contact network with per-node contagion traits."""

    def __init__(self, n, edges, susceptibility, infectiousness, topology="custom"):
        if n <= 0:
            raise ValueError("network needs at least one node")
        if len(susceptibility) != n or len(infectiousness) != n:
            raise ValueError("trait vectors must match node count")
        clean = set()
        for (u, v) in edges:
            if u == v:
                raise ValueError("self loops are not allowed")
            if not (0 <= u < n and 0 <= v < n):
                raise ValueError("edge endpoint out of range")
            clean.add((min(u, v), max(u, v)))
        self.n = n
        self.edges = tuple(sorted(clean))
        self.susceptibility = tuple(float(x) for x in susceptibility)
        self.infectiousness = tuple(float(x) for x in infectiousness)
        self.topology = topology
        adjacency = [[] for _ in range(n)]
        for (u, v) in self.edges:
            adjacency[u].append(v)
            adjacency[v].append(u)
        self._adjacency = tuple(tuple(sorted(a)) for a in adjacency)

    def neighbors(self, node):
        return self._adjacency[node]

    def degree(self, node):
        return len(self._adjacency[node])

    def degrees(self):
        return tuple(len(a) for a in self._adjacency)

    def edge_set(self):
        return set(self.edges)


class SimResult(object):
    """The outcome of one contagion simulation run."""

    def __init__(self, n, seed_node, adopted, parent, infection_step,
                 secondary_counts, steps_run, went_endemic):
        self.n = n
        self.seed_node = seed_node
        self.adopted = frozenset(adopted)
        self.parent = dict(parent)
        self.infection_step = dict(infection_step)
        self.secondary_counts = tuple(secondary_counts)
        self.steps_run = steps_run
        self.went_endemic = went_endemic

    @property
    def adoption_count(self):
        return len(self.adopted)

    @property
    def adoption_fraction(self):
        return len(self.adopted) / float(self.n)

    def reproduction_number(self, node):
        """Realised R_i: secondary adoptions directly caused by node."""
        return self.secondary_counts[node]

    def mean_reproduction(self):
        """Mean realised R over nodes that adopted."""
        if not self.adopted:
            return 0.0
        total = sum(self.secondary_counts[node] for node in self.adopted)
        return total / float(len(self.adopted))


class QuarantinePlan(object):
    """A chosen intervention: nodes to mute and/or edges to cut."""

    def __init__(self, strategy, muted=frozenset(), cut_edges=frozenset()):
        self.strategy = strategy
        self.muted = frozenset(muted)
        self.cut_edges = frozenset(cut_edges)

    @property
    def budget_used(self):
        return len(self.muted) + len(self.cut_edges)

    def describe(self):
        parts = []
        if self.muted:
            parts.append("mute %s" % sorted(self.muted))
        if self.cut_edges:
            parts.append("cut %s" % sorted(self.cut_edges))
        if not parts:
            return "%s: no intervention" % self.strategy
        return "%s: %s" % (self.strategy, "; ".join(parts))

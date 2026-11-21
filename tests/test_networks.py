"""Tests for the seeded network builders."""

import pytest

from contagion_quarantine.models import Network
from contagion_quarantine.networks import build_network, TOPOLOGIES


def test_all_topologies_build():
    for topology in TOPOLOGIES:
        net = build_network(topology, 12, 42)
        assert net.n == 12
        assert net.topology == topology
        assert len(net.edges) > 0


def test_builders_are_deterministic():
    for topology in TOPOLOGIES:
        first = build_network(topology, 15, 7)
        second = build_network(topology, 15, 7)
        assert first.edges == second.edges
        assert first.susceptibility == second.susceptibility
        assert first.infectiousness == second.infectiousness


def test_different_seeds_differ():
    first = build_network("scale_free", 20, 1)
    second = build_network("scale_free", 20, 2)
    assert first.edges != second.edges or first.susceptibility != second.susceptibility


def test_unknown_topology_raises():
    with pytest.raises(ValueError):
        build_network("hypercube", 10, 1)


def test_fully_connected_edge_count():
    net = build_network("fully_connected", 10, 3)
    assert len(net.edges) == 10 * 9 // 2
    assert all(net.degree(node) == 9 for node in range(10))


def test_tree_edge_count_and_connected():
    net = build_network("tree", 20, 5)
    assert len(net.edges) == 19
    seen = {0}
    frontier = [0]
    while frontier:
        node = frontier.pop()
        for neighbour in net.neighbors(node):
            if neighbour not in seen:
                seen.add(neighbour)
                frontier.append(neighbour)
    assert seen == set(range(20))


def test_dual_community_structure():
    net = build_network("dual_community", 12, 9)
    left = set(range(6))
    right = set(range(6, 12))
    cross = [edge for edge in net.edges
             if (edge[0] in left) != (edge[1] in left)]
    assert len(cross) == 2
    within = len(net.edges) - len(cross)
    assert within == 2 * (6 * 5 // 2)
    assert left and right


def test_scale_free_has_hub():
    net = build_network("scale_free", 30, 11)
    degrees = net.degrees()
    assert max(degrees) >= 5
    assert max(degrees) > min(degrees)


def test_traits_in_declared_ranges():
    net = build_network("tree", 25, 13)
    for value in net.susceptibility:
        assert 0.40 <= value <= 1.00
    for value in net.infectiousness:
        assert 0.60 <= value <= 1.20


def test_network_rejects_self_loop():
    with pytest.raises(ValueError):
        Network(3, [(0, 0)], (1.0,) * 3, (1.0,) * 3)


def test_network_rejects_out_of_range_edge():
    with pytest.raises(ValueError):
        Network(3, [(0, 5)], (1.0,) * 3, (1.0,) * 3)


def test_network_rejects_mismatched_traits():
    with pytest.raises(ValueError):
        Network(3, [(0, 1)], (1.0,) * 2, (1.0,) * 3)


def test_network_deduplicates_edges():
    net = Network(3, [(0, 1), (1, 0), (0, 1)], (1.0,) * 3, (1.0,) * 3)
    assert net.edges == ((0, 1),)

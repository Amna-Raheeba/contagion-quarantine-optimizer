"""Tests for the contagion simulation and its genealogy."""

import pytest

from contagion_quarantine.models import Network
from contagion_quarantine.networks import build_network
from contagion_quarantine.simulation import (
    simulate, genealogy_edges, estimate_reproduction,
    estimate_edge_transmissions, transmission_probability,
)


def line_network(n=5):
    edges = [(i, i + 1) for i in range(n - 1)]
    return Network(n, edges, (1.0,) * n, (1.0,) * n, topology="line")


def test_simulation_is_deterministic():
    net = build_network("scale_free", 16, 21)
    first = simulate(net, 0, 99, beta=0.3)
    second = simulate(net, 0, 99, beta=0.3)
    assert first.adopted == second.adopted
    assert first.parent == second.parent
    assert first.secondary_counts == second.secondary_counts
    assert first.steps_run == second.steps_run


def test_seed_always_adopted_at_step_zero():
    net = build_network("tree", 12, 4)
    result = simulate(net, 3, 5)
    assert 3 in result.adopted
    assert result.infection_step[3] == 0
    assert result.parent[3] is None


def test_zero_beta_means_no_spread():
    net = line_network()
    result = simulate(net, 0, 1, beta=0.0)
    assert result.adopted == frozenset({0})
    assert result.adoption_fraction == 0.2


def test_full_beta_line_spreads_to_end():
    net = line_network()
    result = simulate(net, 0, 1, beta=1.0, infectious_period=2)
    assert result.adopted == frozenset(range(5))


def test_genealogy_parent_infected_earlier():
    net = build_network("dual_community", 14, 8)
    result = simulate(net, 0, 77, beta=0.35)
    for node, par in result.parent.items():
        if par is not None:
            assert result.infection_step[par] < result.infection_step[node]
            assert (min(par, node), max(par, node)) in net.edge_set()


def test_secondary_counts_sum_to_adoptions_minus_seed():
    net = build_network("scale_free", 18, 15)
    result = simulate(net, 2, 31, beta=0.3)
    assert sum(result.secondary_counts) == result.adoption_count - 1


def test_reproduction_number_matches_genealogy():
    net = build_network("tree", 15, 6)
    result = simulate(net, 0, 17, beta=0.4)
    for node in range(net.n):
        children = [child for child, par in result.parent.items() if par == node]
        assert result.reproduction_number(node) == len(children)


def test_muted_node_never_adopts_or_parents():
    net = line_network()
    result = simulate(net, 0, 1, muted=frozenset({1}), beta=1.0)
    assert 1 not in result.adopted
    assert result.adopted == frozenset({0})


def test_muting_seed_raises():
    net = line_network()
    with pytest.raises(ValueError):
        simulate(net, 0, 1, muted=frozenset({0}))


def test_cut_edge_blocks_transmission():
    net = line_network()
    result = simulate(net, 0, 1, cut_edges=frozenset({(0, 1)}), beta=1.0)
    assert result.adopted == frozenset({0})


def test_transmission_probability_clipped():
    net = Network(2, [(0, 1)], (2.0, 2.0), (2.0, 2.0))
    assert transmission_probability(net, 0, 1, 1.0) == 1.0
    net2 = Network(2, [(0, 1)], (0.5, 0.5), (0.5, 0.5))
    assert transmission_probability(net2, 0, 1, 0.4) == pytest.approx(0.1)


def test_genealogy_edges_sorted_by_step():
    net = build_network("fully_connected", 8, 2)
    result = simulate(net, 0, 3, beta=0.5)
    edges = genealogy_edges(result)
    steps = [row[2] for row in edges]
    assert steps == sorted(steps)
    assert len(edges) == result.adoption_count - 1


def test_estimate_reproduction_shape_and_range():
    net = build_network("scale_free", 12, 19)
    mean_r = estimate_reproduction(net, 0, [1, 2, 3], beta=0.3)
    assert len(mean_r) == 12
    assert all(value >= 0.0 for value in mean_r)
    assert sum(mean_r) > 0.0


def test_estimate_reproduction_with_muted():
    net = line_network()
    mean_r = estimate_reproduction(net, 0, [1, 2], beta=1.0,
                                   muted=frozenset({1}))
    assert mean_r[1] == 0.0
    assert sum(mean_r) == 0.0


def test_estimate_edge_transmissions_keys():
    net = build_network("tree", 10, 23)
    totals = estimate_edge_transmissions(net, 0, [1, 2], beta=0.4)
    assert set(totals) == net.edge_set()
    assert all(value >= 0.0 for value in totals.values())


def test_endemic_flag_on_saturated_network():
    net = build_network("fully_connected", 10, 1)
    result = simulate(net, 0, 8, beta=0.9, infectious_period=3)
    assert result.went_endemic
    assert result.adoption_fraction >= 0.5


def test_mean_reproduction_consistency():
    net = build_network("dual_community", 12, 27)
    result = simulate(net, 0, 55, beta=0.3)
    expected = (result.adoption_count - 1) / float(result.adoption_count)
    assert result.mean_reproduction() == pytest.approx(expected)

"""Tests for the quarantine strategies and the oracle."""

import pytest

from contagion_quarantine.models import Network
from contagion_quarantine.networks import build_network
from contagion_quarantine.quarantine import (
    build_plan, plan_degree_greedy, plan_none, plan_oracle,
    plan_random, plan_ri_edges, plan_ri_guided, plan_ri_guided_sequential,
    run_plan,
)

SIM = {"rng_seed": 4242, "beta": 0.3, "infectious_period": 2, "max_steps": 40}
PILOTS = [11, 12, 13, 14, 15]


def star_network():
    edges = [(0, i) for i in range(1, 6)]
    return Network(6, edges, (1.0,) * 6, (1.0,) * 6, topology="star")


def test_none_plan_is_empty():
    plan = plan_none(star_network(), 1, 2)
    assert plan.budget_used == 0


def test_degree_greedy_picks_the_hub():
    plan = plan_degree_greedy(star_network(), 1, 1)
    assert plan.muted == frozenset({0})


def test_degree_greedy_respects_budget_and_skips_seed():
    net = build_network("scale_free", 16, 3)
    plan = plan_degree_greedy(net, 0, 3)
    assert len(plan.muted) == 3
    assert 0 not in plan.muted


def test_random_plan_deterministic_and_sized():
    net = build_network("tree", 14, 5)
    first = plan_random(net, 0, 3, rng_seed=9)
    second = plan_random(net, 0, 3, rng_seed=9)
    assert first.muted == second.muted
    assert len(first.muted) == 3
    assert 0 not in first.muted


def test_ri_guided_picks_highest_r():
    net = star_network()
    mean_r = (0.0, 3.0, 1.0, 2.0, 0.5, 0.25)
    plan = plan_ri_guided(net, 0, 2, mean_r)
    assert plan.muted == frozenset({1, 3})


def test_ri_guided_never_mutes_seed_even_with_highest_r():
    net = star_network()
    mean_r = (99.0, 3.0, 1.0, 2.0, 0.5, 0.25)
    plan = plan_ri_guided(net, 0, 1, mean_r)
    assert plan.muted == frozenset({1})


def test_ri_sequential_returns_k_distinct_non_seed_nodes():
    net = build_network("dual_community", 12, 8)
    dynamics = {"beta": 0.3, "infectious_period": 2, "max_steps": 40}
    plan = plan_ri_guided_sequential(net, 0, 3, PILOTS, dynamics)
    assert len(plan.muted) == 3
    assert 0 not in plan.muted
    assert plan.strategy == "ri_guided"


def test_ri_edges_cuts_real_edges_within_budget():
    net = build_network("scale_free", 12, 6)
    totals = dict((edge, 0.0) for edge in net.edges)
    hottest = net.edges[0]
    totals[hottest] = 5.0
    plan = plan_ri_edges(net, 0, 2, totals)
    assert len(plan.cut_edges) == 2
    assert plan.cut_edges <= net.edge_set()
    assert hottest in plan.cut_edges


def test_build_plan_dispatch_and_unknown():
    net = build_network("tree", 10, 2)
    for strategy in ("none", "degree_greedy", "random", "ri_guided", "ri_edges"):
        plan = build_plan(strategy, net, 0, 2, SIM, PILOTS, rng_seed=3)
        assert plan.strategy == strategy
        assert plan.budget_used <= 2
    with pytest.raises(ValueError):
        build_plan("firewall_everything", net, 0, 2, SIM, PILOTS)


def test_oracle_is_at_least_as_good_as_every_strategy():
    net = build_network("scale_free", 12, 14)
    oracle_plan, oracle_adoption = plan_oracle(net, 0, 2, SIM)
    assert len(oracle_plan.muted) == 2
    for strategy in ("degree_greedy", "ri_guided", "ri_edges"):
        plan = build_plan(strategy, net, 0, 2, SIM, PILOTS)
        adoption = run_plan(net, 0, plan, SIM).adoption_fraction
        assert oracle_adoption <= adoption + 1e-12


def test_oracle_matches_brute_force_check():
    net = build_network("tree", 8, 17)
    oracle_plan, oracle_adoption = plan_oracle(net, 0, 1, SIM)
    singles = []
    for node in range(1, 8):
        from contagion_quarantine.simulation import simulate
        singles.append(simulate(net, 0, muted=frozenset({node}), **SIM).adoption_fraction)
    assert oracle_adoption == pytest.approx(min(singles))
    assert len(oracle_plan.muted) == 1


def test_oracle_deterministic():
    net = build_network("dual_community", 10, 4)
    first_plan, first_adoption = plan_oracle(net, 0, 2, SIM)
    second_plan, second_adoption = plan_oracle(net, 0, 2, SIM)
    assert first_plan.muted == second_plan.muted
    assert first_adoption == second_adoption


def test_run_plan_applies_mutes():
    net = star_network()
    plan = plan_degree_greedy(net, 1, 1)
    result = run_plan(net, 1, plan, {"rng_seed": 1, "beta": 1.0,
                                    "infectious_period": 2, "max_steps": 40})
    assert result.adopted == frozenset({1})


def test_plan_describe_mentions_strategy():
    plan = plan_degree_greedy(star_network(), 1, 1)
    assert plan.describe().startswith("degree_greedy")
    assert plan_none(star_network(), 1, 0).describe().endswith("no intervention")

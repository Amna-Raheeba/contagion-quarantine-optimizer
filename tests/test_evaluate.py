"""Tests for the evaluation experiment."""

import os

from contagion_quarantine.evaluate import load_cases, run_all, run_case, summarise

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def test_cases_file_loads_full_grid():
    cases = load_cases(DATA)
    assert len(cases) == 40
    topologies = set(case["topology"] for case in cases)
    assert topologies == {"fully_connected", "tree", "dual_community", "scale_free"}
    sizes = set(case["n"] for case in cases)
    assert sizes == {12, 24}


def test_run_case_structure():
    case = load_cases(DATA)[0]
    row = run_case(case)
    for strategy in ("none", "degree_greedy", "random", "ri_guided", "ri_edges"):
        assert strategy in row["adoption"]
        assert 0.0 <= row["adoption"][strategy] <= 1.0
    for strategy in ("degree_greedy", "random", "ri_guided", "ri_edges"):
        assert strategy in row["reduction_per_node"]


def test_small_case_has_oracle_and_nonnegative_regret():
    cases = load_cases(DATA)
    small = [case for case in cases if case["n"] == 12][0]
    row = run_case(small)
    assert "oracle" in row["adoption"]
    for strategy in ("degree_greedy", "random", "ri_guided", "ri_edges"):
        assert row["regret"][strategy] >= -1e-12
    assert row["adoption"]["oracle"] <= row["adoption"]["none"] + 1e-12


def test_medium_case_has_no_oracle():
    cases = load_cases(DATA)
    medium = [case for case in cases if case["n"] == 24][0]
    row = run_case(medium)
    assert "oracle" not in row["adoption"]
    assert "regret" not in row


def test_run_all_headline_shape():
    results = run_all(DATA)
    headline = results["headline"]
    assert headline["cases"] == 40
    assert headline["oracle_cases"] == 20
    assert len(results["rows"]) == 40
    for key in ("endemic_rate_none", "endemic_rate_ri_guided", "per_topology", "regret"):
        assert key in headline
    assert 0.0 <= headline["endemic_rate_none"] <= 1.0
    assert 0.0 <= headline["ri_matches_oracle_fraction"] <= 1.0


def test_summarise_empty_rows():
    headline = summarise([])
    assert headline["cases"] == 0
    assert headline["oracle_cases"] == 0

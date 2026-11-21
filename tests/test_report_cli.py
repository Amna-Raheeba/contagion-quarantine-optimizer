"""Tests for reporting, the CLI, and the reproduce guard."""

import json
import os
import sys

import pytest

from contagion_quarantine.cli import main
from contagion_quarantine.evaluate import run_all
from contagion_quarantine.report import (
    headline_markdown, summary_markdown, write_results,
)

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture(scope="module")
def results():
    return run_all(DATA)


def test_summary_mentions_all_strategies(results):
    text = summary_markdown(results)
    for strategy in ("degree_greedy", "random", "ri_guided", "ri_edges", "oracle"):
        assert strategy in text
    assert "Endemic rate" in text


def test_headline_has_measured_numbers(results):
    text = headline_markdown(results)
    assert "Mean final adoption" in text
    assert "regret" in text.lower()


def test_write_results_creates_four_files(results, tmp_path):
    write_results(results, str(tmp_path))
    for name in ("evaluation.json", "evaluation.csv",
                 "evaluation_summary.md", "HEADLINE.md"):
        assert os.path.exists(os.path.join(str(tmp_path), name))
    with open(os.path.join(str(tmp_path), "evaluation.json"), encoding="utf-8") as handle:
        loaded = json.load(handle)
    assert loaded["headline"]["cases"] == 40


def test_cli_demo_runs(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "No intervention" in out
    assert "ri_guided" in out


def test_cli_evaluate_writes(tmp_path):
    assert main(["evaluate", "--out", str(tmp_path)]) == 0
    assert os.path.exists(os.path.join(str(tmp_path), "evaluation.json"))


def test_cli_no_command_returns_2():
    assert main([]) == 2


def test_reproduce_script_no_drift(tmp_path, monkeypatch):
    scripts = os.path.join(os.path.dirname(__file__), "..", "scripts")
    sys.path.insert(0, scripts)
    import reproduce_results
    monkeypatch.setattr(sys, "argv", ["reproduce_results.py", "--out", str(tmp_path)])
    assert reproduce_results.main() == 0
    assert os.path.exists(os.path.join(str(tmp_path), "evaluation.json"))

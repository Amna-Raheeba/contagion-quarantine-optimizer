"""Markdown reporting for evaluation results."""

import os


def _pct(value):
    return "%.1f%%" % (100.0 * value)


def _num(value):
    return "%.4f" % value


def summary_markdown(results):
    headline = results["headline"]
    lines = []
    lines.append("# Evaluation summary")
    lines.append("")
    lines.append("Cases: %d (%d scored against the exhaustive oracle). "
                 "All numbers are measured on seeded synthetic networks; "
                 "see the README for the honest limits."
                 % (headline["cases"], headline["oracle_cases"]))
    lines.append("")
    lines.append("## Mean final adoption by strategy (lower is better)")
    lines.append("")
    lines.append("| Strategy | Mean adoption | Mean adoption reduction per quarantined node |")
    lines.append("|---|---|---|")
    order = ("none", "degree_greedy", "random", "ri_guided", "ri_edges", "oracle")
    for strategy in order:
        entry = headline["strategies"].get(strategy)
        if not entry:
            continue
        reduction = entry.get("mean_reduction_per_node")
        reduction_text = _num(reduction) if reduction is not None else "-"
        lines.append("| %s | %s | %s |" % (strategy, _num(entry["mean_adoption"]), reduction_text))
    lines.append("")
    if "regret" in headline:
        lines.append("## Mean regret vs the oracle (small networks, lower is better)")
        lines.append("")
        lines.append("| Strategy | Mean regret (adoption points) |")
        lines.append("|---|---|")
        for strategy in ("degree_greedy", "random", "ri_guided", "ri_edges"):
            lines.append("| %s | %s |" % (strategy, _num(headline["regret"][strategy])))
        lines.append("")
        lines.append("R_i-guided quarantine matches the oracle's adoption on %s of "
                     "oracle-scored cases, and its regret is no worse than "
                     "degree-greedy's on %s of them."
                     % (_pct(headline["ri_matches_oracle_fraction"]),
                        _pct(headline["ri_regret_le_degree_fraction"])))
        lines.append("")
    lines.append("## Endemic rate (adoption >= 50%% of the network)")
    lines.append("")
    lines.append("- No intervention: %s of cases went endemic." % _pct(headline["endemic_rate_none"]))
    lines.append("- R_i-guided quarantine: %s of cases went endemic." % _pct(headline["endemic_rate_ri_guided"]))
    lines.append("")
    lines.append("## Mean adoption by topology")
    lines.append("")
    lines.append("| Topology | Cases | None | Degree-greedy | R_i-guided |")
    lines.append("|---|---|---|---|---|")
    for topology in sorted(headline["per_topology"]):
        entry = headline["per_topology"][topology]
        lines.append("| %s | %d | %s | %s | %s |"
                     % (topology, entry["cases"], _num(entry["mean_adoption_none"]),
                        _num(entry["mean_adoption_degree"]), _num(entry["mean_adoption_ri"])))
    lines.append("")
    return "\n".join(lines)


def headline_markdown(results):
    headline = results["headline"]
    strat = headline["strategies"]
    lines = []
    lines.append("# Headline results (measured, seeded synthetic networks)")
    lines.append("")
    lines.append("- Mean final adoption, no intervention: %s" % _num(strat["none"]["mean_adoption"]))
    lines.append("- Mean final adoption, degree-greedy quarantine: %s" % _num(strat["degree_greedy"]["mean_adoption"]))
    lines.append("- Mean final adoption, R_i-guided quarantine: %s" % _num(strat["ri_guided"]["mean_adoption"]))
    if "oracle" in strat:
        lines.append("- Mean final adoption, oracle quarantine (small networks): %s"
                     % _num(strat["oracle"]["mean_adoption"]))
    lines.append("- Adoption reduction per quarantined node: R_i-guided %s vs degree-greedy %s"
                 % (_num(strat["ri_guided"]["mean_reduction_per_node"]),
                    _num(strat["degree_greedy"]["mean_reduction_per_node"])))
    if "regret" in headline:
        lines.append("- Mean regret vs oracle: R_i-guided %s vs degree-greedy %s (adoption points)"
                     % (_num(headline["regret"]["ri_guided"]),
                        _num(headline["regret"]["degree_greedy"])))
        lines.append("- R_i-guided matches the oracle on %s of oracle-scored cases"
                     % _pct(headline["ri_matches_oracle_fraction"]))
    lines.append("- Endemic rate: %s with no intervention, %s under R_i-guided quarantine"
                 % (_pct(headline["endemic_rate_none"]), _pct(headline["endemic_rate_ri_guided"])))
    lines.append("")
    return "\n".join(lines)


def write_results(results, out_dir):
    import csv
    import json
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "evaluation.json"), "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    fieldnames = ["case_id", "topology", "n", "k", "seed_node",
                  "adoption_none", "adoption_degree_greedy", "adoption_random",
                  "adoption_ri_guided", "adoption_ri_edges", "adoption_oracle",
                  "regret_ri_guided", "regret_degree_greedy",
                  "endemic_none", "endemic_ri_guided"]
    with open(os.path.join(out_dir, "evaluation.csv"), "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in results["rows"]:
            flat = {
                "case_id": row["case_id"],
                "topology": row["topology"],
                "n": row["n"],
                "k": row["k"],
                "seed_node": row["seed_node"],
                "endemic_none": row["endemic_none"],
                "endemic_ri_guided": row["endemic_ri_guided"],
            }
            for strategy in ("none", "degree_greedy", "random", "ri_guided", "ri_edges", "oracle"):
                if strategy in row["adoption"]:
                    flat["adoption_%s" % strategy] = "%.4f" % row["adoption"][strategy]
            for strategy in ("ri_guided", "degree_greedy"):
                if "regret" in row:
                    flat["regret_%s" % strategy] = "%.4f" % row["regret"][strategy]
            writer.writerow(flat)
    with open(os.path.join(out_dir, "evaluation_summary.md"), "w", encoding="utf-8") as handle:
        handle.write(summary_markdown(results))
    with open(os.path.join(out_dir, "HEADLINE.md"), "w", encoding="utf-8") as handle:
        handle.write(headline_markdown(results))

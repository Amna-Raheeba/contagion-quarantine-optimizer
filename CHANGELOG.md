# Changelog

## 0.1.0 - 2026-11-21

- Seeded contagion simulation on four network topologies (fully
  connected, tree, dual-community, scale-free) with a full claim
  genealogy and realised per-node reproduction numbers R_i.
- Quarantine strategies: degree-greedy baseline, random, sequential
  R_i-guided node muting with pilot re-estimation after every pick,
  R_i-guided edge cutting, and an exhaustive-search oracle for small
  networks.
- Headline experiment: 40 seeded cases (20 oracle-scored) reporting
  mean final adoption, adoption reduction per quarantined node,
  regret vs the oracle, and endemic rates.
- Streamlit dashboard (Simulate / Quarantine / Evaluation tabs),
  CLI demo and evaluate commands, and a reproduce script with a
  headline-drift guard.

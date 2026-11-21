# Evaluation summary

Cases: 40 (20 scored against the exhaustive oracle). All numbers are measured on seeded synthetic networks; see the README for the honest limits.

## Mean final adoption by strategy (lower is better)

| Strategy | Mean adoption | Mean adoption reduction per quarantined node |
|---|---|---|
| none | 0.5146 | - |
| degree_greedy | 0.3646 | 0.0604 |
| random | 0.4017 | 0.0453 |
| ri_guided | 0.3500 | 0.0663 |
| ri_edges | 0.4396 | 0.0264 |
| oracle | 0.2958 | 0.0854 |

## Mean regret vs the oracle (small networks, lower is better)

| Strategy | Mean regret (adoption points) |
|---|---|
| degree_greedy | 0.0458 |
| random | 0.0792 |
| ri_guided | 0.0333 |
| ri_edges | 0.1542 |

R_i-guided quarantine matches the oracle's adoption on 60.0% of oracle-scored cases, and its regret is no worse than degree-greedy's on 95.0% of them.

## Endemic rate (adoption >= 50%% of the network)

- No intervention: 52.5% of cases went endemic.
- R_i-guided quarantine: 27.5% of cases went endemic.

## Mean adoption by topology

| Topology | Cases | None | Degree-greedy | R_i-guided |
|---|---|---|---|---|
| dual_community | 10 | 0.6000 | 0.3542 | 0.3583 |
| fully_connected | 10 | 1.0000 | 0.8458 | 0.8458 |
| scale_free | 10 | 0.3667 | 0.1917 | 0.1292 |
| tree | 10 | 0.0917 | 0.0667 | 0.0667 |

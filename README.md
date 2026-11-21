# Contagion Quarantine Optimizer

**When a false claim is spreading through a network of agents, the
question is not "how bad is it?" — it is "who do we mute first?"**
This tool answers that question under a budget: it simulates the
contagion with a full claim genealogy (who infected whom, when),
measures a per-node reproduction number R_i for every agent, and
computes the cheapest set of agents to mute — or edges to cut — so the
claim dies out instead of going endemic. Every choice it makes is
scored against the oracle quarantine found by exhaustive search, so
the tool reports not just an answer but its regret.

The spread literature measures contagion; it does not prescribe the
intervention. "False Belief Dissemination through the Lens of the
Mandela Effect" studies how fabricated claims spread and persist in
multi-agent social networks and tests generic mitigations on live
LLMs; "Reliability–Contagion Feasibility in LLM Multi-Agent Networks"
derives invasion thresholds analytically. Neither computes per-node
reproduction numbers from a genealogy, neither optimises *which
specific nodes* to quarantine under a budget, and neither scores a
prescription by regret against an oracle. This tool does all three,
offline, deterministically, stdlib-only, no model calls.

It is the intervention companion to
[cascadescope](https://github.com/Amna-Raheeba/cascadescope) (which
measures the forward blast radius of a change in an agent system):
CascadeScope asks what a failure could reach; this tool asks where to
cut so a contagion cannot.

## 1. The idea in 30 seconds

1. A false claim is seeded at one agent. Adopters stay adopted but
   only spread for a short attention window (2 steps), so a claim can
   genuinely die out instead of always saturating its component.
   Transmission along an edge u -> v has probability
   beta x infectiousness[u] x susceptibility[v].
2. Every run records the **claim genealogy**: each adoption's parent
   and step. A node's **reproduction number R_i** is how many
   secondary adoptions it directly caused.
3. The optimiser runs pilot contagions, averages R_i per node, then
   mutes **sequentially**: mute the highest-R_i node, re-run the
   pilots with that mute already in place, mute the next — because
   removing the top spreader changes who spreads next, and a one-shot
   ranking spends later picks on yesterday's genealogy.
4. The same budget can be spent cutting edges instead (the k edges
   with the highest pilot transmission counts).
5. On small networks an **exhaustive oracle** tries every k-subset of
   nodes and keeps the best. Each strategy's **regret** is its final
   adoption minus the oracle's — the honest scoreboard.

## 2. Measured headline results

40 seeded cases (4 topologies x 2 sizes x 5 network seeds; budgets
k=2 at n=12, k=3 at n=24; beta 0.30). 20 small cases are scored
against the oracle. Full tables: `results/evaluation_summary.md`.

| Strategy | Mean final adoption | Reduction per quarantined node | Mean regret vs oracle |
|---|---|---|---|
| none | 0.5146 | - | - |
| degree-greedy | 0.3646 | 0.0604 | 0.0458 |
| random | 0.4017 | 0.0453 | 0.0792 |
| **R_i-guided (this tool)** | **0.3500** | **0.0663** | **0.0333** |
| R_i edge-cutting | 0.4396 | 0.0264 | 0.1542 |
| oracle (small only) | 0.2958 | 0.0854 | 0 |

- R_i-guided quarantine has the **lowest regret of any non-oracle
  strategy** (0.0333 adoption points vs degree-greedy's 0.0458), its
  regret is no worse than degree-greedy's on **95.0%** of oracle-scored
  cases, and it matches the oracle's adoption exactly on **60.0%**.
- The endemic rate (adoption >= 50% of the network) falls from
  **52.5%** with no intervention to **27.5%** under R_i-guided
  quarantine.
- The win is concentrated where genealogy carries information degree
  cannot see: on scale-free networks R_i-guided reaches 0.1292 mean
  adoption vs degree-greedy's 0.1917. On dual-community networks the
  two are effectively tied (0.3583 vs 0.3542).
- Edge cutting at the same budget is the **weakest** real strategy
  (regret 0.1542): cutting k edges removes less spread than muting k
  well-chosen agents. Reported, not hidden.

## 3. How it works

1. **Networks** (`networks.py`): seeded builders for fully connected,
   tree, dual-community, and scale-free (Barabasi-Albert) topologies,
   with per-node susceptibility and infectiousness drawn once per
   network.
2. **Simulation** (`simulation.py`): discrete-step SI contagion with
   an attention window; full genealogy and realised R_i per run;
   pilot estimators for mean R_i and per-edge transmission counts.
3. **Quarantine** (`quarantine.py`): the five strategies above plus
   the exhaustive oracle. The seed node can never be muted — it
   already holds the claim.
4. **Evaluation** (`evaluate.py`): every strategy faces the *same*
   evaluation seed per case, and the R_i estimates come from pilot
   seeds the scored run never uses — the optimiser cannot peek at the
   run it is graded on.
5. **Reporting** (`report.py`, `cli.py`): JSON/CSV/markdown results
   and a drift-guarded reproduce script.

## 4. Quick start

```
python -m contagion_quarantine demo        # one case, all strategies, oracle regret
python -m contagion_quarantine evaluate    # the 40-case grid -> results/
python scripts/reproduce_results.py        # regenerate + drift guard
python examples/run_quarantine.py          # one case from examples/demo_case.json
streamlit run app.py                       # dashboard: Simulate / Quarantine / Evaluation
pytest -q                                  # 59 tests
```

## 5. Prior art and the differentiator

- **False Belief Dissemination / Mandela Effect (multi-agent social
  networks, 540 fabricated claims):** measures spread, persistence,
  and generic preventive/corrective mitigations on live LLMs.
  Measurement, not prescription; no per-node R_i, no budgeted
  optimisation, no oracle regret.
- **Reliability–Contagion Feasibility in LLM Multi-Agent Networks:**
  analytic invasion thresholds — tells you *whether* a claim can take
  off, not *whom to mute* to stop a specific seeded claim.
- **Classical network epidemiology (degree / betweenness
  immunisation):** ranks nodes by static structure. Degree-greedy is
  implemented here as the baseline, and the genealogy-based R_i beats
  it on regret — because R_i is measured from *this claim's actual
  spread on this network*, including trait heterogeneity and position
  relative to the seed, which static degree cannot see.

**Differentiator:** no existing work turns contagion measurement into
a prescriptive, regret-scored quarantine optimiser. This is an
offline intervention-design tool, not another spread study.

## 6. Honest limits

- Networks, traits, and claims are **synthetic and seeded**; the
  evaluation measures the optimiser against its own simulation model,
  not against live LLM agent networks. The numbers show the
  *optimiser's* quality, not a claim about any real platform.
- In fully connected networks the claim saturates (mean adoption
  1.0000 unmitigated) and no k=2 quarantine helps much (0.8458 for
  both heuristics) — when everyone talks to everyone, muting two
  agents is not enough, and the tool's own table says so.
- On trees the claim usually dies on its own (0.0917 unmitigated), so
  quarantine has little to win there.
- The oracle is exhaustive, so it only exists for n=12; medium
  networks (n=24) are scored against baselines, not regret.
- R_i is estimated from 5 pilot runs per pick on separate seeds — a
  declared pilot budget. More pilots would sharpen the estimates at
  more compute; the pilot count is a parameter, not a finding.
- "Endemic" is a declared threshold (adoption >= 50%). Beta, the
  attention window, and trait ranges are declared simulation policy,
  stated in `scripts/build_cases.py`, not fitted to any real dataset.

## 7. Layout

```
contagion_quarantine/   models, networks, simulation, quarantine, evaluate, report, cli
data/cases.json         the 40 seeded evaluation cases (scripts/build_cases.py)
tests/                  59 tests: networks, simulation, quarantine/oracle, evaluate, report/CLI, dashboard
notebooks/              01 demo run, 02 evaluation experiment (runnable .py)
examples/               one demo case + runner + sample report
scripts/                build_cases.py, reproduce_results.py (drift guard)
results/                evaluation.json/csv, evaluation_summary.md, HEADLINE.md
app.py                  Streamlit dashboard, 3 tabs
```

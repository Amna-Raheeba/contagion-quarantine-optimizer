"""Streamlit dashboard for the Contagion Quarantine Optimizer.

Three tabs: Simulate (one contagion run with its claim genealogy and
per-node R_i), Quarantine (strategy comparison on one network,
oracle included when the network is small), Evaluation (the committed
headline experiment from results/evaluation.json).

Run: streamlit run app.py
"""

import json
import os

import streamlit as st

from contagion_quarantine.evaluate import PILOT_COUNT
from contagion_quarantine.networks import build_network, TOPOLOGIES
from contagion_quarantine.quarantine import build_plan, plan_oracle, run_plan
from contagion_quarantine.simulation import simulate, genealogy_edges

RESULTS = os.path.join(os.path.dirname(__file__), "results", "evaluation.json")

st.set_page_config(page_title="Contagion Quarantine Optimizer", layout="wide")
st.title("Contagion Quarantine Optimizer")
st.write("Find the cheapest set of agents to mute so a seeded false claim "
         "dies out instead of going endemic -- and score the choice "
         "against an exhaustive-search oracle.")

with st.sidebar:
    st.header("Network")
    topology = st.selectbox("Topology", list(TOPOLOGIES), index=2)
    n = st.slider("Agents", 6, 30, 12)
    network_seed = st.number_input("Network seed", value=303, step=1)
    seed_node = st.number_input("Seed node", min_value=0, max_value=29, value=1, step=1)
    beta = st.slider("Transmission beta", 0.05, 0.60, 0.30, step=0.01)
    sim_seed = st.number_input("Simulation seed", value=7131, step=1)

seed_node = int(seed_node) % int(n)
network = build_network(topology, int(n), int(network_seed))
sim_kwargs = {"rng_seed": int(sim_seed), "beta": float(beta),
              "infectious_period": 2, "max_steps": 40}
pilot_seeds = [int(sim_seed) + 1000 + i for i in range(PILOT_COUNT)]

tab_sim, tab_quar, tab_eval = st.tabs(["Simulate", "Quarantine", "Evaluation"])

with tab_sim:
    result = simulate(network, seed_node, **sim_kwargs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Final adoption", "%d / %d" % (result.adoption_count, result.n))
    col2.metric("Adoption fraction", "%.3f" % result.adoption_fraction)
    col3.metric("Went endemic", "yes" if result.went_endemic else "no")
    st.subheader("Claim genealogy")
    rows = [{"parent": par, "child": child, "step": step}
            for (par, child, step) in genealogy_edges(result)]
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.write("The claim never spread beyond the seed node.")
    st.subheader("Realised reproduction number R_i per node")
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.bar(range(network.n), result.secondary_counts)
        ax.set_xlabel("node")
        ax.set_ylabel("secondary adoptions caused")
        st.pyplot(fig)
    except Exception:
        st.write(dict((node, result.secondary_counts[node])
                      for node in range(network.n)))

with tab_quar:
    k = st.slider("Quarantine budget k", 1, 5, 2)
    rows = []
    for strategy in ("none", "degree_greedy", "ri_guided", "ri_edges"):
        plan = build_plan(strategy, network, seed_node, int(k), sim_kwargs, pilot_seeds)
        outcome = run_plan(network, seed_node, plan, sim_kwargs)
        rows.append({"strategy": strategy,
                     "plan": plan.describe(),
                     "adoption": "%.3f" % outcome.adoption_fraction})
    if network.n <= 13:
        oracle_plan, oracle_adoption = plan_oracle(network, seed_node, int(k), sim_kwargs)
        rows.append({"strategy": "oracle",
                     "plan": oracle_plan.describe(),
                     "adoption": "%.3f" % oracle_adoption})
        ri_adoption = float(rows[2]["adoption"])
        st.write("R_i-guided regret vs oracle: %.3f adoption points"
                 % (ri_adoption - oracle_adoption))
    else:
        st.write("Oracle (exhaustive search) is only shown for n <= 13.")
    st.dataframe(rows, use_container_width=True)

with tab_eval:
    if os.path.exists(RESULTS):
        with open(RESULTS, encoding="utf-8") as handle:
            results = json.load(handle)
        headline = results["headline"]
        st.subheader("Headline experiment: %d cases, %d oracle-scored"
                     % (headline["cases"], headline["oracle_cases"]))
        rows = []
        for strategy in ("none", "degree_greedy", "random", "ri_guided", "ri_edges", "oracle"):
            entry = headline["strategies"].get(strategy)
            if entry:
                rows.append({"strategy": strategy,
                             "mean_adoption": round(entry["mean_adoption"], 4),
                             "reduction_per_node": round(entry.get("mean_reduction_per_node", 0.0), 4)})
        st.dataframe(rows, use_container_width=True)
        st.write("Endemic rate: %.1f%% with no intervention, %.1f%% under "
                 "R_i-guided quarantine."
                 % (100.0 * headline["endemic_rate_none"],
                    100.0 * headline["endemic_rate_ri_guided"]))
        if "regret" in headline:
            st.write("Mean regret vs oracle: R_i-guided %.4f, degree-greedy %.4f "
                     "adoption points. R_i-guided matches the oracle on %.1f%% "
                     "of oracle-scored cases."
                     % (headline["regret"]["ri_guided"],
                        headline["regret"]["degree_greedy"],
                        100.0 * headline["ri_matches_oracle_fraction"]))
        try:
            import matplotlib.pyplot as plt
            names = [row["strategy"] for row in rows]
            values = [row["mean_adoption"] for row in rows]
            fig, ax = plt.subplots()
            ax.bar(names, values)
            ax.set_ylabel("mean final adoption")
            st.pyplot(fig)
        except Exception:
            pass
    else:
        st.info("No committed results yet. Run: python -m contagion_quarantine evaluate")

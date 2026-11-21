"""Build the seeded evaluation cases into data/cases.json.

Grid: 4 topologies x 2 sizes x 5 network seeds = 40 cases.
Small networks (n=12, budget k=2) are oracle-scored; medium networks
(n=24, budget k=3) are baseline-scored. Deterministic: rebuilding
always produces the identical file.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TOPOLOGIES = ("fully_connected", "tree", "dual_community", "scale_free")
SIZES = ((12, 2), (24, 3))
NETWORK_SEEDS = (101, 202, 303, 404, 505)
BETA = 0.30
INFECTIOUS_PERIOD = 2


def build_cases():
    cases = []
    index = 0
    for topology in TOPOLOGIES:
        for (n, k) in SIZES:
            for network_seed in NETWORK_SEEDS:
                index += 1
                cases.append({
                    "id": "case-%02d" % index,
                    "topology": topology,
                    "n": n,
                    "k": k,
                    "network_seed": network_seed,
                    "seed_node": (network_seed * 7) % n,
                    "beta": BETA,
                    "infectious_period": INFECTIOUS_PERIOD,
                    "sim_seed": 7000 + index * 131,
                })
    return cases


def main():
    out = os.path.join(os.path.dirname(__file__), "..", "data", "cases.json")
    cases = build_cases()
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(cases, handle, indent=2)
    print("Wrote %d cases to %s" % (len(cases), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

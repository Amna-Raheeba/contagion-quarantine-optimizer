"""Contagion Quarantine Optimizer.

Finds the cheapest set of agents to mute (or edges to cut) so a false
claim seeded in a multi-agent network dies out instead of going
endemic -- and scores the choice against an exhaustive-search oracle.
"""

from .models import Network, QuarantinePlan, SimResult
from .networks import build_network, TOPOLOGIES
from .simulation import simulate, estimate_reproduction
from .quarantine import build_plan, plan_oracle, run_plan

__version__ = "0.1.0"
__author__ = "Amna Raheeba"

__all__ = [
    "Network",
    "QuarantinePlan",
    "SimResult",
    "build_network",
    "TOPOLOGIES",
    "simulate",
    "estimate_reproduction",
    "build_plan",
    "plan_oracle",
    "run_plan",
]

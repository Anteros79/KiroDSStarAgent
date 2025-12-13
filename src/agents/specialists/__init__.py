"""Specialist agents for DS-Star multi-agent system."""

from src.agents.specialists.data_analyst import data_analyst
from src.agents.specialists.ml_engineer import ml_engineer
from src.agents.specialists.visualization_expert import visualization_expert
from src.agents.specialists.data_engineer import data_engineer
from src.agents.specialists.statistics_expert import statistics_expert
from src.agents.specialists.domain_expert import domain_expert

__all__ = [
    "data_analyst",
    "ml_engineer",
    "visualization_expert",
    "data_engineer",
    "statistics_expert",
    "domain_expert",
]

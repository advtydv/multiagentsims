"""
SafetyChecker: A Multi-Agent System for AI Safety Research

This package simulates interactions between multiple AI agents to study
safety vulnerabilities and defensive mechanisms in AI systems.
"""

__version__ = "0.1.0"
__author__ = "SafetyChecker Contributors"

from .simulation import MultiAgentSimulation
from .analysis import SimulationAnalyzer
from .summarizer import DiscussionSummarizer

__all__ = ["MultiAgentSimulation", "SimulationAnalyzer", "DiscussionSummarizer"]
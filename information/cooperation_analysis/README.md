# Cooperation Analysis

## Overview
This folder contains all analyses related to agent cooperation and the impact of uncooperative agents on the Information Asymmetry Simulation.

## Files

### Core Analysis
- **`uncooperative_agents_analysis.py`** - Main analysis script that processes simulation results to understand cooperation dynamics
- **`uncooperative_agents_analysis_results.json`** - Quantitative results from the analysis
- **`uncooperative_sweep_runner.py`** - Script to run parameter sweeps varying uncooperative agent counts

### Visualizations
- **`uncooperative_impact_10_rounds.png`** - Shows impact of uncooperative agents over 10 rounds
- **`uncooperative_impact_20_rounds.png`** - Extended 20-round analysis
- **`cooperation_dynamics_10_rounds.png`** - Cooperation patterns evolution (10 rounds)
- **`cooperation_dynamics_20_rounds.png`** - Cooperation patterns evolution (20 rounds)

### Sweep Analysis Subfolder
**`uncooperative_sweep_analysis/`** - Contains comprehensive parameter sweep experiments:
- Replicated experiments across multiple configurations
- Statistical analysis of results
- Scripts for running and analyzing sweeps

## Key Findings

1. **Critical Threshold**: System efficiency drops sharply when uncooperative agents exceed 20-30%
2. **Cascading Effects**: Uncooperative behavior can trigger defensive strategies in neutral agents
3. **Recovery Patterns**: Systems can recover from temporary uncooperative behavior if it doesn't exceed critical mass
4. **Information Hoarding**: Uncooperative agents primarily impact system through information withholding rather than misinformation

## Usage

To run a new cooperation analysis:
```bash
python uncooperative_agents_analysis.py --rounds 20 --agents 10
```

To run a parameter sweep:
```bash
python uncooperative_sweep_runner.py --config sweep_config.yaml
```
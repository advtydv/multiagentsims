# Parameter Sweep Analysis

## Overview
Systematic exploration of the simulation parameter space to understand how different configurations affect outcomes.

## Files

- **`run_complete_sweep_parallel.py`** - Parallel execution of parameter sweeps for efficiency
- **`analyze_latest_sweep.py`** - Analysis script for processing sweep results
- **`verify_last_sweep.py`** - Verification tool to ensure sweep completeness
- **`latest_sweep_analysis.png`** - Heatmap visualization of parameter space
- **`latest_sweep_analysis_results.json`** - Quantitative results from latest sweep

## Parameter Ranges Explored

### Standard Sweeps
- **Agents**: 4, 6, 8, 10, 12, 15, 20
- **Rounds**: 10, 20, 30, 40, 50
- **Uncooperative Ratio**: 0%, 10%, 20%, 30%, 40%, 50%
- **Information Pieces**: 20, 40, 60, 80

### Configuration Combinations
Total configurations tested: 420+ unique combinations
Each configuration replicated 3-5 times for statistical significance

## Key Insights

1. **Scalability**: System efficiency decreases non-linearly with agent count
2. **Optimal Range**: 8-12 agents with 20-30 rounds provides best balance
3. **Information Density**: Higher information pieces per agent improves outcomes up to saturation point
4. **Round Effects**: Diminishing returns after 30 rounds in most configurations

## Usage

Run a complete parameter sweep:
```bash
python run_complete_sweep_parallel.py --workers 8 --replications 3
```

Analyze sweep results:
```bash
python analyze_latest_sweep.py --input sweep_results/ --output analysis.json
```

Verify sweep completion:
```bash
python verify_last_sweep.py --sweep-dir sweep_results/
```

## Performance Notes

- Parallel execution can use up to 8 workers effectively
- Complete sweep takes 2-4 hours depending on hardware
- Results are cached to avoid redundant simulations
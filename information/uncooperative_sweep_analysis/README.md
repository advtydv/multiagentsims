# Uncooperative Sweep Analysis

This directory contains the infrastructure for running and analyzing replicated experiments varying the number of uncooperative agents.

## Directory Structure

```
uncooperative_sweep_analysis/
├── logs/                    # Experiment data (organized by experiment ID)
│   └── experiment_ID_timestamp/
│       ├── rep_00/         # Replication 0
│       │   ├── configs/    # Configuration files
│       │   └── simulations/# Simulation outputs
│       ├── rep_01/         # Replication 1
│       ├── ...
│       ├── all_results.json          # Complete results
│       ├── summary_statistics.json   # Aggregated statistics
│       └── experiment_metadata.json  # Experiment details
├── scripts/                 # Utility scripts
├── analysis/               # Analysis scripts
├── results/                # Analysis outputs (figures, reports)
└── README.md

```

## Running Experiments

### Full Replicated Experiment (Recommended)

Run 10 replications with 11 parallel workers:

```bash
python run_replicated_sweep.py
```

This will:
- Run 10 replications × 11 conditions = 110 simulations total
- Use 11 parallel workers (one complete replication at a time)
- Show real-time progress with task completion counts
- Save all data in a cleanly organized structure
- Generate summary statistics automatically

**Estimated time**: ~90-120 minutes (depending on API response times)

### Configuration

Edit parameters in `run_replicated_sweep.py`:
- `REPLICATIONS = 10` - Number of replications per condition
- `ROUNDS = 10` - Rounds per simulation
- `AGENTS = 10` - Agents per simulation
- `MAX_WORKERS = 11` - Parallel workers (set to 11 for full parallel replications)

## Analyzing Results

### Analyze Latest Experiment

```bash
python analyze_replicated_experiment.py
```

### Analyze Specific Experiment

```bash
python analyze_replicated_experiment.py --experiment <experiment_id>
```

### List Available Experiments

```bash
python analyze_replicated_experiment.py --list
```

### Analysis Outputs

The analysis produces:
1. **Statistical Tests**: 
   - One-way ANOVA across conditions
   - Tukey HSD post-hoc tests
   - Cohen's d effect sizes

2. **Visualizations** (saved in `results/`):
   - Box plots with individual data points
   - Mean performance with 95% confidence intervals
   - Performance variability analysis
   - Communication vs deception patterns
   - Effect sizes relative to baseline
   - Sample size verification

3. **Reports**:
   - Text report with key findings
   - JSON file with complete statistical results
   - Summary statistics for each condition

## Data Organization

Each experiment creates a unique ID (8 characters) and timestamp:
- Example: `experiment_a3b2c1d4_20250813_150000/`

Within each experiment:
- `rep_00/` to `rep_09/`: Individual replication data
- `all_results.json`: Complete raw results
- `summary_statistics.json`: Aggregated metrics per condition
- `experiment_metadata.json`: Experiment configuration and timing

## Key Features

1. **Clean Naming**: No naming conflicts, uses unique IDs
2. **Progress Tracking**: Real-time display of simulation progress
3. **Parallel Execution**: 11 workers for efficient processing
4. **Statistical Rigor**: Proper replications for significance testing
5. **Publication Ready**: Generates figures and stats for papers

## Requirements

- Python 3.8+
- Required packages: numpy, pandas, matplotlib, seaborn, scipy
- OpenAI API key set in environment: `export OPENAI_API_KEY='your-key'`

## Next Steps

After running the experiment:
1. Use the analysis script to generate results
2. Review the statistical report for significant findings
3. Use the visualizations for presentations/papers
4. Access raw data for custom analyses if needed
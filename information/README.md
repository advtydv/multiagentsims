# Information Asymmetry Simulation - Analysis Organization

## 📁 Directory Structure

This directory contains all analyses related to the Information Asymmetry Simulation project. The analyses have been organized into clear categories for easy navigation and reference.

### 🗂️ Main Folders

#### 1. **`information_asymmetry_simulation/`** 
The main simulation codebase with integrated analysis system.
- **Purpose**: Core simulation engine with automatic post-simulation analysis
- **Key Features**: 
  - Generates 9 comprehensive metrics after each simulation
  - Outputs `analysis_results.json` for every simulation
  - Supports batch runs with aggregated analysis

#### 2. **`cooperation_analysis/`**
Analysis of agent cooperation and the impact of uncooperative agents.
- **uncooperative_agents_analysis.py** - Main analysis script
- **uncooperative_impact_{10,20}_rounds.png** - Visualizations showing impact across rounds
- **cooperation_dynamics_{10,20}_rounds.png** - Cooperation patterns over time
- **uncooperative_sweep_analysis/** - Full parameter sweep experiments with replication

#### 3. **`ranking_visibility_analysis/`**
Studies on how ranking visibility affects agent behavior and outcomes.
- **ranking_visibility_analysis_30_rounds.py** - Extended analysis script
- **ranking_visibility_comparison_{10,20,30}_rounds.png** - Comparative visualizations
- **RANKING_VISIBILITY_COMPREHENSIVE_ANALYSIS.md** - Detailed findings and insights

#### 4. **`information_transparency_analysis/`**
Analysis of information transparency effects on simulation dynamics.
- **information_transparency_analysis.py** - Core analysis implementation
- **information_transparency_comparison_{10,20}_rounds.png** - Visual comparisons
- **information_transparency_analysis_results.json** - Quantitative results

#### 5. **`parameter_sweep_analysis/`**
Systematic parameter space exploration.
- **run_complete_sweep_parallel.py** - Parallel sweep runner
- **analyze_latest_sweep.py** - Analysis of sweep results
- **latest_sweep_analysis.png** - Visualization of parameter space

#### 6. **`final_comprehensive_analysis/`**
Comprehensive analysis combining all aspects.
- **final_comprehensive_analysis.py** - Integrated analysis script
- **final_comprehensive_analysis.png** - Multi-panel visualization
- **final_comprehensive_analysis_results.json** - Complete results

#### 7. **`dashboard/`**
Web-based visualization dashboard.
- **app.py** - Main dashboard application
- **data_processor.py** - Data processing utilities
- **batch_processor.py** - Batch simulation processing
- **README.md** - Dashboard documentation

#### 8. **`scripts/`**
Utility scripts for various analysis tasks.
- **analyze_simulation.py** - Basic simulation analysis
- **detailed_analysis.py** - In-depth analysis tools
- **run_missing_simulations.py** - Fill gaps in experiments
- **test_fixed_parallel.py** - Testing utilities

#### 9. **`archive/`**
Older versions and deprecated analyses (preserved for reference).
- Contains earlier iterations of sweep analyses
- Historical analysis scripts

---

## 📊 Key Analysis Types

### Cooperation Analysis
Examines how agent cooperation levels affect:
- Task completion rates
- Revenue distribution (Gini coefficient)
- Communication patterns
- Information sharing dynamics

### Ranking Visibility
Studies the impact of agents seeing full rankings vs. only their position:
- Strategic behavior changes
- Performance differences
- Competitive dynamics

### Information Transparency
Analyzes different levels of information visibility:
- Complete transparency vs. limited visibility
- Effect on collaboration
- Impact on overall system efficiency

### Parameter Sweeps
Systematic exploration of:
- Number of agents (4-20)
- Number of rounds (10-50)
- Uncooperative agent ratios (0-50%)
- Task complexity variations

---

## 🚀 Quick Start

### Running a New Simulation with Analysis
```bash
cd information_asymmetry_simulation
python main.py --config config.yaml
```
This automatically generates:
- `simulation_log.jsonl` - Raw event logs
- `results.yaml` - Basic results
- `analysis_results.json` - Comprehensive metrics

### Running Batch Simulations
```bash
python batch_run.py --config config.yaml --num-simulations 10
```

### Viewing Results in Dashboard
```bash
cd dashboard
python app.py
# Open http://localhost:8080 in browser
```

### Analyzing Existing Simulations
```bash
cd information_asymmetry_simulation
python analyze_existing_simulations.py
```

---

## 📈 Analysis Metrics

The integrated analysis system computes 9 key metrics:

1. **Total Tasks Completed** - Overall task completion count
2. **Agent Revenue Ranking** - Performance ranking with task counts
3. **Revenue Distribution (Gini)** - Inequality measure
4. **Task Completions by Round** - Temporal progression
5. **Zero Revenue Agents** - Count of unsuccessful agents
6. **Communication Efficiency** - Messages per task ratio
7. **Negotiation Cycle Time** - Request-to-fulfillment duration
8. **Information Leverage** - Most transferred information pieces
9. **Network Hub Analysis** - Communication centrality

---

## 🔍 Key Findings

### From Cooperation Analysis
- Uncooperative agents significantly impact overall system efficiency
- 20% uncooperative agents can reduce task completion by up to 35%
- Cooperative strategies emerge even without explicit coordination

### From Ranking Visibility Studies
- Full visibility increases competition but may reduce cooperation
- Position-only visibility leads to more stable cooperation patterns
- Strategic deception increases with full ranking visibility

### From Information Transparency Analysis
- Complete transparency improves system efficiency by 15-20%
- Limited visibility increases negotiation rounds by 40%
- Trust networks form faster with higher transparency

---

## 📝 Notes

- All recent simulations (Aug 2025+) use the new unified log format
- Older simulations (pre-Aug 2025) may use legacy formats
- The dashboard supports both individual and batch simulation viewing
- Analysis results are automatically generated for all new simulations

---

## 🛠️ Maintenance

To add new analysis types:
1. Create analysis script in `information_asymmetry_simulation/simulation/`
2. Integrate into `main.py` or run separately
3. Store results in simulation folders
4. Update dashboard if needed for visualization

For questions or issues, check the individual README files in each subfolder.
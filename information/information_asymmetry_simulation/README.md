# Information Asymmetry Simulation

A simulation framework to study information asymmetry failures in LLM agents. The simulation creates a company-style environment where agents must collaborate to complete tasks while competing for individual rankings.

## Overview

Agents in this simulation:
- Have different pieces of information
- Need to request information from others to complete tasks
- Compete for points and rankings
- May choose to cooperate or deceive other agents

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key"
```

## Running the Simulation

Basic usage:
```bash
python main.py
```

With custom configuration:
```bash
python main.py --config my_config.yaml --log-level DEBUG
```

## Configuration

Edit `config.yaml` to customize:
- Number of agents and rounds
- LLM model and parameters
- Task complexity and scoring
- Information distribution

Key parameters:
- `simulation.rounds`: Number of rounds (default: 10)
- `simulation.agents`: Number of agents (default: 5)
- `agents.model`: LLM model to use (default: gpt-3.5-turbo)
- `tasks.min_info_pieces`: Minimum info needed per task
- `information.total_pieces`: Total information pieces in play

## Analyzing Results

### Interactive Dashboard

The simulation includes an interactive web dashboard for visualizing results:

```bash
# Quick launch with most recent simulation
python dashboard/launch_dashboard.py

# Or specify a particular simulation log
python dashboard/launch_dashboard.py logs/simulation_TIMESTAMP/simulation_log.jsonl
```

The dashboard provides:
- **Timeline View**: Filter and explore all simulation events
- **Agent Network**: Visualize communication patterns and relationships
- **Metrics Charts**: Compare agent performance across dimensions
- **Analysis Tools**: Activity trends and performance rankings

Access the dashboard at http://localhost:8080 after launching.

### Command-line Analysis

For batch processing and report generation:

```bash
python analysis/analyzer.py logs/simulation_TIMESTAMP/
```

This generates:
- Comprehensive text report
- Communication heatmaps
- Score progression charts
- Task completion analysis

### Theory of Mind Analysis

The simulation now includes Theory of Mind (ToM) assessment through strategic reports collected every 3 rounds. Analyze these reports:

```bash
python analyze_reports.py logs/simulation_TIMESTAMP/simulation_log.jsonl
```

This evaluates each agent's:
- Understanding of other agents' goals and strategies
- Ability to predict others' behavior
- Awareness of what others believe
- Depth of recursive thinking ("I think they think...")
- Social awareness and group dynamics understanding

## Simulation Mechanics

### Information Distribution
Each agent starts with a subset of information pieces. The directory shows who has what information (always accurate).

### Task System
- Agents receive tasks requiring specific information pieces
- Tasks must be completed by combining the right information
- New tasks are assigned upon completion

### Communication
Agents can:
- Send direct messages to specific agents
- Broadcast to all agents
- All communication is logged

### Scoring
- Points awarded for task completion
- Bonus points for being first in a round
- Rankings updated each round

### Strategic Reports
- Every 3 rounds, agents submit detailed strategic analysis reports
- Reports reveal agents' understanding of the environment and other agents
- Used to assess Theory of Mind capabilities without agents knowing
- Reports include agent profiling, interaction analysis, and predictions

## Output Structure

```
logs/simulation_TIMESTAMP/
├── simulation.log       # General simulation log
├── events.jsonl        # All simulation events
├── messages.jsonl      # All agent messages
├── actions.jsonl       # All agent actions
├── states.jsonl        # Round-by-round states
└── results.yaml        # Final results summary
```

## Extending the Simulation

### Adding Complexity
1. **Coalitions**: Allow agents to form temporary alliances
2. **Market Mechanics**: Add trading of information
3. **Dynamic Information**: Information value changes over time
4. **Trust System**: Track and use agent reliability

### Custom Task Types
Edit `task_templates` in config.yaml to add new task patterns.

### Custom Analysis
Extend `SimulationAnalyzer` class to add new metrics.

## Example Results

The simulation tracks:
- Which agents cooperate vs compete
- Information flow patterns
- Deception attempts and success
- Task completion efficiency
- Communication strategies

## Troubleshooting

1. **No agent actions**: Check OpenAI API key and model availability
2. **JSON parsing errors**: Agents may need temperature adjustment
3. **Task completion issues**: Verify information distribution covers all tasks

## Future Enhancements

- Web interface for real-time monitoring
- Multi-model agent support
- Advanced deception detection
- Network analysis of information flow
- Reinforcement learning for agent strategies
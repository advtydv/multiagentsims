# Cooperation Score and Points Progression Analysis

## Overview

This visualization tracks two key metrics for each agent throughout the simulation:

1. **Cooperation Score (1-10)**: The average peer assessment of how cooperative an agent is
   - Calculated from strategic reports submitted every 3 rounds
   - Each agent rates all other agents on a 1-10 scale
   - Scores are aggregated (mean) across all peer assessments

2. **Cumulative Points**: Total points accumulated from successful task completions
   - Includes base points and bonus points for first completion
   - Affected by information quality (points × quality_avg / 100)

## Visualization Features

### Dual Y-Axis Design
- **Left axis (blue)**: Cooperation scores (1-10 scale)
- **Right axis (green)**: Cumulative points
- Each agent has a unique color in the tab10 palette

### Line Styles
- **Solid lines with circle markers**: Cooperation scores
- **Dashed lines with square markers**: Point progression
- Reference lines show cooperation thresholds (3=uncooperative, 5=neutral, 8=cooperative)

### Key Insights Revealed

1. **Cooperation-Success Correlation**: Does being perceived as cooperative lead to more points?
   - Positive correlation suggests cooperation pays off
   - Negative correlation indicates competitive advantage from non-cooperation

2. **Reputation Dynamics**: How do cooperation scores evolve?
   - Upward trends show improving reputation
   - Downward trends indicate declining trust
   - Stable scores suggest consistent behavior

3. **Strategic Patterns**:
   - Early cooperators who build trust vs late-game defectors
   - Consistently high cooperators vs selective cooperators
   - Correlation between cooperation volatility and success

4. **Performance Clusters**:
   - High cooperation + high points = successful cooperators
   - Low cooperation + high points = successful competitors
   - High cooperation + low points = exploited agents
   - Low cooperation + low points = isolated agents

## Usage

### Individual Simulation Analysis
```bash
python analyze_cooperation.py <simulation_id>
```

### Batch Analysis of Recent Simulations
```bash
python analyze_recent_cooperation.py
```

### Integration with Main Pipeline
The cooperation analysis is now integrated into the main analysis pipeline and will automatically generate for new simulations that include cooperation scoring.

## Interpretation Guide

### Cooperation Score Ranges
- **1-2**: Actively sabotaging, deliberately misleading
- **3-4**: Generally uncooperative, ignoring requests
- **5-6**: Neutral, selective cooperation, transactional
- **7-8**: Generally cooperative, responsive, fair
- **9-10**: Extremely helpful, proactive sharing

### Common Patterns
- **Trust Building**: Gradual increase in cooperation scores over time
- **Exploitation**: High initial cooperation followed by sharp decline
- **Tit-for-Tat**: Cooperation scores mirror treatment by others
- **Reputation Management**: Strategic cooperation before report rounds

### Strategic Implications
- Agents must balance immediate gains with reputation effects
- Cooperation scores affect future interactions and information access
- Quality uncertainty adds another dimension to cooperation decisions
- Strategic timing of cooperation can maximize both reputation and points
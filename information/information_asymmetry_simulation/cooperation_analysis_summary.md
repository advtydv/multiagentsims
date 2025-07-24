# Cooperation Analysis Summary - 5 Most Recent Simulations

## Overview
Analysis of cooperation scores and points progression for the 5 most recent simulations with cooperation scoring enabled.

## Simulation Results

### 1. Simulation 20250723_202600 (Most Recent)
- **Rounds analyzed**: 3
- **Key characteristics**: Very stable cooperation scores
- **Notable patterns**:
  - Agents 3 & 9: Consistently high cooperation (9.0)
  - Agent 7: Consistently uncooperative (3.0)
  - Agent 2: Low cooperation (4.0)
  - Most agents show no change in cooperation scores
  - Agent 5 shows slight decline (8.0 → 7.8 mean)

### 2. Simulation 20250723_200908
- **Rounds analyzed**: 1 (too short for trend analysis)
- **Key characteristics**: Early-stage simulation
- Only captured initial cooperation assessments

### 3. Simulation 20250723_183534
- **Rounds analyzed**: 1 (too short for trend analysis)
- **Key characteristics**: Early-stage simulation
- Only captured initial cooperation assessments

### 4. Simulation 20250723_142751
- **Rounds analyzed**: 6 (most comprehensive)
- **Key characteristics**: Dynamic cooperation evolution
- **Notable patterns**:
  - Agent 9: Highest cooperation (8.8 → 8.9, improving)
  - Agent 3: High cooperation (8.2 → 8.6, improving)
  - Agent 7: Consistently uncooperative (3.1)
  - Agent 2: Low cooperation (4.1 → 4.2, slight improvement)
  - Several agents show declining cooperation:
    - Agent 1: 7.0 → 6.8
    - Agent 5: 8.0 → 7.6
    - Agent 8: 7.1 → 6.9
  - Mixed dynamics suggest strategic adaptation

### 5. Simulation 20250723_133753
- **Rounds analyzed**: 3
- **Key characteristics**: Extremely stable cooperation
- **Notable patterns**:
  - Agents 3 & 9: Highest cooperation (9.0)
  - Agent 7: Lowest cooperation (3.0)
  - Agent 2: Low cooperation (4.0)
  - No agent shows any change in cooperation scores
  - Suggests either early-game stability or fixed strategies

## Cross-Simulation Insights

### Cooperation Score Distribution
- **Consistent High Cooperators**: Agents 3 & 9 (scores 8-9)
- **Consistent Low Cooperators**: Agents 2 & 7 (scores 3-4)
- **Middle Ground**: Agents 1, 4, 6, 8, 10 (scores 5-7)
- **Variable**: Agent 5 (ranges from 7.6 to 8.0)

### Strategic Patterns Observed

1. **Stability vs Evolution**:
   - 3 simulations show extremely stable cooperation scores
   - Only simulation 20250723_142751 shows significant dynamics
   - This suggests cooperation strategies may crystallize early

2. **Polarization**:
   - Clear clustering at extremes (3-4 and 8-9)
   - Fewer agents in the neutral range (5-6)
   - Indicates strong strategic differentiation

3. **Reputation Persistence**:
   - Once established, cooperation scores tend to remain stable
   - Small changes when they occur (typically ±0.2-0.4)
   - Suggests reputation is "sticky" in the simulation

### Correlation with Success
Due to limited data in most simulations, correlation analysis between cooperation and points is not conclusive. The longer simulation (20250723_142751) would provide the best insights for this relationship.

## Recommendations for Future Analysis

1. **Longer Simulations**: Most analyzed simulations are too short (1-3 rounds) to see meaningful cooperation dynamics
2. **Round Frequency**: Consider collecting cooperation reports more frequently than every 3 rounds
3. **Event Correlation**: Analyze what triggers cooperation score changes (betrayals, successful trades, etc.)
4. **Success Metrics**: Need deeper analysis of cooperation-success correlation in longer simulations
5. **Strategic Groups**: Identify coalitions based on mutual high cooperation scores

## Visualization Insights

The graphs clearly show:
- Cooperation score trajectories (solid lines, left axis)
- Points accumulation (dashed lines, right axis)
- Reference lines for cooperation thresholds
- Each agent's unique color coding

The dual-axis design effectively captures both reputation (cooperation) and performance (points) dynamics in a single view.
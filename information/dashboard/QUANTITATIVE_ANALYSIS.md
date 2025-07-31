# Quantitative Analysis Features

## Overview

The dashboard now includes comprehensive quantitative analysis capabilities that provide deep insights into agent behavior, performance, and cooperation patterns in the information asymmetry simulation.

## Features Implemented

### 1. Performance Metrics

#### Overall Metrics
- **Total Tasks Completed**: Number of tasks successfully completed across all agents
- **Total Points Awarded**: Sum of all points earned 
- **Average Points per Task**: Mean points earned per completed task
- **First Completion Rate**: Percentage of tasks where agents earned the first-completion bonus

#### Agent-Level Metrics
- Tasks completed per agent
- Total points earned
- Average points per task
- Number of first completions
- Messages sent/received
- Information pieces shared
- Response rate to requests

### 2. Communication Analysis

#### Message Flow Visualization
- Stacked bar chart showing message flow between agents
- Color-coded by recipient agent
- Shows communication patterns and frequency

#### Communication Summary
- Total messages sent
- Direct messages vs broadcasts
- Average response time to requests
- Median response time

### 3. Cooperation Patterns

#### Information Flow Matrix
- Visual heatmap showing information sharing between agents
- Color intensity indicates volume of information shared
- Helps identify cooperation networks and information hubs

### 4. Score Progression
- Real-time tracking of agent scores over rounds
- Line chart showing score evolution
- Identifies when agents gain advantages

### 5. Task Progress View
- Displays all completed tasks grouped by agent
- Shows task details: round completed, points earned, first-completion bonuses
- Summary statistics for task completion

## Technical Implementation

### Backend Enhancements

1. **Score Tracking Function** (`get_agent_scores_over_time`)
   - Tracks cumulative scores round by round
   - Handles varying numbers of agents and rounds
   - Provides data in Chart.js-compatible format

2. **Performance Metrics Calculator** (`calculate_performance_metrics`)
   - Processes all events to extract performance data
   - Calculates derived metrics (averages, rates)
   - Tracks request/response patterns

3. **Communication Metrics** (`calculate_communication_metrics`)
   - Analyzes message patterns
   - Calculates response times
   - Builds communication matrices

### Frontend Features

1. **Quantitative Analysis Tab**
   - Card-based layout for key metrics
   - Sortable performance table
   - Interactive charts and visualizations

2. **Dynamic Data Loading**
   - Real-time metric calculation
   - Handles varying simulation configurations
   - Error handling for edge cases

## Usage

1. Select a simulation from the dropdown
2. Navigate to the "Quantitative Analysis" tab
3. View overall performance metrics at the top
4. Examine agent-specific performance in the table
5. Analyze communication patterns in the charts
6. Study cooperation through the information flow matrix

## Insights Provided

- **Performance Analysis**: Which agents are most successful and why
- **Communication Efficiency**: Who communicates most effectively
- **Cooperation Networks**: Which agents form alliances
- **Strategic Behavior**: Response rates reveal cooperation vs competition
- **Information Flow**: How information spreads through the network

## Future Enhancements

While not yet implemented, potential additions include:
- Temporal analysis (cooperation evolution over time)
- Correlation analysis (e.g., communication frequency vs performance)
- Network centrality metrics
- Machine learning-based pattern detection
- Comparative analysis across multiple simulations

The quantitative analysis features provide researchers with powerful tools to understand emergent behaviors in information asymmetry scenarios.
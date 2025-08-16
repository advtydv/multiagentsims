# Single Simulation Analysis Documentation

## Abstract

This document provides a comprehensive overview of the analytical methods and metrics employed in the Information Asymmetry Simulation Dashboard. The dashboard analyzes multi-agent simulations where LLM-powered agents compete and cooperate in an environment characterized by asymmetric information distribution. We detail each analytical component, from basic event tracking to sophisticated strategic behavior analysis, providing researchers with a thorough understanding of the insights generated from simulation data.

## 1. Introduction

The Information Asymmetry Simulation creates a controlled environment where autonomous agents must navigate complex strategic decisions involving cooperation, competition, and information exchange. The dashboard provides multiple analytical lenses through which to examine agent behavior, performance, and emergent dynamics. This documentation describes each analytical component in detail.

## 2. Core Analytical Components

### 2.1 Timeline View (Event Transcript)

The Timeline View provides a chronological record of all simulation events, serving as the foundational data layer for all subsequent analyses.

**Components:**
- **Event Stream**: Complete chronological sequence of all actions, messages, and state changes
- **Agent Color Coding**: Visual identification system where each agent is assigned a unique color for tracking across all views
- **Round Navigation**: Ability to examine events within specific simulation rounds
- **Event Filtering**: Options to filter by event type (messages, task completions, information exchanges) or by specific agents

**Metrics Captured:**
- Timestamp of each event
- Event type classification
- Agent identification for all participants
- Event-specific data (message content, information pieces exchanged, task details)

### 2.2 Agent Network Visualization

The Agent Network provides a graph-based representation of agent interactions and relationships.

**Network Construction:**
- **Nodes**: Represent individual agents, sized by total activity level
- **Edges**: Represent communication channels between agents
  - Edge thickness indicates message frequency
  - Edge color intensity shows information exchange volume
  - Directionality shows asymmetric communication patterns

**Calculated Metrics:**
- **Degree Centrality**: Number of unique agents each agent communicates with
- **Information Flow**: Total pieces of information passing through each agent
- **Broker Score**: Measure of how much an agent connects otherwise unconnected agents
- **Network Density**: Ratio of actual connections to possible connections

### 2.3 Task Progress Tracking

This component monitors task completion patterns and efficiency metrics throughout the simulation.

**Task Metrics:**
- **Completion Rate**: Percentage of available tasks completed by each agent
- **Task Distribution**: How tasks are distributed among agents
- **First Completion Bonus**: Tracking of agents who complete tasks first
- **Task Quality Scores**: When available, quality metrics for completed tasks

**Temporal Analysis:**
- Task completion timeline showing when tasks are completed
- Round-by-round completion rates
- Task competition patterns (multiple agents attempting same tasks)

### 2.4 Rankings & Score Evolution

This analysis tracks competitive dynamics through score accumulation and ranking changes.

**Score Tracking:**
- **Cumulative Scores**: Total points accumulated by each agent over time
- **Score Trajectories**: Line graphs showing score evolution round by round
- **Ranking Changes**: How agent rankings shift throughout the simulation
- **Score Sources**: Breakdown of points from task completion vs. first completion bonuses

**Statistical Measures:**
- Score variance across agents
- Gini coefficient for score inequality
- Rank stability metrics
- Performance consistency indicators

## 3. Strategic Analysis Components

### 3.1 Agent Strategy Detection

This sophisticated analysis examines private thoughts and communication patterns to infer agent strategies.

**Strategy Categories Identified:**

1. **Cooperation Strategies**
   - Strong indicators: "collaborate", "mutual benefit", "work together"
   - Moderate indicators: "help", "share", "assist", "trust"
   - Weak indicators: "might help", "consider sharing"

2. **Competition Strategies**
   - Strong indicators: "beat everyone", "dominate", "win at all costs"
   - Moderate indicators: "compete", "rank", "advantage", "strategic"
   - Weak indicators: "stay ahead", "maintain position"

3. **Information Hoarding**
   - Strong indicators: "never share", "withhold all", "protect at all costs"
   - Moderate indicators: "selective", "cautious", "careful"
   - Weak indicators: "might withhold", "consider keeping"

4. **Deception Patterns**
   - Strong indicators: "lie outright", "false information", "trick them"
   - Moderate indicators: "mislead", "manipulate", "pretend"
   - Weak indicators: "strategic ambiguity", "consider withholding truth"

**Behavioral Pattern Analysis:**
- Persistence indicators (follow-up behavior)
- Urgency patterns (immediate vs. delayed actions)
- Reciprocity expectations
- Trust-building vs. exploitation strategies

### 3.2 Communication-Information Correlation

This analysis examines the relationship between communication efforts and information acquisition success.

**Key Metrics:**
- **Messages per Information Piece**: How many messages are required to obtain information
- **Response Rate**: Percentage of information requests that receive responses
- **Communication Effectiveness**: Ratio of information received to messages sent
- **Ignored Agents**: Identification of agents whose requests go unanswered

**Effectiveness Classifications:**
- Highly effective (>0.8 info pieces per message)
- Moderately effective (0.3-0.8 info pieces per message)
- Low effectiveness (<0.3 info pieces per message)
- No response (0 info pieces despite multiple messages)

## 4. Quantitative Analysis

### 4.1 Performance Metrics

Comprehensive performance tracking for each agent:

**Core Metrics:**
- Total tasks completed
- Total points earned
- Average points per task
- First completion rate
- Task quality scores (when available)

**Communication Metrics:**
- Messages sent/received
- Information pieces sent/received
- Information requests made
- Request fulfillment rate
- Response time statistics

### 4.2 Cooperation Dynamics

This analysis examines both perceived and actual cooperative behavior.

**Cooperation Scoring System:**
- Agents rate each other on a 1-10 scale in strategic reports
- Scores are tracked across rounds to identify trends
- Average cooperation given vs. received calculated for each agent

**Actual vs. Perceived Cooperation:**
- Comparison of cooperation ratings with actual information sharing behavior
- Identification of "false cooperators" (high ratings, low actual sharing)
- Detection of "undervalued cooperators" (low ratings, high actual sharing)
- Strategic misperception severity scoring

**Cooperation Networks:**
- Identification of cooperation cliques (mutually high-rating groups)
- Network performance analysis (do cooperative networks perform better?)
- Isolation detection (agents excluded from cooperation networks)

### 4.3 Reciprocity Analysis

Detailed examination of reciprocal relationships:

**Reciprocity Metrics:**
- Score reciprocity: Similarity in mutual cooperation ratings
- Behavioral reciprocity: Balance in actual information exchange
- Reciprocal pair identification (mutual ratings ≥6, difference <2)
- Performance analysis of reciprocal pairs

## 5. Advanced Analytics

### 5.1 Temporal Cooperation Evolution

This analysis tracks how cooperative relationships evolve over the simulation:

**Temporal Metrics:**
- Round-by-round cooperation score changes
- Trust trajectory analysis (increasing, decreasing, volatile)
- Alliance formation and dissolution patterns
- Cooperation stability scores per agent

**Key Insights Generated:**
- Early vs. late game cooperation patterns
- Critical rounds for alliance formation
- Trust volatility as a strategic indicator

### 5.2 Information Value and Timing

Analysis of when and how information is shared:

**Timing Categories:**
- Early game sharing (rounds 1-7)
- Mid game sharing (rounds 8-14)
- Late game sharing (rounds 15-20)

**Strategic Timing Patterns:**
- Response time analysis (immediate vs. delayed responses)
- Strategic withholding detection
- Information value assessment based on task completion impact

### 5.3 Network Centrality and Influence

Advanced network analysis examining agent positioning:

**Centrality Measures:**
- Degree centrality (connection count)
- Information flow centrality (total info passing through)
- Broker centrality (connecting otherwise disconnected agents)
- Influence scoring (how ratings affect network dynamics)

**Network-Level Metrics:**
- Overall network density
- Clustering coefficient
- Key broker identification
- Information bottleneck detection

## 6. Theory of Mind Analysis

The dashboard analyzes strategic reports where agents demonstrate theory of mind capabilities:

**Report Components Analyzed:**
- Current strategy descriptions
- Predictions about other agents' strategies
- Cooperation score assignments
- Strategic pivots and adaptations

**Metacognitive Indicators:**
- Accuracy of predictions about others
- Strategic adaptation based on observations
- Depth of strategic reasoning
- Deception awareness and counter-strategies

## 7. Statistical Summary

The dashboard provides aggregate statistics including:

**Event Statistics:**
- Total event count by type
- Event frequency analysis
- Activity timeline (events per minute)
- Round completion tracking

**Cooperation Matrix:**
- Full N×N matrix of cooperation frequencies
- Directional information flow mapping
- Message exchange patterns
- Asymmetric relationship identification

## 8. Insights and Interpretation

The dashboard generates automated insights including:

**Performance Insights:**
- Identification of top performers and their strategies
- Correlation between cooperation and performance
- Critical success factors

**Strategic Insights:**
- Dominant strategies in the simulation
- Strategy effectiveness analysis
- Emergent behavioral patterns

**Network Insights:**
- Alliance performance comparisons
- Network position advantages
- Information flow optimizations

## 9. Data Export and Further Analysis

All analytical results can be exported for further analysis:
- Raw event logs (JSONL format)
- Processed metrics (JSON format)
- Network data (graph formats)
- Time series data (CSV format)

## 10. Conclusion

The Information Asymmetry Simulation Dashboard provides a comprehensive analytical framework for understanding complex multi-agent dynamics. By combining quantitative metrics with strategic behavior analysis, researchers can gain deep insights into cooperation, competition, and information exchange strategies in environments characterized by asymmetric information distribution. The multi-faceted analytical approach enables examination of both individual agent strategies and emergent system-level phenomena, making it a powerful tool for studying strategic decision-making in multi-agent systems.
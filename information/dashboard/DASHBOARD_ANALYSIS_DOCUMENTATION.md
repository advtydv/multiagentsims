# Information Asymmetry Simulation Dashboard - Analysis Documentation

This document provides comprehensive documentation of all analyses and visualizations available in the Information Asymmetry Simulation Dashboard.

## Overview
The dashboard analyzes multi-agent simulations where agents with partial information must cooperate and compete to complete tasks. The simulation captures complex dynamics of information sharing, strategic behavior, and cooperation in an organizational setting.

## Dashboard Tabs and Analyses

### 1. Timeline View
**Purpose**: Provides a chronological view of all events in the simulation.

**Features**:
- **Round-by-Round Navigation**: Browse through each round (1-20) of the simulation
- **Event Type Filtering**: Filter by event types (messages, information exchanges, task completions, etc.)
- **Agent Filtering**: Focus on specific agents' activities
- **Color-Coded Agents**: Each agent has a unique color for easy identification

**Event Types Displayed**:
- **Messages**: Agent-to-agent communications
- **Information Exchanges**: Actual data sharing between agents
- **Task Completions**: When agents successfully complete tasks
- **Private Thoughts**: Agent's internal reasoning (if logged)
- **Agent Reports**: Strategic assessments submitted by agents
- **Deception Attempts**: When agents provide misleading information

### 2. Agent Network (Quantitative Analysis)
**Purpose**: Provides quantitative metrics and visualizations of agent communication patterns and network dynamics.

**Visualizations**:

#### Communication Volume Matrix
- **Type**: Heatmap
- **Shows**: Number of messages sent from each agent (rows) to each agent (columns)
- **Insight**: Identifies who communicates most frequently with whom
- **Color Scale**: Blue intensity indicates message volume

#### Response Rate Matrix
- **Type**: Heatmap  
- **Shows**: Percentage of requests that were answered between agent pairs
- **Insight**: Reveals trust relationships and reliability patterns
- **Color Scale**: Red (0%) → Yellow (50%) → Green (100%)

#### Information Flow Balance
- **Type**: Stacked bar chart
- **Shows**: Information shared (negative/red) vs received (positive/green) per agent
- **Metrics**: Net flow = received - shared
- **Insight**: Identifies net contributors vs net consumers of information

#### Communication Efficiency
- **Type**: Scatter plot
- **X-axis**: Messages sent
- **Y-axis**: Information pieces received
- **Metric**: Efficiency = info received / messages sent
- **Insight**: Shows who communicates efficiently vs who sends many messages for little return

#### Network Centrality Metrics
Three key measures:
1. **Degree Centrality**: Number of unique agents each agent communicates with
2. **Betweenness Centrality**: How often an agent is on the shortest path between others (pending implementation)
3. **Information Brokerage**: Number of unique information pieces shared by each agent

#### Network Evolution Over Time
- **Type**: Multi-line chart
- **Metrics Tracked**:
  - Message volume per round
  - Active connections (unique communication pairs)
  - Network density (% of possible connections used)
- **Insight**: Shows how network activity changes throughout the simulation

#### Key Network Insights Panel
Automatically identifies and displays:
- Most connected agent
- Top information broker
- Most efficient communicator
- Top net receiver/contributor
- Average network density

### 3. Task Progress
**Purpose**: Tracks task completion throughout the simulation.

**Metrics**:
- **Total Points Awarded**: Sum of all points earned
- **Tasks by Round**: Distribution of completions over time
- **First Completion Bonuses**: Extra points for being first
- **Task Quality**: Average quality scores

**Visualizations**:
- Task completion timeline
- Points breakdown by agent
- Quality distribution charts

### 4. Rankings & Scores
**Purpose**: Shows competitive dynamics and performance evolution.

**Components**:
- **Score Progression Chart**: Line graph showing each agent's score over rounds
- **Final Rankings Table**: End-of-simulation leaderboard
- **Rank Changes**: How positions shifted throughout the game

**Insights**:
- Performance trajectories (steady climbers vs. early leaders)
- Competitive clustering
- Impact of strategic choices on outcomes

### 5. Strategic Analysis
**Purpose**: Analyzes strategic behaviors through keyword detection and pattern analysis.

**Analyses**:
- **Keyword-Based Behavior Detection**:
  - **Strong Indicators**: "urgent", "critical", "please help"
  - **Moderate Indicators**: "need", "require", "share"
  - **Weak Indicators**: "would", "could", "might"

- **Deception Detection**: Compares private thoughts with public messages
- **Strategic Patterns**: Identifies manipulation, hoarding, coalition-forming

**Visualizations**:
- Behavior frequency charts
- Agent strategy profiles
- Deception instances timeline

### 6. Quantitative Analysis
**Purpose**: Provides detailed performance metrics and statistical analysis.

#### Performance Metrics
- **Total Tasks**: Number completed by all agents
- **Total Points**: Aggregate score
- **Average Points/Task**: Efficiency metric
- **First Completion Rate**: Percentage of tasks completed first

#### Agent Performance Table
Columns:
- **Tasks Completed**: Individual count
- **Points Earned**: Total score
- **Messages Sent/Received**: Communication activity
- **Info Shared**: Generosity metric
- **Response Rate**: Reliability measure

#### Communication Analysis
- **Message Flow Heatmap**: Who talks to whom
- **Information Request Patterns**: Asking vs. sharing behavior
- **Response Time Analysis**: How quickly agents respond

#### Message Content Analysis
- **Keyword Patterns**: Strategic language use
- **Deception Indicators**: Mismatches between thoughts and messages
- **Communication Effectiveness**: Correlation between messages sent and information received

### 7. Strategic Reports
**Purpose**: Displays confidential strategic assessments submitted by agents.

**Report Contents**:
- **Confidential Assessment**: Narrative analysis covering:
  - Situation assessment
  - Stakeholder landscape
  - Strategic considerations
  - Forward outlook
  - Risk assessment

- **Cooperation Scores**: Each agent rates others (1-10 scale):
  - 1-2: Actively sabotaging
  - 3-4: Uncooperative
  - 5-6: Neutral
  - 7-8: Generally cooperative
  - 9-10: Extremely helpful

**Features**:
- Agent selector to view individual reports
- Chronological report viewing
- Collapsible rounds for easy navigation

### 8. Cooperation Analysis
**Purpose**: Deep analysis of cooperation dynamics and their impact on performance.

#### Key Metrics
- **Hoarding Rate**: (Requests received - Info shared) / Requests received
  - 0% = Shares everything requested
  - 100% = Shares nothing

- **Average Cooperation Given/Received**: Mean scores from strategic reports
- **Response Rate**: Percentage of requests answered
- **Strategic Misperception**: When perceived cooperation doesn't match actual behavior

#### Analyses Performed

##### Cooperation Score Correlations
- **Performance Correlation**: How cooperation scores relate to final rankings
- **Perception vs. Reality**: Comparing given scores with actual sharing behavior
- **Self-Assessment Accuracy**: How agents rate their own cooperation

##### Strategic Misperception Analysis
- **False Cooperators**: High cooperation score but high hoarding rate
- **Undervalued Cooperators**: Low cooperation score but generous sharing
- **Misperception Impact**: How wrong assessments affect outcomes

##### Cooperation Networks
- **Mutual High Ratings**: Identifies trusted partnerships
- **Cooperation Cliques**: Groups with high internal trust
- **Network Performance**: Whether cooperative networks outperform others

##### Reciprocity Patterns
- **Balanced Exchanges**: Agents with equal give-and-take
- **Asymmetric Relationships**: One-sided cooperation
- **Reciprocity ROI**: Whether reciprocal behavior improves performance

##### Temporal Cooperation Evolution
- **Cooperation Trajectory**: How average cooperation changes over rounds
- **Volatility Measure**: Stability of cooperation patterns
- **Alliance Formation**: When stable partnerships emerge
- **Betrayal Events**: Sharp drops in cooperation scores
- **Convergence Point**: When cooperation patterns stabilize

### 9. Information Value Analysis
**Purpose**: Analyzes which information pieces drive value and how timing affects strategy.

#### High-Value Information
- **Value Metrics**:
  - Total points generated
  - Average points per use
  - Usage frequency
- **Value Distribution**: Bar chart of top 10 most valuable pieces

#### Timing Strategies
- **Sharing Patterns**:
  - Early game (Rounds 1-5): Proactive sharing
  - Mid game (Rounds 6-15): Strategic trading
  - Late game (Rounds 16-20): Hoarding or dumping

- **First Mover Advantage**: Agents who benefit from early information acquisition
- **Late Game Specialists**: Agents who perform better in final rounds

#### Strategic Information Management
Identifies four key patterns:
1. **Selective Sharers**: Share low-value freely, hoard high-value
2. **Reciprocal Traders**: High-value only to trusted partners
3. **Information Brokers**: Leverage network position
4. **Free Sharers**: Share regardless of value

## Key Insights and Patterns

### Performance Indicators
- **High Performers**: Often balance cooperation with strategic withholding
- **Information Brokers**: Central network position correlates with success
- **Trust Networks**: Stable alliances outperform lone wolves

### Strategic Behaviors
- **Deception**: Rare but impactful when detected
- **Hoarding**: Short-term gains but long-term reputation damage
- **Coalition Formation**: Emerges naturally around round 5-7

### Cooperation Dynamics
- **Tit-for-Tat**: Most common successful strategy
- **Reputation Effects**: Past behavior strongly influences future interactions
- **Endgame Effects**: Cooperation often breaks down in final rounds

## Using the Dashboard

### Best Practices
1. Start with Timeline View for narrative understanding
2. Use Cooperation Analysis to identify key relationships
3. Check Strategic Reports for agent perspectives
4. Correlate Performance Metrics with behavioral patterns

### Interpretation Guidelines
- High hoarding + high performance = effective but selfish strategy
- High cooperation + low performance = possibly exploited
- Central network position + moderate cooperation = information broker
- Volatile cooperation scores = strategic player or unstable personality

### Limitations
- Keyword analysis may miss subtle strategic communication
- Cooperation scores are subjective agent assessments
- Network visualization becomes cluttered with >15 agents
- Some metrics require complete information to calculate accurately

## Technical Details

### Data Sources
- **Event Logs**: JSONL format capturing all simulation events
- **Agent Reports**: Structured JSON with narrative and scores
- **Configuration**: Simulation parameters affecting analysis

### Calculations
- **Hoarding Rate**: Based on tracked requests and shares
- **Network Centrality**: Simplified betweenness centrality
- **Information Value**: Points generated per information piece
- **Cooperation Volatility**: Standard deviation of score changes

### Update Frequency
- Real-time parsing of historical simulation data
- No live updates during simulation run
- Complete data required for some analyses

## Future Enhancements
- Cross-simulation comparison capabilities
- Predictive modeling of agent behavior
- Real-time dashboard updates during simulation
- Advanced game theory pattern detection
- Machine learning-based strategy classification
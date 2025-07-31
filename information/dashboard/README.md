# Information Asymmetry Simulation Dashboard

A web-based dashboard for viewing and analyzing logs from the Information Asymmetry Simulation.

## Features

- **Timeline View**: Round-by-round display of all simulation events
- **Agent Color Coding**: Each agent has a unique color for easy identification
- **Event Filtering**: Filter events by type and agent
- **Score Tracking**: View agent rankings and score progression
- **Interactive Navigation**: Easy navigation between rounds
- **Responsive Design**: Works on desktop and mobile devices

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the dashboard:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Select a Simulation**: Use the dropdown in the top navigation to select a simulation run
2. **Navigate Rounds**: Use Previous/Next buttons to move between rounds
3. **Apply Filters**: Use the left sidebar to filter events by type or agent
4. **View Different Tabs**: 
   - Timeline View: See events as they happen
   - Agent Network: (Coming soon) Visualize communication patterns
   - Task Progress: (Coming soon) Track task completion
   - Rankings & Scores: View score progression and final rankings
   - Strategic Analysis: (Coming soon) Analyze agent strategies

## Dashboard Structure

```
dashboard/
├── app.py                 # Flask application
├── log_parser.py         # JSONL parsing utilities
├── data_processor.py     # Data aggregation and analysis
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html       # Main HTML template
└── static/
    ├── css/
    │   └── styles.css   # Custom styles
    └── js/
        └── dashboard.js # Frontend JavaScript
```

## Key Features Explained

### Timeline View
- Shows all events in chronological order
- Color-coded by agent
- Expandable private thoughts
- Message flow visualization
- Information exchange tracking

### Event Types
- **Agent Actions**: What agents decide to do
- **Messages**: Communication between agents
- **Information Exchanges**: Transfer of information pieces
- **Task Completions**: When tasks are successfully completed
- **Private Thoughts**: Agent's strategic reasoning

### Agent Colors
Each agent is assigned a unique color that remains consistent throughout all views:
- Agent 1: Red
- Agent 2: Teal
- Agent 3: Blue
- Agent 4: Yellow
- Agent 5: Purple
- (And more for additional agents)

## Future Enhancements

- Agent network graph visualization
- Task progress tracking
- Information distribution matrix
- Export functionality
- Real-time updates for ongoing simulations
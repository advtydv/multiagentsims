# Simulation Visualizer Module

## Overview

The `visualizer.py` module provides comprehensive, publication-ready visualizations for the information asymmetry simulation analysis. It creates six major visualization types that provide insights into agent behavior, communication patterns, and strategic dynamics.

## Visualizations Created

### 1. Agent Performance Dashboard (`agent_performance_dashboard.png`)
A multi-panel figure showing:
- **Agent Rankings Bar Chart**: Final scores for all agents
- **Cooperation Scores**: Horizontal bar chart showing cooperation levels
- **Deception Scores**: Horizontal bar chart showing deception rates
- **Strategy Space Scatter Plot**: 2D plot of cooperation vs deception with bubble size representing final score

### 2. Communication Networks (`communication_networks.png`)
Two network graphs showing:
- **General Communication Network**: All messages between agents
- **Information Transfer Network**: Actual information sharing patterns
- Node size represents total message volume
- Edge width represents communication frequency

### 3. Information Flow Heatmap (`information_flow_heatmap.png`)
- Matrix visualization showing who shared information with whom
- Color intensity indicates frequency of information sharing
- Exact counts annotated in each cell
- Diagonal masked (agents don't share with themselves)

### 4. Negotiation Analysis (`negotiation_analysis.png`)
Four panels showing:
- **Success Rate by Agent**: Bar chart of negotiation success rates
- **Negotiation Network**: Graph showing negotiation partnerships
- **Complexity Distribution**: Pie chart of negotiation types
- **Success Rate Over Time**: Line plot of temporal trends

### 5. Temporal Analysis (`temporal_analysis.png`)
Three time-series plots:
- **Task Completion Timeline**: Bar chart of tasks completed per round
- **Communication Volume**: Line plot of message frequency
- **Deception Events**: Scatter plot of deception occurrences

### 6. Strategic Behavior Analysis (`strategic_behavior_analysis.png`)
- **Word Cloud**: Visual representation of private thoughts (requires wordcloud package)
- **Message Activity Distribution**: Histogram of agent communication levels
- **Communication Type Distribution**: Pie chart of broadcasts vs direct messages

## Dependencies

### Required Packages
- `matplotlib`: Core plotting library
- `seaborn`: Statistical data visualization
- `numpy`: Numerical operations

### Optional Packages
- `networkx`: For network visualizations (communication and negotiation networks)
- `wordcloud`: For generating word clouds from private thoughts

The module handles missing optional packages gracefully and skips those specific visualizations.

## Usage

### From Main Analyzer
The visualizer is automatically called when running the main analyzer:

```bash
python -m analysis.main_analyzer simulation_20250714_103613
```

### Direct Usage
```python
from analysis.visualizer import create_visualizations

# Assuming you have log_data and analysis_results
create_visualizations(log_data, analysis_results, output_dir)
```

### Testing
Run the test script to visualize the most recent simulation:

```bash
python test_visualizer.py
```

## Customization

### Color Scheme
The module uses a consistent color scheme defined in the `COLORS` dictionary:
- Primary: `#2E86AB` (blue)
- Secondary: `#E63946` (red)
- Success: `#06D6A0` (green)
- Warning: `#F77F00` (orange)
- Info: `#7209B7` (purple)

### Figure Quality
All figures are saved at 300 DPI for publication quality. Modify the `dpi` parameter in `savefig()` calls to adjust.

### Layout
The module uses matplotlib's GridSpec for complex layouts. Adjust `hspace` and `wspace` parameters to control spacing between subplots.

## Output

All visualizations are saved as PNG files in the specified output directory (typically `logs/[simulation_id]/analysis/`).

## Troubleshooting

### Missing Packages
If optional packages are missing:
- NetworkX: Network visualizations will be skipped
- WordCloud: Word cloud visualization will show a placeholder

Install missing packages with:
```bash
pip install networkx wordcloud
```

### Memory Issues
For very large simulations, consider:
- Reducing figure DPI
- Processing data in chunks
- Limiting the number of agents shown in certain visualizations

### Style Issues
If plots look different than expected:
- The module uses `seaborn-v0_8-darkgrid` style
- Ensure matplotlib and seaborn are up to date
- Check for custom matplotlib configurations in your environment
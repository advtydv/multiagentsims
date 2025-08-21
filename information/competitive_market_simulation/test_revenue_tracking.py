#!/usr/bin/env python3
"""Test the new revenue tracking implementation"""

from simulation.analysis import SimulationAnalyzer
from pathlib import Path
import json

# Analyze the most recent simulation
log_dir = Path('logs/simulation_20250818_094416')
analyzer = SimulationAnalyzer(log_dir)
results = analyzer.analyze()

# Print the new metric
if 'total_revenue_by_round' in results['metrics']:
    print('Total Revenue by Round:')
    print('=' * 50)
    for round_data in results['metrics']['total_revenue_by_round']:
        print(f"Round {round_data['round']:2}: "
              f"Revenue this round: ${round_data['revenue_this_round']:>10.2f} | "
              f"Cumulative: ${round_data['cumulative_revenue']:>10.2f} | "
              f"Avg per agent: ${round_data['average_revenue_per_agent']:>8.2f}")
    
    print('\n' + '=' * 50)
    print('Summary:')
    final = results['metrics']['total_revenue_by_round'][-1]
    print(f"Total Revenue Generated: ${final['cumulative_revenue']:,.2f}")
    print(f"Average Revenue per Agent: ${final['average_revenue_per_agent']:,.2f}")
else:
    print('total_revenue_by_round metric not found in results')

# Also check the updated analysis_results.json file
analysis_file = log_dir / 'analysis_results.json'
print(f"\nAnalysis results saved to: {analysis_file}")
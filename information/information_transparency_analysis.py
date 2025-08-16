#!/usr/bin/env python3
"""
Analysis of task completion rates based on ranking visibility settings.
Compares simulations with show_full_rankings=true vs false for both 10 and 20 round simulations.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Define the simulation paths
SIMULATIONS = {
    '10_rounds': {
        'full_rankings_true': 'simulation_20250811_123438',
        'full_rankings_false': 'simulation_20250811_175050'
    },
    '20_rounds': {
        'full_rankings_true': 'simulation_20250811_144020',
        'full_rankings_false': 'simulation_20250811_164139'
    }
}

BASE_PATH = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation/logs')


def extract_task_completions(simulation_path):
    """
    Extract task completion events from a simulation log.
    Returns a dict mapping round numbers to cumulative task completions.
    """
    log_file = BASE_PATH / simulation_path / 'simulation_log.jsonl'
    
    # Track completions by round
    completions_by_round = defaultdict(int)
    current_round = 1
    max_round_seen = 1
    
    with open(log_file, 'r') as f:
        for line in f:
            event = json.loads(line)
            
            # Track round changes from agent_action events
            if event['event_type'] == 'agent_action':
                if 'round' in event['data']:
                    current_round = event['data']['round']
                    max_round_seen = max(max_round_seen, current_round)
            
            # Also check private_thoughts for round info
            elif event['event_type'] == 'private_thoughts':
                if 'round' in event['data']:
                    current_round = event['data']['round']
                    max_round_seen = max(max_round_seen, current_round)
            
            # Count successful task completions
            elif event['event_type'] == 'task_completion':
                if event['data']['success']:
                    completions_by_round[current_round] += 1
    
    # Convert to cumulative counts
    cumulative_completions = {}
    total = 0
    
    for round_num in range(1, max_round_seen + 1):
        total += completions_by_round.get(round_num, 0)
        cumulative_completions[round_num] = total
    
    return cumulative_completions


def get_simulation_config(simulation_path):
    """Extract configuration details from simulation."""
    log_file = BASE_PATH / simulation_path / 'simulation_log.jsonl'
    
    with open(log_file, 'r') as f:
        first_line = f.readline()
        event = json.loads(first_line)
        if event['event_type'] == 'simulation_start':
            return event['data']['config']
    return None


def plot_comparison(round_count):
    """Create comparison plot for simulations with specified round count."""
    
    # Extract data for both conditions
    sim_true = SIMULATIONS[f'{round_count}_rounds']['full_rankings_true']
    sim_false = SIMULATIONS[f'{round_count}_rounds']['full_rankings_false']
    
    completions_true = extract_task_completions(sim_true)
    completions_false = extract_task_completions(sim_false)
    
    # Prepare data for plotting
    rounds = list(range(1, round_count + 1))
    values_true = [completions_true.get(r, completions_true.get(r-1, 0) if r > 1 else 0) for r in rounds]
    values_false = [completions_false.get(r, completions_false.get(r-1, 0) if r > 1 else 0) for r in rounds]
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(rounds, values_true, marker='o', linewidth=2, markersize=6, 
             label='Full Transparency', color='#2E86AB')
    plt.plot(rounds, values_false, marker='s', linewidth=2, markersize=6,
             label='Limited Transparency', color='#A23B72')
    
    plt.xlabel('Round Number', fontsize=12)
    plt.ylabel('Cumulative Tasks Completed', fontsize=12)
    plt.title(f'Impact of Information Transparency on Task Completion ({round_count} Rounds)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.xticks(rounds)
    
    # Add value labels on data points
    for i, (r, v) in enumerate(zip(rounds, values_true)):
        if i % 2 == 0 or i == len(rounds) - 1:  # Label every other point to avoid crowding
            plt.annotate(str(v), (r, v), textcoords="offset points", xytext=(0,5), 
                        ha='center', fontsize=9, color='#2E86AB')
    
    for i, (r, v) in enumerate(zip(rounds, values_false)):
        if i % 2 == 1 or i == len(rounds) - 1:  # Label alternate points
            plt.annotate(str(v), (r, v), textcoords="offset points", xytext=(0,-15), 
                        ha='center', fontsize=9, color='#A23B72')
    
    plt.tight_layout()
    
    # Save the plot
    output_file = f'information_transparency_comparison_{round_count}_rounds.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {output_file}")
    
    # Also display
    plt.show()
    
    # Print summary statistics
    print(f"\n{round_count}-Round Simulation Summary:")
    print(f"  Full Transparency: {values_true[-1]} total tasks completed")
    print(f"  Limited Transparency: {values_false[-1]} total tasks completed")
    print(f"  Difference: {values_true[-1] - values_false[-1]} tasks")
    if values_false[-1] > 0:
        print(f"  Percentage difference: {((values_true[-1] - values_false[-1]) / values_false[-1] * 100):.1f}%")
    else:
        if values_true[-1] > 0:
            print(f"  Percentage difference: Full transparency had {values_true[-1]} completions vs 0")
        else:
            print(f"  Percentage difference: Both had 0 completions")
    
    return {
        'rounds': rounds,
        'full_transparency': values_true,
        'limited_transparency': values_false
    }


def main():
    """Main analysis function."""
    print("=" * 60)
    print("INFORMATION TRANSPARENCY IMPACT ON TASK COMPLETION")
    print("=" * 60)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Verify all simulations exist
    print("Verifying simulation files...")
    for round_type, sims in SIMULATIONS.items():
        for visibility, sim_name in sims.items():
            path = BASE_PATH / sim_name / 'simulation_log.jsonl'
            if path.exists():
                config = get_simulation_config(sim_name)
                rounds = config['simulation']['rounds']
                show_rankings = config['simulation']['show_full_rankings']
                print(f"  ✓ {sim_name}: {rounds} rounds, show_full_rankings={show_rankings}")
            else:
                print(f"  ✗ {sim_name}: FILE NOT FOUND")
                return
    
    print("\nGenerating comparison plots...\n")
    
    # Generate plots for both 10 and 20 round simulations
    results_10 = plot_comparison(10)
    results_20 = plot_comparison(20)
    
    # Save detailed results to JSON for future reference
    detailed_results = {
        'analysis_timestamp': datetime.now().isoformat(),
        'simulations_analyzed': SIMULATIONS,
        '10_round_results': {
            'rounds': results_10['rounds'],
            'full_transparency': results_10['full_transparency'],
            'limited_transparency': results_10['limited_transparency']
        },
        '20_round_results': {
            'rounds': results_20['rounds'],
            'full_transparency': results_20['full_transparency'],
            'limited_transparency': results_20['limited_transparency']
        }
    }
    
    with open('information_transparency_analysis_results.json', 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print("Output files generated:")
    print("  - information_transparency_comparison_10_rounds.png")
    print("  - information_transparency_comparison_20_rounds.png")
    print("  - information_transparency_analysis_results.json")


if __name__ == "__main__":
    main()
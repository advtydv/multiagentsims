#!/usr/bin/env python3
"""
Analysis of task completion rates based on ranking visibility settings for 30-round simulations.
Compares simulations with show_full_rankings=true vs false.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Define the simulation paths for 30-round simulations
SIMULATIONS_30 = {
    'full_rankings_true': 'simulation_20250813_181133',
    'full_rankings_false': 'simulation_20250813_181726'
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


def analyze_cooperation_dynamics(simulation_path):
    """Analyze cooperation score dynamics throughout the simulation."""
    log_file = BASE_PATH / simulation_path / 'simulation_log.jsonl'
    
    cooperation_rounds = []
    
    with open(log_file, 'r') as f:
        for line in f:
            event = json.loads(line)
            if event['event_type'] == 'cooperation_scores_aggregated':
                round_num = event['data']['round']
                aggregated = event['data']['aggregated_scores']
                
                # Calculate average cooperation score for this round
                scores = []
                for agent, stats in aggregated.items():
                    if stats['mean'] is not None:
                        scores.append(stats['mean'])
                
                if scores:
                    avg_cooperation = sum(scores) / len(scores)
                    cooperation_rounds.append({
                        'round': round_num,
                        'avg_cooperation': avg_cooperation,
                        'num_agents': len(scores)
                    })
    
    return cooperation_rounds


def plot_30_round_comparison():
    """Create comprehensive comparison plots for 30-round simulations."""
    
    # Extract data for both conditions
    sim_true = SIMULATIONS_30['full_rankings_true']
    sim_false = SIMULATIONS_30['full_rankings_false']
    
    completions_true = extract_task_completions(sim_true)
    completions_false = extract_task_completions(sim_false)
    
    # Get cooperation dynamics
    cooperation_true = analyze_cooperation_dynamics(sim_true)
    cooperation_false = analyze_cooperation_dynamics(sim_false)
    
    # Prepare data for plotting
    rounds = list(range(1, 31))
    values_true = [completions_true.get(r, completions_true.get(r-1, 0) if r > 1 else 0) for r in rounds]
    values_false = [completions_false.get(r, completions_false.get(r-1, 0) if r > 1 else 0) for r in rounds]
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Task Completions
    ax1.plot(rounds, values_true, marker='o', linewidth=2, markersize=5, 
             label='Full Rankings Visible', color='#2E86AB', alpha=0.8)
    ax1.plot(rounds, values_false, marker='s', linewidth=2, markersize=5,
             label='Own Ranking Only', color='#A23B72', alpha=0.8)
    
    ax1.set_xlabel('Round Number', fontsize=12)
    ax1.set_ylabel('Cumulative Tasks Completed', fontsize=12)
    ax1.set_title('Impact of Ranking Visibility on Task Completion (30 Rounds)', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11, loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(range(0, 31, 3))
    
    # Add value labels on key data points (every 5 rounds and final)
    for i, (r, v) in enumerate(zip(rounds, values_true)):
        if r % 5 == 0 or r == 30:
            ax1.annotate(str(v), (r, v), textcoords="offset points", xytext=(0,5), 
                        ha='center', fontsize=9, color='#2E86AB')
    
    for i, (r, v) in enumerate(zip(rounds, values_false)):
        if r % 5 == 0 or r == 30:
            ax1.annotate(str(v), (r, v), textcoords="offset points", xytext=(0,-15), 
                        ha='center', fontsize=9, color='#A23B72')
    
    # Plot 2: Cooperation Dynamics (if available)
    if cooperation_true and cooperation_false:
        coop_rounds_true = [c['round'] for c in cooperation_true]
        coop_scores_true = [c['avg_cooperation'] for c in cooperation_true]
        coop_rounds_false = [c['round'] for c in cooperation_false]
        coop_scores_false = [c['avg_cooperation'] for c in cooperation_false]
        
        ax2.plot(coop_rounds_true, coop_scores_true, marker='o', linewidth=2, markersize=8,
                label='Full Rankings Visible', color='#2E86AB', alpha=0.8)
        ax2.plot(coop_rounds_false, coop_scores_false, marker='s', linewidth=2, markersize=8,
                label='Own Ranking Only', color='#A23B72', alpha=0.8)
        
        ax2.set_xlabel('Round Number', fontsize=12)
        ax2.set_ylabel('Average Cooperation Score', fontsize=12)
        ax2.set_title('Cooperation Dynamics Based on Ranking Visibility', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11, loc='best')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(1, 10)
        ax2.set_xticks(coop_rounds_true)  # Report rounds only
    
    plt.tight_layout()
    
    # Save the plot
    output_file = 'ranking_visibility_comparison_30_rounds.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {output_file}")
    
    # Also display
    plt.show()
    
    return {
        'rounds': rounds,
        'full_rankings_visible': values_true,
        'own_ranking_only': values_false,
        'cooperation_dynamics': {
            'full_rankings': cooperation_true,
            'own_ranking': cooperation_false
        }
    }


def generate_detailed_analysis():
    """Generate detailed statistical analysis of the 30-round simulations."""
    
    print("=" * 70)
    print("RANKING VISIBILITY ANALYSIS - 30 ROUND SIMULATIONS")
    print("=" * 70)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Verify simulations exist and get configurations
    print("Simulation Details:")
    print("-" * 50)
    
    for visibility_type, sim_name in SIMULATIONS_30.items():
        path = BASE_PATH / sim_name / 'simulation_log.jsonl'
        if path.exists():
            config = get_simulation_config(sim_name)
            rounds = config['simulation']['rounds']
            show_rankings = config['simulation']['show_full_rankings']
            visibility_label = "Full Rankings Visible" if show_rankings else "Own Ranking Only"
            print(f"  {sim_name}:")
            print(f"    - Rounds: {rounds}")
            print(f"    - Visibility: {visibility_label}")
            print(f"    - show_full_rankings: {show_rankings}")
        else:
            print(f"  ✗ {sim_name}: FILE NOT FOUND")
            return
    
    print("\nGenerating analysis...\n")
    
    # Generate plots and get data
    results = plot_30_round_comparison()
    
    # Calculate statistics
    full_rankings = results['full_rankings_visible']
    own_ranking = results['own_ranking_only']
    
    print("Task Completion Statistics:")
    print("-" * 50)
    print(f"  Full Rankings Visible:")
    print(f"    - Total tasks completed: {full_rankings[-1]}")
    print(f"    - Tasks per round (avg): {full_rankings[-1] / 30:.2f}")
    print(f"    - Round 10: {full_rankings[9]} tasks")
    print(f"    - Round 20: {full_rankings[19]} tasks")
    print(f"    - Round 30: {full_rankings[29]} tasks")
    
    print(f"\n  Own Ranking Only:")
    print(f"    - Total tasks completed: {own_ranking[-1]}")
    print(f"    - Tasks per round (avg): {own_ranking[-1] / 30:.2f}")
    print(f"    - Round 10: {own_ranking[9]} tasks")
    print(f"    - Round 20: {own_ranking[19]} tasks")
    print(f"    - Round 30: {own_ranking[29]} tasks")
    
    print(f"\n  Comparative Analysis:")
    print(f"    - Absolute difference: {abs(full_rankings[-1] - own_ranking[-1])} tasks")
    if own_ranking[-1] > 0:
        pct_diff = ((full_rankings[-1] - own_ranking[-1]) / own_ranking[-1]) * 100
        if pct_diff > 0:
            print(f"    - Full rankings completed {pct_diff:.1f}% more tasks")
        else:
            print(f"    - Own ranking only completed {abs(pct_diff):.1f}% more tasks")
    
    # Analyze progression patterns
    print(f"\n  Task Completion Progression:")
    for milestone in [5, 10, 15, 20, 25, 30]:
        full_val = full_rankings[milestone-1]
        own_val = own_ranking[milestone-1]
        print(f"    Round {milestone:2d}: Full={full_val:3d}, Own={own_val:3d}, Diff={full_val-own_val:+3d}")
    
    # Cooperation analysis
    if results['cooperation_dynamics']['full_rankings'] and results['cooperation_dynamics']['own_ranking']:
        print(f"\n  Cooperation Dynamics:")
        coop_full = results['cooperation_dynamics']['full_rankings']
        coop_own = results['cooperation_dynamics']['own_ranking']
        
        for cf, co in zip(coop_full, coop_own):
            round_num = cf['round']
            print(f"    Round {round_num:2d}: Full={cf['avg_cooperation']:.2f}, Own={co['avg_cooperation']:.2f}")
    
    # Save all results to JSON
    analysis_results = {
        'analysis_timestamp': datetime.now().isoformat(),
        'simulations_analyzed': {
            '30_rounds': SIMULATIONS_30
        },
        '30_round_results': {
            'rounds': results['rounds'],
            'full_rankings_visible': results['full_rankings_visible'],
            'own_ranking_only': results['own_ranking_only']
        },
        'cooperation_dynamics': results['cooperation_dynamics'],
        'summary_statistics': {
            'full_rankings': {
                'total_tasks': full_rankings[-1],
                'avg_per_round': full_rankings[-1] / 30,
                'milestone_10': full_rankings[9],
                'milestone_20': full_rankings[19],
                'milestone_30': full_rankings[29]
            },
            'own_ranking': {
                'total_tasks': own_ranking[-1],
                'avg_per_round': own_ranking[-1] / 30,
                'milestone_10': own_ranking[9],
                'milestone_20': own_ranking[19],
                'milestone_30': own_ranking[29]
            }
        }
    }
    
    # Update the combined results file
    combined_results_file = 'ranking_visibility_analysis_results.json'
    
    # Load existing results if they exist
    if Path(combined_results_file).exists():
        with open(combined_results_file, 'r') as f:
            existing_results = json.load(f)
    else:
        existing_results = {}
    
    # Add 30-round results
    existing_results['30_round_results'] = analysis_results['30_round_results']
    existing_results['simulations_analyzed']['30_rounds'] = SIMULATIONS_30
    existing_results['analysis_timestamp_30_rounds'] = datetime.now().isoformat()
    
    # Save updated combined results
    with open(combined_results_file, 'w') as f:
        json.dump(existing_results, f, indent=2)
    
    # Also save dedicated 30-round results
    with open('ranking_visibility_analysis_30_rounds.json', 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("Output files generated:")
    print("  - ranking_visibility_comparison_30_rounds.png")
    print("  - ranking_visibility_analysis_30_rounds.json")
    print("  - ranking_visibility_analysis_results.json (updated)")


def main():
    """Main analysis function."""
    generate_detailed_analysis()


if __name__ == "__main__":
    main()
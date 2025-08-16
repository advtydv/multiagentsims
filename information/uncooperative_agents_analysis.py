#!/usr/bin/env python3
"""
Analysis of the impact of uncooperative agents on task completion and cooperation dynamics.
Examines how varying numbers of disruptive agents affect system performance.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import matplotlib.patches as mpatches

# Define the simulations to analyze
SIMULATIONS_10_ROUNDS = {
    0: 'simulation_20250811_123438',  # Baseline from Aug 11
    1: 'simulation_20250812_132312',
    2: 'simulation_20250812_120055',
    9: 'simulation_20250812_142647'
}

SIMULATIONS_20_ROUNDS = {
    0: 'simulation_20250812_173538',
    2: 'simulation_20250812_161040'
}

BASE_PATH = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation/logs')


def extract_simulation_data(simulation_path):
    """
    Extract comprehensive data from a simulation including:
    - Task completions by round
    - Cooperation scores
    - Agent types (cooperative vs uncooperative)
    """
    log_file = BASE_PATH / simulation_path / 'simulation_log.jsonl'
    
    data = {
        'task_completions_by_round': defaultdict(int),
        'cooperation_scores': [],
        'agent_types': {},
        'total_messages': 0,
        'deception_attempts': 0,
        'config': None,
        'current_round': 1,
        'max_round': 1
    }
    
    with open(log_file, 'r') as f:
        for line in f:
            event = json.loads(line)
            event_type = event['event_type']
            
            # Get configuration
            if event_type == 'simulation_start':
                data['config'] = event['data']['config']
                # Extract agent types if available
                if 'agent_types' in data['config']:
                    data['agent_types'] = data['config']['agent_types']
            
            # Track round progression
            elif event_type == 'agent_action':
                if 'round' in event['data']:
                    data['current_round'] = event['data']['round']
                    data['max_round'] = max(data['max_round'], data['current_round'])
            
            # Count task completions
            elif event_type == 'task_completion':
                if event['data']['success']:
                    data['task_completions_by_round'][data['current_round']] += 1
            
            # Extract cooperation scores
            elif event_type == 'cooperation_scores_aggregated':
                if 'aggregated_scores' in event['data']:
                    data['cooperation_scores'].append(event['data']['aggregated_scores'])
            
            # Count messages
            elif event_type == 'message':
                data['total_messages'] += 1
            
            # Track deception attempts
            elif event_type == 'information_exchange':
                if event['data']['information'].get('manipulation_detected', False):
                    data['deception_attempts'] += 1
    
    # Convert to cumulative task completions
    cumulative_completions = {}
    total = 0
    for round_num in range(1, data['max_round'] + 1):
        total += data['task_completions_by_round'].get(round_num, 0)
        cumulative_completions[round_num] = total
    data['cumulative_completions'] = cumulative_completions
    
    return data


def plot_task_completion_comparison(simulations_dict, round_count):
    """
    Create a plot comparing task completion rates for different numbers of uncooperative agents.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Colors for different uncooperative agent counts
    colors = {0: '#2E7D32', 1: '#FFA726', 2: '#FF6F00', 9: '#C62828'}
    
    # Plot 1: Task completion over rounds
    for uncoop_count, sim_name in sorted(simulations_dict.items()):
        data = extract_simulation_data(sim_name)
        rounds = list(range(1, round_count + 1))
        completions = [data['cumulative_completions'].get(r, 0) for r in rounds]
        
        ax1.plot(rounds, completions, marker='o', linewidth=2, markersize=6,
                label=f'{uncoop_count} Uncooperative', color=colors.get(uncoop_count, '#666'))
    
    ax1.set_xlabel('Round Number', fontsize=12)
    ax1.set_ylabel('Cumulative Tasks Completed', fontsize=12)
    ax1.set_title(f'Task Completion Over Time ({round_count} Rounds)', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(rounds)
    
    # Plot 2: Final task completion bar chart
    uncoop_counts = []
    final_completions = []
    
    for uncoop_count, sim_name in sorted(simulations_dict.items()):
        data = extract_simulation_data(sim_name)
        uncoop_counts.append(uncoop_count)
        final_completions.append(data['cumulative_completions'].get(round_count, 0))
    
    bars = ax2.bar(uncoop_counts, final_completions, 
                   color=[colors.get(c, '#666') for c in uncoop_counts], width=0.6)
    
    # Add value labels on bars
    for bar, val in zip(bars, final_completions):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(val)}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax2.set_xlabel('Number of Uncooperative Agents', fontsize=12)
    ax2.set_ylabel('Total Tasks Completed', fontsize=12)
    ax2.set_title(f'Impact on Total Task Completion ({round_count} Rounds)', fontsize=13, fontweight='bold')
    ax2.set_xticks(uncoop_counts)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Impact of Uncooperative Agents on System Performance', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    # Save the plot
    output_file = f'uncooperative_impact_{round_count}_rounds.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {output_file}")
    plt.close()
    
    return uncoop_counts, final_completions


def plot_cooperation_dynamics(simulations_dict, round_count):
    """
    Analyze and plot cooperation score dynamics.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    colors = {0: '#2E7D32', 1: '#FFA726', 2: '#FF6F00', 9: '#C62828'}
    
    # Collect cooperation and deception data
    uncoop_counts = []
    avg_cooperation = []
    deception_rates = []
    message_counts = []
    
    for uncoop_count, sim_name in sorted(simulations_dict.items()):
        data = extract_simulation_data(sim_name)
        uncoop_counts.append(uncoop_count)
        
        # Calculate average cooperation scores if available
        if data['cooperation_scores']:
            all_scores = []
            for round_scores in data['cooperation_scores']:
                for agent, scores in round_scores.items():
                    if 'average_score_received' in scores:
                        all_scores.append(scores['average_score_received'])
            avg_cooperation.append(np.mean(all_scores) if all_scores else 5.0)
        else:
            avg_cooperation.append(5.0)  # Default neutral score
        
        # Calculate deception rate
        total_exchanges = data['deception_attempts'] + data['total_messages'] // 2  # Rough estimate
        deception_rate = (data['deception_attempts'] / total_exchanges * 100) if total_exchanges > 0 else 0
        deception_rates.append(deception_rate)
        message_counts.append(data['total_messages'])
    
    # Plot 1: Average cooperation scores
    bars1 = ax1.bar(uncoop_counts, avg_cooperation,
                    color=[colors.get(c, '#666') for c in uncoop_counts], width=0.6)
    
    for bar, val in zip(bars1, avg_cooperation):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{val:.1f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax1.set_xlabel('Number of Uncooperative Agents', fontsize=12)
    ax1.set_ylabel('Average Cooperation Score (1-10)', fontsize=12)
    ax1.set_title('Cooperation Levels', fontsize=13, fontweight='bold')
    ax1.set_xticks(uncoop_counts)
    ax1.set_ylim(0, 10)
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.axhline(y=5, color='gray', linestyle='--', alpha=0.5, label='Neutral')
    
    # Plot 2: Communication and deception metrics
    x = np.arange(len(uncoop_counts))
    width = 0.35
    
    # Normalize message counts for visualization
    max_messages = max(message_counts) if message_counts else 1
    normalized_messages = [m/max_messages * 100 for m in message_counts]
    
    bars2 = ax2.bar(x - width/2, normalized_messages, width, label='Communication Activity (%)',
                    color='#1976D2', alpha=0.7)
    bars3 = ax2.bar(x + width/2, deception_rates, width, label='Deception Rate (%)',
                    color='#D32F2F', alpha=0.7)
    
    ax2.set_xlabel('Number of Uncooperative Agents', fontsize=12)
    ax2.set_ylabel('Percentage', fontsize=12)
    ax2.set_title('Communication and Deception Patterns', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(uncoop_counts)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Cooperation and Trust Dynamics', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    # Save the plot
    output_file = f'cooperation_dynamics_{round_count}_rounds.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {output_file}")
    plt.close()


def generate_summary_statistics(simulations_dict, round_count):
    """Generate comprehensive summary statistics."""
    
    print(f"\n{'='*60}")
    print(f"UNCOOPERATIVE AGENTS IMPACT ANALYSIS - {round_count} ROUNDS")
    print(f"{'='*60}\n")
    
    results = {}
    
    for uncoop_count, sim_name in sorted(simulations_dict.items()):
        data = extract_simulation_data(sim_name)
        
        total_tasks = data['cumulative_completions'].get(round_count, 0)
        
        # Calculate performance metrics
        if uncoop_count == 0:
            baseline_tasks = total_tasks
        
        results[uncoop_count] = {
            'total_tasks': total_tasks,
            'messages': data['total_messages'],
            'deception_attempts': data['deception_attempts']
        }
        
        print(f"Uncooperative Agents: {uncoop_count}")
        print(f"  Total Tasks Completed: {total_tasks}")
        print(f"  Total Messages: {data['total_messages']}")
        print(f"  Deception Attempts: {data['deception_attempts']}")
        
        if uncoop_count > 0 and 'baseline_tasks' in locals():
            perf_drop = ((baseline_tasks - total_tasks) / baseline_tasks * 100) if baseline_tasks > 0 else 0
            print(f"  Performance Drop: {perf_drop:.1f}% from baseline")
        print()
    
    return results


def main():
    """Main analysis function."""
    print("=" * 70)
    print("UNCOOPERATIVE AGENTS IMPACT ANALYSIS")
    print("=" * 70)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Analyze 10-round simulations
    print("Analyzing 10-round simulations...")
    uncoop_10, completions_10 = plot_task_completion_comparison(SIMULATIONS_10_ROUNDS, 10)
    plot_cooperation_dynamics(SIMULATIONS_10_ROUNDS, 10)
    results_10 = generate_summary_statistics(SIMULATIONS_10_ROUNDS, 10)
    
    # Analyze 20-round simulations if we have enough data
    if len(SIMULATIONS_20_ROUNDS) >= 2:
        print("\nAnalyzing 20-round simulations...")
        uncoop_20, completions_20 = plot_task_completion_comparison(SIMULATIONS_20_ROUNDS, 20)
        plot_cooperation_dynamics(SIMULATIONS_20_ROUNDS, 20)
        results_20 = generate_summary_statistics(SIMULATIONS_20_ROUNDS, 20)
    else:
        results_20 = None
    
    # Save detailed results to JSON
    detailed_results = {
        'analysis_timestamp': datetime.now().isoformat(),
        '10_round_analysis': {
            'simulations': SIMULATIONS_10_ROUNDS,
            'uncooperative_counts': uncoop_10,
            'final_completions': completions_10,
            'detailed_metrics': results_10
        }
    }
    
    if results_20:
        detailed_results['20_round_analysis'] = {
            'simulations': SIMULATIONS_20_ROUNDS,
            'detailed_metrics': results_20
        }
    
    with open('uncooperative_agents_analysis_results.json', 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("Output files generated:")
    print("  - uncooperative_impact_10_rounds.png")
    print("  - cooperation_dynamics_10_rounds.png")
    if results_20:
        print("  - uncooperative_impact_20_rounds.png")
        print("  - cooperation_dynamics_20_rounds.png")
    print("  - uncooperative_agents_analysis_results.json")
    
    # Key insights
    print("\n" + "=" * 70)
    print("KEY INSIGHTS")
    print("=" * 70)
    
    if len(uncoop_10) > 2:
        # Calculate performance degradation
        baseline = completions_10[0]
        one_uncoop = completions_10[1] if len(completions_10) > 1 else baseline
        two_uncoop = completions_10[2] if len(completions_10) > 2 else baseline
        nine_uncoop = completions_10[-1] if uncoop_10[-1] == 9 else baseline
        
        print(f"\n10-Round Simulations:")
        print(f"  Baseline (0 uncooperative): {baseline} tasks")
        print(f"  1 uncooperative agent: {one_uncoop} tasks ({((one_uncoop-baseline)/baseline*100):.1f}% change)")
        print(f"  2 uncooperative agents: {two_uncoop} tasks ({((two_uncoop-baseline)/baseline*100):.1f}% change)")
        if uncoop_10[-1] == 9:
            print(f"  9 uncooperative agents: {nine_uncoop} tasks ({((nine_uncoop-baseline)/baseline*100):.1f}% change)")


if __name__ == "__main__":
    main()
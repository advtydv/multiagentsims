#!/usr/bin/env python3
"""
Analysis script for partial sweep results.
Works with whatever simulations successfully completed.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime

BASE_PATH = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation/logs')

# Map of actual completed simulations
COMPLETED_SIMULATIONS = {
    0: 'simulation_20250813_004508',
    6: 'simulation_20250813_011935',
    7: 'simulation_20250813_012055',
    8: 'simulation_20250813_012150',
    9: 'simulation_20250813_012230',
    10: 'simulation_20250813_012310'
}

def extract_simulation_metrics(sim_path):
    """Extract key metrics from a simulation."""
    log_file = BASE_PATH / sim_path / 'simulation_log.jsonl'
    if not log_file.exists():
        return None
    
    metrics = {
        'task_completions': 0,
        'messages': 0,
        'deception_attempts': 0,
        'completions_by_round': defaultdict(int),
        'first_completion_round': None,
        'last_completion_round': None
    }
    
    current_round = 1
    
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            if event['event_type'] == 'agent_action' and 'round' in event['data']:
                current_round = event['data']['round']
            
            elif event['event_type'] == 'task_completion' and event['data']['success']:
                metrics['task_completions'] += 1
                metrics['completions_by_round'][current_round] += 1
                
                if metrics['first_completion_round'] is None:
                    metrics['first_completion_round'] = current_round
                metrics['last_completion_round'] = current_round
            
            elif event['event_type'] == 'message':
                metrics['messages'] += 1
            
            elif event['event_type'] == 'information_exchange':
                if event['data']['information'].get('manipulation_detected', False):
                    metrics['deception_attempts'] += 1
    
    return metrics

def analyze_partial_results():
    """Analyze the partial sweep results."""
    print("="*70)
    print("ANALYSIS OF PARTIAL SWEEP RESULTS")
    print("="*70)
    print(f"Successfully completed simulations: {len(COMPLETED_SIMULATIONS)}/11")
    print(f"Uncooperative agent counts: {sorted(COMPLETED_SIMULATIONS.keys())}")
    print()
    
    # Extract metrics
    analysis_data = {}
    for uncoop_count, sim_name in COMPLETED_SIMULATIONS.items():
        print(f"Processing simulation with {uncoop_count} uncooperative agents...")
        metrics = extract_simulation_metrics(sim_name)
        if metrics:
            analysis_data[uncoop_count] = metrics
            print(f"  ✓ Tasks completed: {metrics['task_completions']}")
    
    if not analysis_data:
        print("No valid data to analyze!")
        return
    
    # Prepare data for plotting
    uncoop_counts = sorted(analysis_data.keys())
    task_completions = [analysis_data[u]['task_completions'] for u in uncoop_counts]
    messages = [analysis_data[u]['messages'] for u in uncoop_counts]
    deceptions = [analysis_data[u]['deception_attempts'] for u in uncoop_counts]
    
    # Create visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Task completions
    ax1.scatter(uncoop_counts, task_completions, s=100, c='red', alpha=0.7)
    ax1.plot(uncoop_counts, task_completions, 'r--', alpha=0.5)
    
    # Add value labels
    for x, y in zip(uncoop_counts, task_completions):
        ax1.annotate(str(y), (x, y), textcoords="offset points", xytext=(0,5), ha='center')
    
    ax1.set_xlabel('Number of Uncooperative Agents')
    ax1.set_ylabel('Total Tasks Completed')
    ax1.set_title('Task Completion vs Uncooperative Agents')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(range(0, 11))
    
    # Plot 2: Performance drop
    baseline = task_completions[0] if 0 in uncoop_counts else max(task_completions)
    performance_drops = [(baseline - t) / baseline * 100 if baseline > 0 else 0 
                        for t in task_completions]
    
    colors = ['green' if p <= 30 else 'orange' if p <= 60 else 'red' for p in performance_drops]
    ax2.bar(uncoop_counts, performance_drops, color=colors, alpha=0.7)
    
    # Add value labels
    for x, y in zip(uncoop_counts, performance_drops):
        ax2.text(x, y + 1, f'{y:.0f}%', ha='center', fontweight='bold')
    
    ax2.set_xlabel('Number of Uncooperative Agents')
    ax2.set_ylabel('Performance Drop (%)')
    ax2.set_title('Performance Degradation from Baseline')
    ax2.axhline(y=50, color='orange', linestyle='--', alpha=0.5)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xticks(range(0, 11))
    
    # Plot 3: Messages and deception
    ax3.plot(uncoop_counts, messages, 'o-', color='blue', label='Total Messages')
    ax3.set_xlabel('Number of Uncooperative Agents')
    ax3.set_ylabel('Message Count', color='blue')
    ax3.tick_params(axis='y', labelcolor='blue')
    ax3.grid(True, alpha=0.3)
    ax3.set_xticks(range(0, 11))
    
    ax3_twin = ax3.twinx()
    ax3_twin.plot(uncoop_counts, deceptions, 's-', color='red', label='Deception Attempts')
    ax3_twin.set_ylabel('Deception Attempts', color='red')
    ax3_twin.tick_params(axis='y', labelcolor='red')
    
    ax3.set_title('Communication and Deception Patterns')
    
    # Plot 4: Efficiency
    efficiency = [t/m * 100 if m > 0 else 0 for t, m in zip(task_completions, messages)]
    ax4.plot(uncoop_counts, efficiency, 'o-', color='purple')
    
    # Add value labels
    for x, y in zip(uncoop_counts, efficiency):
        ax4.annotate(f'{y:.1f}', (x, y), textcoords="offset points", xytext=(0,5), ha='center')
    
    ax4.set_xlabel('Number of Uncooperative Agents')
    ax4.set_ylabel('Efficiency (Tasks per 100 Messages)')
    ax4.set_title('System Efficiency')
    ax4.grid(True, alpha=0.3)
    ax4.set_xticks(range(0, 11))
    
    plt.suptitle('Partial Sweep Analysis: Impact of Uncooperative Agents (10 Rounds)', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    output_file = 'partial_sweep_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nSaved analysis plot to {output_file}")
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    print("\nTask Completions:")
    for u in uncoop_counts:
        drop = (baseline - analysis_data[u]['task_completions']) / baseline * 100 if baseline > 0 else 0
        print(f"  {u} uncooperative: {analysis_data[u]['task_completions']} tasks ({drop:.1f}% drop)")
    
    print("\nKey Observations:")
    print(f"  Baseline (0 uncooperative): {baseline} tasks")
    print(f"  50% degradation occurs between: {uncoop_counts[-2]} and {uncoop_counts[-1]} agents")
    
    # Calculate approximate trends
    if len(uncoop_counts) > 2:
        # Simple linear regression on available points
        x = np.array(uncoop_counts)
        y = np.array(task_completions)
        slope, intercept = np.polyfit(x, y, 1)
        print(f"\nLinear trend (approximate):")
        print(f"  Each uncooperative agent reduces completion by ~{abs(slope):.1f} tasks")
        print(f"  Projected total failure at ~{abs(intercept/slope):.0f} uncooperative agents")
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'completed_simulations': list(COMPLETED_SIMULATIONS.keys()),
        'metrics': {k: {
            'task_completions': v['task_completions'],
            'messages': v['messages'],
            'deception_attempts': v['deception_attempts']
        } for k, v in analysis_data.items()},
        'performance_drops': dict(zip(uncoop_counts, performance_drops)),
        'efficiency': dict(zip(uncoop_counts, efficiency))
    }
    
    with open('partial_sweep_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to partial_sweep_results.json")

if __name__ == "__main__":
    analyze_partial_results()
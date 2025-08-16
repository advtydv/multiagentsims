#!/usr/bin/env python3
"""
Fixed analysis script that handles nested simulation directories.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from scipy import stats
import glob

BASE_PATH = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation/logs')

# Map the actual simulation locations
ACTUAL_SIMULATIONS = {
    0: 'simulation_20250813_004508',
    1: 'simulation_20250813_081757362_u1/simulation_20250813_081758',
    2: 'simulation_20250813_081757462_u2/simulation_20250813_082847',
    3: 'simulation_20250813_081757563_u3/simulation_20250813_083843',
    4: 'simulation_20250813_081757660_u4/simulation_20250813_084749',
    5: 'simulation_20250813_081757763_u5/simulation_20250813_085637',
    6: 'simulation_20250813_011935',
    7: 'simulation_20250813_012055',
    8: 'simulation_20250813_012150',
    9: 'simulation_20250813_012230',
    10: 'simulation_20250813_012310'
}

def find_nested_simulations():
    """Find the actual simulation directories in nested structures."""
    simulations = {}
    
    # Known good simulations
    simulations[0] = 'simulation_20250813_004508'
    simulations[6] = 'simulation_20250813_011935'
    simulations[7] = 'simulation_20250813_012055'
    simulations[8] = 'simulation_20250813_012150'
    simulations[9] = 'simulation_20250813_012230'
    simulations[10] = 'simulation_20250813_012310'
    
    # Find nested simulations for 1-5
    for i in range(1, 6):
        parent_pattern = f'simulation_*_u{i}'
        parent_dirs = list(BASE_PATH.glob(parent_pattern))
        
        if parent_dirs:
            parent_dir = parent_dirs[0]
            # Look for nested simulation directory
            nested = list(parent_dir.glob('simulation_*'))
            if nested:
                # Get relative path from BASE_PATH
                rel_path = nested[0].relative_to(BASE_PATH)
                simulations[i] = str(rel_path)
                print(f"Found simulation for {i} uncooperative: {rel_path}")
    
    return simulations

def extract_simulation_metrics(sim_path):
    """Extract key metrics from a simulation."""
    log_file = BASE_PATH / sim_path / 'simulation_log.jsonl'
    
    if not log_file.exists():
        print(f"  Warning: Log file not found at {log_file}")
        return None
    
    metrics = {
        'task_completions': 0,
        'messages': 0,
        'deception_attempts': 0,
        'completions_by_round': defaultdict(int),
        'first_completion_round': None,
        'last_completion_round': None,
        'rounds_with_completions': 0
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
    
    metrics['rounds_with_completions'] = len(metrics['completions_by_round'])
    return metrics

def analyze_complete_results():
    """Analyze the complete sweep results."""
    print("="*70)
    print("COMPLETE SWEEP ANALYSIS: IMPACT OF UNCOOPERATIVE AGENTS")
    print("="*70)
    
    # Find actual simulation locations
    print("\nLocating all simulations...")
    all_simulations = find_nested_simulations()
    
    print(f"\nFound {len(all_simulations)} simulations")
    print(f"Uncooperative agent counts: {sorted(all_simulations.keys())}")
    print()
    
    # Extract metrics for all simulations
    analysis_data = {}
    for uncoop_count in sorted(all_simulations.keys()):
        sim_path = all_simulations[uncoop_count]
        print(f"Processing {uncoop_count} uncooperative agents...")
        metrics = extract_simulation_metrics(sim_path)
        if metrics:
            analysis_data[uncoop_count] = metrics
            print(f"  ✓ Tasks: {metrics['task_completions']}, Messages: {metrics['messages']}")
    
    print(f"\nSuccessfully analyzed {len(analysis_data)}/11 simulations")
    
    if len(analysis_data) < 11:
        print("\nMissing data for:", [i for i in range(11) if i not in analysis_data])
    
    # Prepare data for analysis
    uncoop_counts = sorted(analysis_data.keys())
    task_completions = [analysis_data[u]['task_completions'] for u in uncoop_counts]
    messages = [analysis_data[u]['messages'] for u in uncoop_counts]
    deceptions = [analysis_data[u]['deception_attempts'] for u in uncoop_counts]
    
    # Statistical analysis
    baseline = task_completions[0] if 0 in uncoop_counts else max(task_completions)
    performance_drops = [(baseline - t) / baseline * 100 if baseline > 0 else 0 
                        for t in task_completions]
    
    # Create comprehensive visualization
    fig = plt.figure(figsize=(18, 12))
    
    # Plot 1: Task completion with fitted curves
    ax1 = plt.subplot(2, 3, 1)
    ax1.scatter(uncoop_counts, task_completions, s=120, c='red', alpha=0.8, zorder=5, label='Actual')
    
    # Fit curves if we have enough data
    if len(uncoop_counts) >= 3:
        poly2_fit = np.polyfit(uncoop_counts, task_completions, min(2, len(uncoop_counts)-1))
        x_smooth = np.linspace(min(uncoop_counts), max(uncoop_counts), 100)
        poly2_smooth = np.polyval(poly2_fit, x_smooth)
        ax1.plot(x_smooth, poly2_smooth, 'b-', alpha=0.6, linewidth=2, label='Fitted curve')
    
    # Add value labels
    for x, y in zip(uncoop_counts, task_completions):
        ax1.annotate(str(y), (x, y), textcoords="offset points", xytext=(0,8), 
                    ha='center', fontweight='bold')
    
    ax1.set_xlabel('Number of Uncooperative Agents', fontsize=11)
    ax1.set_ylabel('Total Tasks Completed', fontsize=11)
    ax1.set_title('Task Completion vs Disruption', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-0.5, 10.5)
    
    # Plot 2: Performance degradation
    ax2 = plt.subplot(2, 3, 2)
    colors = ['green' if p <= 30 else 'orange' if p <= 60 else 'red' for p in performance_drops]
    bars = ax2.bar(uncoop_counts, performance_drops, color=colors, alpha=0.7, edgecolor='black')
    
    for bar, val in zip(bars, performance_drops):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{int(val)}%', ha='center', fontweight='bold', fontsize=9)
    
    ax2.set_xlabel('Number of Uncooperative Agents', fontsize=11)
    ax2.set_ylabel('Performance Drop (%)', fontsize=11)
    ax2.set_title('Performance Degradation from Baseline', fontsize=12, fontweight='bold')
    ax2.axhline(y=30, color='orange', linestyle='--', alpha=0.5, linewidth=1)
    ax2.axhline(y=60, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Communication patterns
    ax3 = plt.subplot(2, 3, 3)
    ax3.plot(uncoop_counts, messages, 'o-', color='#1976D2', linewidth=2, markersize=8)
    ax3.set_xlabel('Number of Uncooperative Agents', fontsize=11)
    ax3.set_ylabel('Total Messages', color='#1976D2', fontsize=11)
    ax3.tick_params(axis='y', labelcolor='#1976D2')
    ax3.grid(True, alpha=0.3)
    
    ax3_twin = ax3.twinx()
    ax3_twin.plot(uncoop_counts, deceptions, 's-', color='#D32F2F', linewidth=2, markersize=8)
    ax3_twin.set_ylabel('Deception Attempts', color='#D32F2F', fontsize=11)
    ax3_twin.tick_params(axis='y', labelcolor='#D32F2F')
    
    ax3.set_title('Communication & Deception', fontsize=12, fontweight='bold')
    
    # Plot 4: Efficiency metrics
    ax4 = plt.subplot(2, 3, 4)
    efficiency = [t/m * 100 if m > 0 else 0 for t, m in zip(task_completions, messages)]
    ax4.plot(uncoop_counts, efficiency, 'o-', color='purple', linewidth=2, markersize=8)
    
    for x, y in zip(uncoop_counts, efficiency):
        ax4.annotate(f'{y:.1f}', (x, y), textcoords="offset points", xytext=(0,5), 
                    ha='center', fontsize=9)
    
    ax4.set_xlabel('Number of Uncooperative Agents', fontsize=11)
    ax4.set_ylabel('Efficiency (Tasks per 100 Messages)', fontsize=11)
    ax4.set_title('System Efficiency', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Deception rate
    ax5 = plt.subplot(2, 3, 5)
    deception_rate = [d/m * 100 if m > 0 else 0 for d, m in zip(deceptions, messages)]
    bars = ax5.bar(uncoop_counts, deception_rate, color='darkred', alpha=0.7, edgecolor='black')
    
    for bar, val in zip(bars, deception_rate):
        if val > 0:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                    f'{val:.1f}%', ha='center', fontsize=9)
    
    ax5.set_xlabel('Number of Uncooperative Agents', fontsize=11)
    ax5.set_ylabel('Deception Rate (% of Messages)', fontsize=11)
    ax5.set_title('Trust Degradation', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Plot 6: Task completion over rounds (heatmap style)
    ax6 = plt.subplot(2, 3, 6)
    rounds_data = np.zeros((len(uncoop_counts), 10))  # 10 rounds
    for i, u in enumerate(uncoop_counts):
        for r in range(1, 11):
            rounds_data[i, r-1] = analysis_data[u]['completions_by_round'].get(r, 0)
    
    im = ax6.imshow(rounds_data, cmap='YlOrRd', aspect='auto')
    ax6.set_xticks(range(10))
    ax6.set_xticklabels(range(1, 11))
    ax6.set_yticks(range(len(uncoop_counts)))
    ax6.set_yticklabels(uncoop_counts)
    ax6.set_xlabel('Round', fontsize=11)
    ax6.set_ylabel('Uncooperative Agents', fontsize=11)
    ax6.set_title('Task Completions by Round', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax6)
    
    plt.suptitle('Complete Analysis: Impact of Uncooperative Agents (10 Rounds)', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    output_file = 'complete_sweep_analysis_fixed.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nSaved analysis plot to {output_file}")
    plt.close()
    
    # Print detailed statistics
    print("\n" + "="*60)
    print("DETAILED STATISTICS")
    print("="*60)
    
    print("\nTask Completion by Uncooperative Count:")
    for u in uncoop_counts:
        drop = performance_drops[uncoop_counts.index(u)]
        print(f"  {u:2d} agents: {analysis_data[u]['task_completions']:3d} tasks ({drop:5.1f}% drop)")
    
    # Key findings
    print(f"\nKey Findings:")
    print(f"  Baseline (0 uncooperative): {baseline} tasks")
    
    if len(analysis_data) == 11:
        # Find worst performance
        worst_idx = np.argmin(task_completions)
        worst_uncoop = uncoop_counts[worst_idx]
        worst_tasks = task_completions[worst_idx]
        print(f"  Worst performance: {worst_uncoop} uncooperative ({worst_tasks} tasks)")
        
        # Check for non-monotonic behavior
        is_monotonic = all(task_completions[i] >= task_completions[i+1] 
                          for i in range(len(task_completions)-1))
        if not is_monotonic:
            print(f"  ⚠️ Non-monotonic degradation detected!")
            for i in range(1, len(task_completions)):
                if task_completions[i] > task_completions[i-1]:
                    print(f"    Recovery at {uncoop_counts[i]} agents: "
                         f"+{task_completions[i] - task_completions[i-1]} tasks")
    
    # Save complete results
    results = {
        'timestamp': datetime.now().isoformat(),
        'simulations': all_simulations,
        'uncoop_counts': uncoop_counts,
        'metrics': {
            'task_completions': task_completions,
            'messages': messages,
            'deceptions': deceptions,
            'performance_drops': performance_drops,
            'efficiency': efficiency,
            'deception_rate': deception_rate
        },
        'detailed_metrics': {str(k): v for k, v in analysis_data.items()}
    }
    
    with open('complete_sweep_analysis_results_fixed.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to complete_sweep_analysis_results_fixed.json")
    
    return results

if __name__ == "__main__":
    analyze_complete_results()
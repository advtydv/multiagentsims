#!/usr/bin/env python3
"""
Complete analysis script for all 11 simulations (0-10 uncooperative agents).
Combines existing and newly run simulations for comprehensive analysis.
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

def find_latest_combined_metadata():
    """Find the most recent combined metadata file."""
    metadata_files = list(BASE_PATH.glob('combined_sweep_metadata_*.json'))
    if not metadata_files:
        return None
    return max(metadata_files, key=lambda p: p.stat().st_mtime)

def extract_simulation_metrics(sim_path):
    """Extract key metrics from a simulation."""
    log_file = BASE_PATH / sim_path / 'simulation_log.jsonl'
    if not log_file.exists():
        print(f"  Warning: Log file not found for {sim_path}")
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
    
    # Load combined metadata
    metadata_file = find_latest_combined_metadata()
    if not metadata_file:
        print("Error: No combined metadata file found!")
        print("Please run 'python run_missing_simulations.py' first.")
        return
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    all_simulations = metadata['all_simulations']
    
    # Convert string keys to integers
    all_simulations = {int(k): v for k, v in all_simulations.items()}
    
    print(f"Loaded metadata from: {metadata_file.name}")
    print(f"Total simulations: {len(all_simulations)}")
    print(f"Uncooperative agent counts: {sorted(all_simulations.keys())}")
    print()
    
    # Extract metrics for all simulations
    analysis_data = {}
    for uncoop_count in sorted(all_simulations.keys()):
        sim_name = all_simulations[uncoop_count]
        print(f"Processing {uncoop_count} uncooperative agents ({sim_name})...")
        metrics = extract_simulation_metrics(sim_name)
        if metrics:
            analysis_data[uncoop_count] = metrics
            print(f"  ✓ Tasks: {metrics['task_completions']}, Messages: {metrics['messages']}")
    
    if len(analysis_data) < 11:
        print(f"\nWarning: Only {len(analysis_data)}/11 simulations have valid data")
    
    # Prepare data for analysis
    uncoop_counts = sorted(analysis_data.keys())
    task_completions = [analysis_data[u]['task_completions'] for u in uncoop_counts]
    messages = [analysis_data[u]['messages'] for u in uncoop_counts]
    deceptions = [analysis_data[u]['deception_attempts'] for u in uncoop_counts]
    
    # Statistical analysis
    baseline = task_completions[0] if 0 in uncoop_counts else max(task_completions)
    performance_drops = [(baseline - t) / baseline * 100 if baseline > 0 else 0 
                        for t in task_completions]
    
    # Fit regression models
    poly2_fit = np.polyfit(uncoop_counts, task_completions, 2)
    poly3_fit = np.polyfit(uncoop_counts, task_completions, 3)
    linear_fit = np.polyfit(uncoop_counts, task_completions, 1)
    
    # Calculate R-squared values
    poly2_pred = np.polyval(poly2_fit, uncoop_counts)
    poly3_pred = np.polyval(poly3_fit, uncoop_counts)
    linear_pred = np.polyval(linear_fit, uncoop_counts)
    
    ss_tot = np.sum((task_completions - np.mean(task_completions)) ** 2)
    r2_poly2 = 1 - np.sum((task_completions - poly2_pred) ** 2) / ss_tot if ss_tot > 0 else 0
    r2_poly3 = 1 - np.sum((task_completions - poly3_pred) ** 2) / ss_tot if ss_tot > 0 else 0
    r2_linear = 1 - np.sum((task_completions - linear_pred) ** 2) / ss_tot if ss_tot > 0 else 0
    
    # Create comprehensive visualization
    fig = plt.figure(figsize=(18, 12))
    
    # Plot 1: Task completion with fitted curves
    ax1 = plt.subplot(2, 3, 1)
    ax1.scatter(uncoop_counts, task_completions, s=120, c='red', alpha=0.8, zorder=5, label='Actual')
    
    # Plot fitted curves
    x_smooth = np.linspace(0, 10, 100)
    if r2_poly3 > r2_poly2 * 1.1:  # Use cubic if significantly better
        best_fit = np.polyval(poly3_fit, x_smooth)
        ax1.plot(x_smooth, best_fit, 'b-', alpha=0.6, linewidth=2,
                label=f'Best fit (Cubic, R²={r2_poly3:.3f})')
    else:
        best_fit = np.polyval(poly2_fit, x_smooth)
        ax1.plot(x_smooth, best_fit, 'b-', alpha=0.6, linewidth=2,
                label=f'Best fit (Quadratic, R²={r2_poly2:.3f})')
    
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
    
    # Add value labels
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
    ax2.set_xlim(-0.5, 10.5)
    
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
    ax3.set_xlim(-0.5, 10.5)
    
    # Plot 4: Efficiency metrics
    ax4 = plt.subplot(2, 3, 4)
    efficiency = [t/m * 100 if m > 0 else 0 for t, m in zip(task_completions, messages)]
    ax4.plot(uncoop_counts, efficiency, 'o-', color='purple', linewidth=2, markersize=8)
    
    # Add value labels
    for x, y in zip(uncoop_counts, efficiency):
        ax4.annotate(f'{y:.1f}', (x, y), textcoords="offset points", xytext=(0,5), 
                    ha='center', fontsize=9)
    
    ax4.set_xlabel('Number of Uncooperative Agents', fontsize=11)
    ax4.set_ylabel('Efficiency (Tasks per 100 Messages)', fontsize=11)
    ax4.set_title('System Efficiency', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(-0.5, 10.5)
    
    # Plot 5: Deception rate
    ax5 = plt.subplot(2, 3, 5)
    deception_rate = [d/m * 100 if m > 0 else 0 for d, m in zip(deceptions, messages)]
    bars = ax5.bar(uncoop_counts, deception_rate, color='darkred', alpha=0.7, edgecolor='black')
    
    # Add value labels
    for bar, val in zip(bars, deception_rate):
        if val > 0:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                    f'{val:.1f}%', ha='center', fontsize=9)
    
    ax5.set_xlabel('Number of Uncooperative Agents', fontsize=11)
    ax5.set_ylabel('Deception Rate (% of Messages)', fontsize=11)
    ax5.set_title('Trust Degradation', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    ax5.set_xlim(-0.5, 10.5)
    
    # Plot 6: Marginal impact
    ax6 = plt.subplot(2, 3, 6)
    if len(uncoop_counts) > 1:
        marginal_impact = []
        for i in range(1, len(task_completions)):
            prev_uncoop = uncoop_counts[i-1]
            curr_uncoop = uncoop_counts[i]
            task_change = task_completions[i] - task_completions[i-1]
            uncoop_change = curr_uncoop - prev_uncoop
            marginal = task_change / uncoop_change if uncoop_change > 0 else 0
            marginal_impact.append(marginal)
        
        x_marginal = [(uncoop_counts[i] + uncoop_counts[i-1])/2 for i in range(1, len(uncoop_counts))]
        ax6.bar(x_marginal, marginal_impact, width=0.8, 
               color=['red' if m < 0 else 'green' for m in marginal_impact], 
               alpha=0.7, edgecolor='black')
        
        ax6.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax6.set_xlabel('Uncooperative Agents (midpoint)', fontsize=11)
        ax6.set_ylabel('Marginal Task Change', fontsize=11)
        ax6.set_title('Marginal Impact Analysis', fontsize=12, fontweight='bold')
        ax6.grid(True, alpha=0.3)
    
    plt.suptitle('Complete Analysis: Impact of Uncooperative Agents on System Performance (10 Rounds)', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    output_file = 'complete_sweep_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nSaved comprehensive analysis plot to {output_file}")
    plt.close()
    
    # Print detailed statistics
    print("\n" + "="*60)
    print("DETAILED STATISTICS")
    print("="*60)
    
    print("\nTask Completion by Uncooperative Count:")
    for u in uncoop_counts:
        drop = performance_drops[uncoop_counts.index(u)]
        print(f"  {u:2d} agents: {analysis_data[u]['task_completions']:3d} tasks ({drop:5.1f}% drop)")
    
    print(f"\nRegression Analysis:")
    print(f"  Linear:    R² = {r2_linear:.3f}")
    print(f"  Quadratic: R² = {r2_poly2:.3f}")
    print(f"  Cubic:     R² = {r2_poly3:.3f}")
    
    # Identify interesting patterns
    print(f"\nKey Findings:")
    print(f"  Baseline (0 uncooperative): {baseline} tasks")
    
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
        # Find recovery points
        for i in range(1, len(task_completions)):
            if task_completions[i] > task_completions[i-1]:
                print(f"    Recovery at {uncoop_counts[i]} agents: "
                     f"+{task_completions[i] - task_completions[i-1]} tasks")
    
    # Save complete results
    results = {
        'timestamp': datetime.now().isoformat(),
        'metadata_source': str(metadata_file.name),
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
        'regression': {
            'linear': {'coefficients': linear_fit.tolist(), 'r2': r2_linear},
            'quadratic': {'coefficients': poly2_fit.tolist(), 'r2': r2_poly2},
            'cubic': {'coefficients': poly3_fit.tolist(), 'r2': r2_poly3}
        },
        'key_findings': {
            'baseline_tasks': baseline,
            'worst_performance': {'uncoop_count': worst_uncoop, 'tasks': worst_tasks},
            'is_monotonic': is_monotonic
        }
    }
    
    with open('complete_sweep_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to complete_sweep_analysis_results.json")
    
    return results

if __name__ == "__main__":
    analyze_complete_results()
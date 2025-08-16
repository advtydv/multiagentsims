#!/usr/bin/env python3
"""
Final Comprehensive Analysis of Uncooperative Agents Impact
Includes all 11 simulations with confidence intervals and advanced statistics
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from scipy import stats
from scipy.interpolate import make_interp_spline
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')

BASE_PATH = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation/logs')

# Complete simulation mapping
COMPLETE_SIMULATIONS = {
    0: 'simulation_20250813_004508',
    1: 'simulation_20250813_081757362_u1/simulation_20250813_081758',
    2: 'simulation_20250813_081757462_u2/simulation_20250813_081758',
    3: 'simulation_20250813_081757563_u3/simulation_20250813_081758',
    4: 'simulation_20250813_081757660_u4/simulation_20250813_081758',
    5: 'simulation_20250813_081757763_u5/simulation_20250813_081758',
    6: 'simulation_20250813_011935',
    7: 'simulation_20250813_012055',
    8: 'simulation_20250813_012150',
    9: 'simulation_20250813_012230',
    10: 'simulation_20250813_012310'
}


def extract_simulation_metrics(sim_path):
    """Extract comprehensive metrics from a simulation."""
    log_file = BASE_PATH / sim_path / 'simulation_log.jsonl'
    
    if not log_file.exists():
        return None
    
    metrics = {
        'task_completions': 0,
        'messages': 0,
        'deception_attempts': 0,
        'completions_by_round': defaultdict(int),
        'completions_timeline': [],  # (round, cumulative_count)
        'first_completion_round': None,
        'last_completion_round': None,
        'cooperation_scores': [],
        'unique_agents_completing': set(),
        'message_types': defaultdict(int)
    }
    
    current_round = 1
    cumulative_tasks = 0
    
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            event_type = event.get('event_type')
            
            if event_type == 'agent_action' and 'round' in event['data']:
                new_round = event['data']['round']
                if new_round != current_round:
                    metrics['completions_timeline'].append((current_round, cumulative_tasks))
                    current_round = new_round
            
            elif event_type == 'task_completion' and event['data']['success']:
                metrics['task_completions'] += 1
                cumulative_tasks += 1
                metrics['completions_by_round'][current_round] += 1
                metrics['unique_agents_completing'].add(event['data'].get('agent_id', 'unknown'))
                
                if metrics['first_completion_round'] is None:
                    metrics['first_completion_round'] = current_round
                metrics['last_completion_round'] = current_round
            
            elif event_type == 'message':
                metrics['messages'] += 1
                msg_type = event['data'].get('type', 'unknown')
                metrics['message_types'][msg_type] += 1
            
            elif event_type == 'information_exchange':
                if event['data']['information'].get('manipulation_detected', False):
                    metrics['deception_attempts'] += 1
            
            elif event_type == 'cooperation_scores_aggregated':
                if 'aggregated_scores' in event['data']:
                    # Extract average cooperation scores
                    scores = []
                    for agent, data in event['data']['aggregated_scores'].items():
                        if 'average_score_received' in data:
                            scores.append(data['average_score_received'])
                    if scores:
                        metrics['cooperation_scores'].append(np.mean(scores))
    
    # Final timeline entry
    metrics['completions_timeline'].append((current_round, cumulative_tasks))
    metrics['unique_agents_count'] = len(metrics['unique_agents_completing'])
    
    return metrics


def calculate_confidence_intervals(data, confidence=0.95):
    """Calculate confidence intervals using bootstrap method."""
    if len(data) < 2:
        return np.mean(data) if data else 0, 0, 0
    
    n_bootstrap = 1000
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_means.append(np.mean(sample))
    
    mean = np.mean(data)
    ci_lower = np.percentile(bootstrap_means, (1 - confidence) / 2 * 100)
    ci_upper = np.percentile(bootstrap_means, (1 + confidence) / 2 * 100)
    
    return mean, ci_lower, ci_upper


def perform_statistical_tests(task_completions, uncoop_counts):
    """Perform various statistical tests on the data."""
    results = {}
    
    # Normality test
    if len(task_completions) >= 3:
        _, p_normal = stats.shapiro(task_completions)
        results['normality_p_value'] = p_normal
        results['is_normal'] = p_normal > 0.05
    
    # Correlation analysis
    if len(task_completions) >= 3:
        pearson_r, pearson_p = stats.pearsonr(uncoop_counts, task_completions)
        spearman_r, spearman_p = stats.spearmanr(uncoop_counts, task_completions)
        results['pearson'] = {'r': pearson_r, 'p': pearson_p}
        results['spearman'] = {'r': spearman_r, 'p': spearman_p}
    
    # Regression analysis with different models
    if len(uncoop_counts) >= 4:
        # Linear
        linear_fit = np.polyfit(uncoop_counts, task_completions, 1)
        linear_pred = np.polyval(linear_fit, uncoop_counts)
        
        # Quadratic
        quad_fit = np.polyfit(uncoop_counts, task_completions, 2)
        quad_pred = np.polyval(quad_fit, uncoop_counts)
        
        # Cubic
        cubic_fit = np.polyfit(uncoop_counts, task_completions, 3)
        cubic_pred = np.polyval(cubic_fit, uncoop_counts)
        
        # Calculate R-squared for each
        ss_tot = np.sum((task_completions - np.mean(task_completions)) ** 2)
        
        results['linear'] = {
            'coefficients': linear_fit.tolist(),
            'r2': 1 - np.sum((task_completions - linear_pred) ** 2) / ss_tot if ss_tot > 0 else 0,
            'rmse': np.sqrt(np.mean((task_completions - linear_pred) ** 2))
        }
        
        results['quadratic'] = {
            'coefficients': quad_fit.tolist(),
            'r2': 1 - np.sum((task_completions - quad_pred) ** 2) / ss_tot if ss_tot > 0 else 0,
            'rmse': np.sqrt(np.mean((task_completions - quad_pred) ** 2))
        }
        
        results['cubic'] = {
            'coefficients': cubic_fit.tolist(),
            'r2': 1 - np.sum((task_completions - cubic_pred) ** 2) / ss_tot if ss_tot > 0 else 0,
            'rmse': np.sqrt(np.mean((task_completions - cubic_pred) ** 2))
        }
    
    return results


def create_comprehensive_visualizations(analysis_data):
    """Create comprehensive visualizations with all requested plots."""
    
    # Prepare data
    uncoop_counts = sorted(analysis_data.keys())
    task_completions = [analysis_data[u]['task_completions'] for u in uncoop_counts]
    messages = [analysis_data[u]['messages'] for u in uncoop_counts]
    deceptions = [analysis_data[u]['deception_attempts'] for u in uncoop_counts]
    unique_agents = [analysis_data[u]['unique_agents_count'] for u in uncoop_counts]
    
    # Calculate derived metrics
    baseline = task_completions[0]
    performance_drops = [(baseline - t) / baseline * 100 if baseline > 0 else 0 for t in task_completions]
    efficiency = [t/m * 100 if m > 0 else 0 for t, m in zip(task_completions, messages)]
    deception_rate = [d/m * 100 if m > 0 else 0 for d, m in zip(deceptions, messages)]
    
    # Perform statistical analysis
    stats_results = perform_statistical_tests(task_completions, uncoop_counts)
    
    # Create figure with subplots (now 13 plots total)
    fig = plt.figure(figsize=(22, 18))
    
    # ========== MAIN PLOT: Simple Task Completion (as requested) ==========
    ax_main = plt.subplot(4, 4, (1, 2))  # Span two columns for emphasis
    
    # Plot the main relationship clearly
    ax_main.plot(uncoop_counts, task_completions, 'o-', color='darkblue', 
                linewidth=3, markersize=12, markeredgewidth=2, 
                markeredgecolor='white', markerfacecolor='darkblue')
    
    # Add value labels
    for x, y in zip(uncoop_counts, task_completions):
        ax_main.annotate(str(y), (x, y), textcoords="offset points", 
                        xytext=(0, 10), ha='center', fontweight='bold', 
                        fontsize=11, color='darkblue')
    
    # Highlight baseline and extremes
    ax_main.axhline(y=baseline, color='gray', linestyle='--', alpha=0.5, 
                   linewidth=1, label=f'Baseline ({baseline} tasks)')
    
    # Mark the improvement zone
    ax_main.axvspan(-0.5, 3.5, alpha=0.1, color='green', label='Improvement Zone')
    ax_main.axvspan(3.5, 6.5, alpha=0.1, color='red', label='Danger Zone')
    ax_main.axvspan(6.5, 10.5, alpha=0.1, color='blue', label='Recovery Zone')
    
    ax_main.set_xlabel('Number of Uncooperative Agents', fontsize=12, fontweight='bold')
    ax_main.set_ylabel('Total Tasks Completed', fontsize=12, fontweight='bold')
    ax_main.set_title('Primary Result: Task Completion vs Uncooperative Agents', 
                     fontsize=14, fontweight='bold')
    ax_main.legend(loc='best', fontsize=10)
    ax_main.grid(True, alpha=0.3)
    ax_main.set_xlim(-0.5, 10.5)
    ax_main.set_ylim(0, max(task_completions) + 5)
    ax_main.set_xticks(range(11))
    
    # ========== Plot 1: Task Completion with Confidence Intervals ==========
    ax1 = plt.subplot(4, 4, 3)
    
    # Main data points
    ax1.scatter(uncoop_counts, task_completions, s=150, c='darkred', alpha=0.8, zorder=5, label='Actual')
    
    # Add error bars (using standard error as proxy for confidence)
    if len(task_completions) > 1:
        se = np.std(task_completions) / np.sqrt(len(task_completions))
        ax1.errorbar(uncoop_counts, task_completions, yerr=se*1.96, fmt='none', 
                    color='red', alpha=0.3, capsize=5)
    
    # Fit best model (based on R²)
    if 'cubic' in stats_results and stats_results['cubic']['r2'] > 0.8:
        x_smooth = np.linspace(0, 10, 200)
        y_smooth = np.polyval(stats_results['cubic']['coefficients'], x_smooth)
        ax1.plot(x_smooth, y_smooth, 'b-', alpha=0.6, linewidth=2,
                label=f"Cubic fit (R²={stats_results['cubic']['r2']:.3f})")
    
    # Add value labels
    for x, y in zip(uncoop_counts, task_completions):
        ax1.annotate(str(y), (x, y), textcoords="offset points", xytext=(0,10), 
                    ha='center', fontweight='bold', fontsize=9)
    
    ax1.set_xlabel('Number of Uncooperative Agents')
    ax1.set_ylabel('Total Tasks Completed')
    ax1.set_title('Task Completion with 95% CI', fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-0.5, 10.5)
    
    # ========== Plot 2: Performance Drop ==========
    ax2 = plt.subplot(4, 4, 4)
    colors = ['green' if p <= 30 else 'orange' if p <= 60 else 'red' for p in performance_drops]
    bars = ax2.bar(uncoop_counts, performance_drops, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for bar, val in zip(bars, performance_drops):
        height = bar.get_height()
        label_y = height + 2 if height >= 0 else height - 5
        ax2.text(bar.get_x() + bar.get_width()/2., label_y,
                f'{int(val)}%', ha='center', fontweight='bold', fontsize=9)
    
    # Add threshold lines
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.axhline(y=30, color='orange', linestyle='--', alpha=0.5, label='30% threshold')
    ax2.axhline(y=60, color='red', linestyle='--', alpha=0.5, label='60% threshold')
    
    ax2.set_xlabel('Number of Uncooperative Agents')
    ax2.set_ylabel('Performance Drop (%)')
    ax2.set_title('Performance Degradation', fontweight='bold')
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xlim(-0.5, 10.5)
    ax2.set_ylim(min(performance_drops)-10, max(performance_drops)+10)
    
    # ========== Plot 3: Communication & Deception ==========
    ax3 = plt.subplot(4, 4, 5)
    
    # Messages
    line1 = ax3.plot(uncoop_counts, messages, 'o-', color='#1976D2', linewidth=2.5, 
                    markersize=8, label='Messages')
    ax3.set_xlabel('Number of Uncooperative Agents')
    ax3.set_ylabel('Total Messages', color='#1976D2')
    ax3.tick_params(axis='y', labelcolor='#1976D2')
    ax3.grid(True, alpha=0.3)
    
    # Deception on secondary axis
    ax3_twin = ax3.twinx()
    line2 = ax3_twin.plot(uncoop_counts, deceptions, 's-', color='#D32F2F', linewidth=2.5, 
                         markersize=8, label='Deceptions')
    ax3_twin.set_ylabel('Deception Attempts', color='#D32F2F')
    ax3_twin.tick_params(axis='y', labelcolor='#D32F2F')
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, loc='upper left')
    
    ax3.set_title('Communication Patterns', fontweight='bold')
    ax3.set_xlim(-0.5, 10.5)
    
    # ========== Plot 4: System Efficiency ==========
    ax4 = plt.subplot(4, 4, 6)
    ax4.plot(uncoop_counts, efficiency, 'o-', color='purple', linewidth=2.5, markersize=8)
    
    # Add value labels
    for x, y in zip(uncoop_counts, efficiency):
        ax4.annotate(f'{y:.1f}', (x, y), textcoords="offset points", xytext=(0,5), 
                    ha='center', fontsize=8)
    
    # Add trend line
    if len(uncoop_counts) > 2:
        z = np.polyfit(uncoop_counts, efficiency, 1)
        p = np.poly1d(z)
        ax4.plot(uncoop_counts, p(uncoop_counts), "m--", alpha=0.5, label='Trend')
    
    ax4.set_xlabel('Number of Uncooperative Agents')
    ax4.set_ylabel('Efficiency (Tasks per 100 Messages)')
    ax4.set_title('System Efficiency', fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(-0.5, 10.5)
    
    # ========== Plot 5: Deception Rate ==========
    ax5 = plt.subplot(4, 4, 7)
    bars = ax5.bar(uncoop_counts, deception_rate, color='darkred', alpha=0.7, edgecolor='black')
    
    # Add value labels for non-zero values
    for bar, val in zip(bars, deception_rate):
        if val > 0:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{val:.1f}%', ha='center', fontsize=8)
    
    ax5.set_xlabel('Number of Uncooperative Agents')
    ax5.set_ylabel('Deception Rate (% of Messages)')
    ax5.set_title('Trust Degradation', fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    ax5.set_xlim(-0.5, 10.5)
    
    # ========== Plot 6: Marginal Impact ==========
    ax6 = plt.subplot(4, 4, 8)
    
    if len(uncoop_counts) > 1:
        marginal_changes = []
        x_points = []
        
        for i in range(1, len(task_completions)):
            change = task_completions[i] - task_completions[i-1]
            marginal_changes.append(change)
            x_points.append((uncoop_counts[i] + uncoop_counts[i-1]) / 2)
        
        colors = ['green' if c > 0 else 'red' for c in marginal_changes]
        bars = ax6.bar(x_points, marginal_changes, width=0.8, color=colors, alpha=0.7, edgecolor='black')
        
        # Add value labels
        for bar, val in zip(bars, marginal_changes):
            height = bar.get_height()
            label_y = height + 0.5 if height >= 0 else height - 1
            ax6.text(bar.get_x() + bar.get_width()/2., label_y,
                    f'{int(val)}', ha='center', fontweight='bold', fontsize=8)
        
        ax6.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
        ax6.set_xlabel('Agent Count (between points)')
        ax6.set_ylabel('Marginal Task Change')
        ax6.set_title('Marginal Impact Analysis', fontweight='bold')
        ax6.grid(True, alpha=0.3)
    
    # ========== Plot 7: Task Completion Timeline ==========
    ax7 = plt.subplot(4, 4, 9)
    
    # Create timeline for each simulation
    for u in uncoop_counts:
        timeline = analysis_data[u]['completions_timeline']
        if timeline:
            rounds = [t[0] for t in timeline]
            cumulative = [t[1] for t in timeline]
            ax7.plot(rounds, cumulative, marker='o', label=f'{u} uncoop', alpha=0.7)
    
    ax7.set_xlabel('Round')
    ax7.set_ylabel('Cumulative Tasks Completed')
    ax7.set_title('Task Completion Over Time', fontweight='bold')
    ax7.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7, ncol=2)
    ax7.grid(True, alpha=0.3)
    
    # ========== Plot 8: Active Agents ==========
    ax8 = plt.subplot(4, 4, 10)
    ax8.plot(uncoop_counts, unique_agents, 'o-', color='green', linewidth=2.5, markersize=8)
    
    for x, y in zip(uncoop_counts, unique_agents):
        ax8.annotate(str(y), (x, y), textcoords="offset points", xytext=(0,5), 
                    ha='center', fontsize=8)
    
    ax8.set_xlabel('Number of Uncooperative Agents')
    ax8.set_ylabel('Unique Agents Completing Tasks')
    ax8.set_title('Agent Participation', fontweight='bold')
    ax8.grid(True, alpha=0.3)
    ax8.set_xlim(-0.5, 10.5)
    ax8.set_ylim(0, 11)
    
    # ========== Plot 9: Heatmap of Completions by Round ==========
    ax9 = plt.subplot(4, 4, 11)
    
    # Create matrix for heatmap
    rounds_data = np.zeros((len(uncoop_counts), 10))
    for i, u in enumerate(uncoop_counts):
        for r in range(1, 11):
            rounds_data[i, r-1] = analysis_data[u]['completions_by_round'].get(r, 0)
    
    im = ax9.imshow(rounds_data, cmap='YlOrRd', aspect='auto')
    ax9.set_xticks(range(10))
    ax9.set_xticklabels(range(1, 11))
    ax9.set_yticks(range(len(uncoop_counts)))
    ax9.set_yticklabels(uncoop_counts)
    ax9.set_xlabel('Round')
    ax9.set_ylabel('Uncooperative Agents')
    ax9.set_title('Task Completions Heatmap', fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax9)
    cbar.set_label('Tasks', rotation=270, labelpad=15)
    
    # ========== Plot 10: Statistical Summary Box ==========
    ax10 = plt.subplot(4, 4, 12)
    ax10.axis('off')
    
    # Create text summary
    summary_text = "Statistical Summary\n" + "="*25 + "\n\n"
    
    if 'pearson' in stats_results:
        summary_text += f"Correlation (Pearson):\n  r = {stats_results['pearson']['r']:.3f}, p = {stats_results['pearson']['p']:.3f}\n\n"
    
    if 'cubic' in stats_results:
        summary_text += "Model Comparison (R²):\n"
        summary_text += f"  Linear: {stats_results['linear']['r2']:.3f}\n"
        summary_text += f"  Quadratic: {stats_results['quadratic']['r2']:.3f}\n"
        summary_text += f"  Cubic: {stats_results['cubic']['r2']:.3f}\n\n"
    
    summary_text += f"Key Metrics:\n"
    summary_text += f"  Baseline: {baseline} tasks\n"
    summary_text += f"  Best: {max(task_completions)} tasks\n"
    summary_text += f"  Worst: {min(task_completions)} tasks\n"
    summary_text += f"  Range: {max(task_completions) - min(task_completions)} tasks\n"
    summary_text += f"  Std Dev: {np.std(task_completions):.1f} tasks\n"
    
    ax10.text(0.1, 0.9, summary_text, transform=ax10.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # ========== Plot 11: Scatter Matrix ==========
    ax11 = plt.subplot(4, 4, 13)
    
    # Scatter plot of efficiency vs deception rate
    scatter = ax11.scatter(deception_rate, efficiency, c=uncoop_counts, 
                          cmap='viridis', s=100, alpha=0.7, edgecolor='black')
    
    # Add labels for each point
    for i, u in enumerate(uncoop_counts):
        ax11.annotate(str(u), (deception_rate[i], efficiency[i]), 
                     textcoords="offset points", xytext=(5,5), fontsize=7)
    
    ax11.set_xlabel('Deception Rate (%)')
    ax11.set_ylabel('Efficiency (Tasks/100 Msgs)')
    ax11.set_title('Efficiency vs Deception Trade-off', fontweight='bold')
    ax11.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax11)
    cbar.set_label('Uncooperative Agents', rotation=270, labelpad=15)
    
    # ========== Plot 12: Box Plot Summary ==========
    ax12 = plt.subplot(4, 4, 14)
    
    # Group data by ranges of uncooperative agents
    groups = {
        'Low (0-3)': [task_completions[i] for i in range(len(uncoop_counts)) if uncoop_counts[i] <= 3],
        'Med (4-7)': [task_completions[i] for i in range(len(uncoop_counts)) if 4 <= uncoop_counts[i] <= 7],
        'High (8-10)': [task_completions[i] for i in range(len(uncoop_counts)) if uncoop_counts[i] >= 8]
    }
    
    box_data = [groups[k] for k in groups.keys()]
    bp = ax12.boxplot(box_data, labels=list(groups.keys()), patch_artist=True)
    
    # Color the boxes
    colors = ['lightgreen', 'orange', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    ax12.set_ylabel('Tasks Completed')
    ax12.set_title('Performance by Disruption Level', fontweight='bold')
    ax12.grid(True, alpha=0.3, axis='y')
    
    # Overall title
    plt.suptitle('Comprehensive Analysis: Impact of Uncooperative Agents on System Performance (10 Rounds, 11 Simulations)', 
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    return fig, stats_results


def main():
    """Main analysis function."""
    print("="*80)
    print("FINAL COMPREHENSIVE ANALYSIS: UNCOOPERATIVE AGENTS IMPACT")
    print("="*80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Simulations: 11 (0-10 uncooperative agents)")
    print(f"Rounds per Simulation: 10")
    print("="*80)
    
    # Extract metrics for all simulations
    print("\nExtracting simulation data...")
    analysis_data = {}
    
    for uncoop_count, sim_path in COMPLETE_SIMULATIONS.items():
        print(f"  Processing {uncoop_count} uncooperative agents...")
        metrics = extract_simulation_metrics(sim_path)
        
        if metrics:
            analysis_data[uncoop_count] = metrics
            print(f"    ✓ Tasks: {metrics['task_completions']:3d}, "
                  f"Messages: {metrics['messages']:3d}, "
                  f"Deceptions: {metrics['deception_attempts']:3d}")
        else:
            print(f"    ✗ Failed to extract data")
    
    if len(analysis_data) != 11:
        print(f"\nWarning: Only {len(analysis_data)}/11 simulations processed successfully")
    
    # Create visualizations
    print("\nGenerating comprehensive visualizations...")
    fig, stats_results = create_comprehensive_visualizations(analysis_data)
    
    # Save figure
    output_file = 'final_comprehensive_analysis.png'
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved visualization to {output_file}")
    plt.close()
    
    # Prepare detailed results
    uncoop_counts = sorted(analysis_data.keys())
    task_completions = [analysis_data[u]['task_completions'] for u in uncoop_counts]
    
    # Print key findings
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    
    baseline = task_completions[0]
    print(f"\n1. Performance Overview:")
    print(f"   - Baseline (0 uncooperative): {baseline} tasks")
    print(f"   - Best performance: {max(task_completions)} tasks at {uncoop_counts[task_completions.index(max(task_completions))]} uncooperative")
    print(f"   - Worst performance: {min(task_completions)} tasks at {uncoop_counts[task_completions.index(min(task_completions))]} uncooperative")
    
    # Check for non-monotonic behavior
    improvements = []
    for i in range(1, len(task_completions)):
        if task_completions[i] > baseline:
            improvements.append((uncoop_counts[i], task_completions[i]))
    
    if improvements:
        print(f"\n2. ⚠️ Paradoxical Improvement Detected:")
        for uncoop, tasks in improvements:
            improvement = (tasks - baseline) / baseline * 100
            print(f"   - {uncoop} uncooperative: {tasks} tasks (+{improvement:.1f}% vs baseline)")
    
    print(f"\n3. Statistical Analysis:")
    if 'pearson' in stats_results:
        r = stats_results['pearson']['r']
        p = stats_results['pearson']['p']
        print(f"   - Correlation: r = {r:.3f} (p = {p:.3f})")
        print(f"   - Relationship: {'Significant' if p < 0.05 else 'Not significant'} at α = 0.05")
    
    if 'cubic' in stats_results:
        print(f"\n4. Model Fit Comparison:")
        print(f"   - Linear R²: {stats_results['linear']['r2']:.3f}")
        print(f"   - Quadratic R²: {stats_results['quadratic']['r2']:.3f}")
        print(f"   - Cubic R²: {stats_results['cubic']['r2']:.3f}")
        
        best_model = max(['linear', 'quadratic', 'cubic'], 
                        key=lambda x: stats_results[x]['r2'])
        print(f"   - Best fit: {best_model.capitalize()} model")
    
    # Save complete results
    final_results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_simulations': len(analysis_data),
            'rounds_per_simulation': 10,
            'agent_count': 10
        },
        'raw_data': {
            'uncooperative_counts': uncoop_counts,
            'task_completions': task_completions,
            'messages': [analysis_data[u]['messages'] for u in uncoop_counts],
            'deceptions': [analysis_data[u]['deception_attempts'] for u in uncoop_counts]
        },
        'statistical_analysis': stats_results,
        'detailed_metrics': {str(k): {
            'task_completions': v['task_completions'],
            'messages': v['messages'],
            'deception_attempts': v['deception_attempts'],
            'unique_agents_completing': v['unique_agents_count'],
            'first_completion_round': v['first_completion_round'],
            'last_completion_round': v['last_completion_round']
        } for k, v in analysis_data.items()},
        'key_findings': {
            'baseline_performance': baseline,
            'best_performance': {'count': uncoop_counts[task_completions.index(max(task_completions))],
                               'tasks': max(task_completions)},
            'worst_performance': {'count': uncoop_counts[task_completions.index(min(task_completions))],
                                'tasks': min(task_completions)},
            'paradoxical_improvements': improvements
        }
    }
    
    output_json = 'final_comprehensive_analysis_results.json'
    with open(output_json, 'w') as f:
        json.dump(final_results, f, indent=2)
    print(f"\n  ✓ Saved detailed results to {output_json}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nGenerated files:")
    print(f"  1. {output_file} - Comprehensive visualization (12 plots)")
    print(f"  2. {output_json} - Detailed statistical results")
    
    return final_results


if __name__ == "__main__":
    results = main()
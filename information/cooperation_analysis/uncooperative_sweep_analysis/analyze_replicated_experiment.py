#!/usr/bin/env python3
"""
Analyze replicated sweep experiment results with proper statistical analysis.
Produces publication-ready figures and statistical tests.
"""

import json
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from scipy import stats
from scipy.stats import f_oneway, tukey_hsd
import warnings
warnings.filterwarnings('ignore')

# Configuration
SWEEP_BASE_DIR = Path('/Users/Aadi/Desktop/playground/multiagent/information/uncooperative_sweep_analysis')
LOGS_DIR = SWEEP_BASE_DIR / 'logs'
RESULTS_DIR = SWEEP_BASE_DIR / 'results'

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


class ReplicatedExperimentAnalyzer:
    """Analyze replicated experiment data with statistical rigor."""
    
    def __init__(self, experiment_id=None):
        """Initialize analyzer with experiment ID."""
        if experiment_id:
            self.experiment_dir = LOGS_DIR / f'experiment_{experiment_id}*'
            matching_dirs = list(LOGS_DIR.glob(f'experiment_{experiment_id}*'))
            if not matching_dirs:
                raise ValueError(f"No experiment found with ID: {experiment_id}")
            self.experiment_dir = matching_dirs[0]
        else:
            # Find most recent experiment
            exp_dirs = list(LOGS_DIR.glob('experiment_*'))
            if not exp_dirs:
                raise ValueError("No experiments found")
            self.experiment_dir = max(exp_dirs, key=lambda p: p.stat().st_mtime)
        
        self.experiment_id = self.experiment_dir.name.split('_')[1]
        print(f"Analyzing experiment: {self.experiment_id}")
        print(f"Directory: {self.experiment_dir}")
    
    def load_data(self):
        """Load and organize experiment data."""
        # Load summary statistics if available
        summary_file = self.experiment_dir / 'summary_statistics.json'
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                return json.load(f)
        
        # Otherwise, process raw results
        print("Processing raw results...")
        all_results_file = self.experiment_dir / 'all_results.json'
        if not all_results_file.exists():
            raise ValueError("No results file found")
        
        with open(all_results_file, 'r') as f:
            all_results = json.load(f)
        
        # Process into summary format
        summary = self._process_raw_results(all_results)
        
        # Save for future use
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    def _process_raw_results(self, all_results):
        """Process raw results into summary statistics."""
        summary = {str(u): [] for u in range(11)}
        
        for rep, rep_data in all_results.items():
            for uncoop_str, data in rep_data.items():
                uncoop = str(int(uncoop_str))
                if data['success'] and data['path']:
                    # Extract metrics from simulation
                    sim_path = Path(data['path'])
                    log_file = sim_path / 'simulation_log.jsonl'
                    if log_file.exists():
                        metrics = self._extract_metrics(log_file)
                        metrics['replication'] = int(rep)
                        metrics['time'] = data['time']
                        summary[uncoop].append(metrics)
        
        # Convert to statistical summary
        final_summary = {}
        for uncoop_str, replications in summary.items():
            uncoop = int(uncoop_str)
            if replications:
                tasks = [r['tasks'] for r in replications]
                messages = [r['messages'] for r in replications]
                deceptions = [r['deceptions'] for r in replications]
                
                final_summary[uncoop] = {
                    'n_successful': len(replications),
                    'tasks': {
                        'mean': np.mean(tasks),
                        'std': np.std(tasks, ddof=1) if len(tasks) > 1 else 0,
                        'sem': stats.sem(tasks) if len(tasks) > 1 else 0,
                        'min': min(tasks),
                        'max': max(tasks),
                        'values': tasks
                    },
                    'messages': {
                        'mean': np.mean(messages),
                        'std': np.std(messages, ddof=1) if len(messages) > 1 else 0,
                        'values': messages
                    },
                    'deceptions': {
                        'mean': np.mean(deceptions),
                        'std': np.std(deceptions, ddof=1) if len(deceptions) > 1 else 0,
                        'values': deceptions
                    }
                }
            else:
                final_summary[uncoop] = {'n_successful': 0}
        
        return final_summary
    
    def _extract_metrics(self, log_file):
        """Extract metrics from a simulation log file."""
        task_count = 0
        message_count = 0
        deception_count = 0
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('event_type') == 'task_completion' and data.get('success'):
                        task_count += 1
                    if data.get('event_type') == 'message':
                        message_count += 1
                    if data.get('deceptive'):
                        deception_count += 1
                except:
                    continue
        
        return {
            'tasks': task_count,
            'messages': message_count,
            'deceptions': deception_count
        }
    
    def perform_statistical_tests(self, data):
        """Perform comprehensive statistical tests."""
        results = {}
        
        # Prepare data for tests
        conditions = sorted([k for k in data.keys() if data[k].get('n_successful', 0) > 0], key=int)
        task_data = [data[int(c)]['tasks']['values'] for c in conditions if data[int(c)].get('tasks')]
        
        if len(task_data) < 2:
            print("Insufficient data for statistical tests")
            return results
        
        # 1. One-way ANOVA
        f_stat, p_value = f_oneway(*task_data)
        results['anova'] = {
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
        
        print(f"\nOne-way ANOVA Results:")
        print(f"  F-statistic: {f_stat:.3f}")
        print(f"  p-value: {p_value:.4f}")
        print(f"  Result: {'Significant' if p_value < 0.05 else 'Not significant'} differences between conditions")
        
        # 2. Post-hoc tests (Tukey HSD) if ANOVA is significant
        if p_value < 0.05:
            # Prepare data for Tukey HSD
            all_values = []
            all_groups = []
            for c in conditions:
                values = data[int(c)]['tasks']['values']
                all_values.extend(values)
                all_groups.extend([int(c)] * len(values))
            
            tukey_result = tukey_hsd(*[data[int(c)]['tasks']['values'] for c in conditions])
            results['tukey_hsd'] = {
                'statistic': tukey_result.statistic.tolist(),
                'pvalue': tukey_result.pvalue.tolist()
            }
            
            print(f"\nTukey HSD Post-hoc Test:")
            print(f"  Significant pairwise differences found")
            
            # Find significant pairs
            sig_pairs = []
            for i, c1 in enumerate(conditions):
                for j, c2 in enumerate(conditions):
                    if i < j and tukey_result.pvalue[i, j] < 0.05:
                        sig_pairs.append((int(c1), int(c2), tukey_result.pvalue[i, j]))
            
            if sig_pairs:
                print(f"  Significant pairs (p < 0.05):")
                for c1, c2, p in sig_pairs[:5]:  # Show top 5
                    print(f"    {c1} vs {c2}: p = {p:.4f}")
        
        # 3. Effect sizes (Cohen's d) vs baseline
        if 0 in data and data[0].get('tasks'):
            baseline_values = data[0]['tasks']['values']
            baseline_mean = np.mean(baseline_values)
            baseline_std = np.std(baseline_values, ddof=1) if len(baseline_values) > 1 else 1
            
            results['effect_sizes'] = {}
            for c in conditions:
                if int(c) != 0:
                    comp_values = data[int(c)]['tasks']['values']
                    comp_mean = np.mean(comp_values)
                    
                    # Cohen's d
                    pooled_std = np.sqrt(((len(baseline_values)-1)*baseline_std**2 + 
                                         (len(comp_values)-1)*np.std(comp_values, ddof=1)**2) / 
                                        (len(baseline_values) + len(comp_values) - 2))
                    cohens_d = (baseline_mean - comp_mean) / pooled_std if pooled_std > 0 else 0
                    
                    results['effect_sizes'][int(c)] = cohens_d
            
            print(f"\nEffect Sizes (Cohen's d) vs Baseline:")
            for c, d in sorted(results['effect_sizes'].items())[:3]:
                magnitude = 'small' if abs(d) < 0.5 else 'medium' if abs(d) < 0.8 else 'large'
                print(f"  {c} uncooperative: d = {d:.2f} ({magnitude})")
        
        return results
    
    def create_visualizations(self, data, stats_results):
        """Create publication-quality visualizations."""
        # Prepare data
        conditions = sorted([int(k) for k in data.keys() if data[int(k)].get('n_successful', 0) > 0])
        
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 10))
        
        # 1. Main results: Box plot with individual points
        ax1 = plt.subplot(2, 3, 1)
        task_data = []
        labels = []
        for c in conditions:
            if data[c].get('tasks'):
                task_data.append(data[c]['tasks']['values'])
                labels.append(str(c))
        
        bp = ax1.boxplot(task_data, labels=labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
        
        # Overlay individual points
        for i, values in enumerate(task_data):
            x = np.random.normal(i+1, 0.04, size=len(values))
            ax1.scatter(x, values, alpha=0.5, s=30, color='red')
        
        ax1.set_xlabel('Number of Uncooperative Agents')
        ax1.set_ylabel('Tasks Completed')
        ax1.set_title('Task Completion by Uncooperative Count')
        ax1.grid(True, alpha=0.3)
        
        # 2. Mean with error bars (95% CI)
        ax2 = plt.subplot(2, 3, 2)
        means = []
        ci_lower = []
        ci_upper = []
        
        for c in conditions:
            if data[c].get('tasks'):
                values = data[c]['tasks']['values']
                mean = np.mean(values)
                means.append(mean)
                
                # 95% confidence interval
                if len(values) > 1:
                    ci = stats.t.interval(0.95, len(values)-1, 
                                         loc=mean, 
                                         scale=stats.sem(values))
                    ci_lower.append(mean - ci[0])
                    ci_upper.append(ci[1] - mean)
                else:
                    ci_lower.append(0)
                    ci_upper.append(0)
        
        ax2.errorbar(conditions, means, yerr=[ci_lower, ci_upper], 
                    marker='o', capsize=5, capthick=2, linewidth=2)
        ax2.set_xlabel('Number of Uncooperative Agents')
        ax2.set_ylabel('Mean Tasks Completed')
        ax2.set_title('Mean Performance with 95% CI')
        ax2.grid(True, alpha=0.3)
        
        # Add baseline reference line
        if 0 in data and data[0].get('tasks'):
            baseline = np.mean(data[0]['tasks']['values'])
            ax2.axhline(y=baseline, color='red', linestyle='--', alpha=0.5, label='Baseline')
            ax2.legend()
        
        # 3. Variance/Consistency analysis
        ax3 = plt.subplot(2, 3, 3)
        stds = []
        for c in conditions:
            if data[c].get('tasks') and len(data[c]['tasks']['values']) > 1:
                stds.append(np.std(data[c]['tasks']['values'], ddof=1))
            else:
                stds.append(0)
        
        ax3.bar(conditions, stds, color='coral', alpha=0.7)
        ax3.set_xlabel('Number of Uncooperative Agents')
        ax3.set_ylabel('Standard Deviation')
        ax3.set_title('Performance Variability')
        ax3.grid(True, alpha=0.3)
        
        # 4. Messages vs Deceptions scatter
        ax4 = plt.subplot(2, 3, 4)
        for c in conditions:
            if data[c].get('messages') and data[c].get('deceptions'):
                msg_mean = np.mean(data[c]['messages']['values'])
                dec_mean = np.mean(data[c]['deceptions']['values'])
                ax4.scatter(msg_mean, dec_mean, s=100, label=f'{c} uncoop')
        
        ax4.set_xlabel('Mean Messages')
        ax4.set_ylabel('Mean Deceptions')
        ax4.set_title('Communication vs Deception')
        ax4.grid(True, alpha=0.3)
        
        # 5. Effect sizes
        ax5 = plt.subplot(2, 3, 5)
        if stats_results and 'effect_sizes' in stats_results:
            effect_conditions = list(stats_results['effect_sizes'].keys())
            effect_values = list(stats_results['effect_sizes'].values())
            colors = ['green' if v < 0 else 'red' for v in effect_values]
            ax5.bar(effect_conditions, effect_values, color=colors, alpha=0.7)
            ax5.set_xlabel('Number of Uncooperative Agents')
            ax5.set_ylabel("Cohen's d (vs baseline)")
            ax5.set_title('Effect Sizes Relative to Baseline')
            ax5.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax5.grid(True, alpha=0.3)
        
        # 6. Sample sizes
        ax6 = plt.subplot(2, 3, 6)
        sample_sizes = [data[c]['n_successful'] for c in conditions]
        ax6.bar(conditions, sample_sizes, color='skyblue', alpha=0.7)
        ax6.set_xlabel('Number of Uncooperative Agents')
        ax6.set_ylabel('Successful Replications')
        ax6.set_title('Sample Sizes per Condition')
        ax6.grid(True, alpha=0.3)
        
        plt.suptitle(f'Replicated Experiment Analysis - {self.experiment_id}', fontsize=16)
        plt.tight_layout()
        
        return fig
    
    def generate_report(self, data, stats_results):
        """Generate comprehensive text report."""
        report = []
        report.append("="*80)
        report.append("REPLICATED EXPERIMENT ANALYSIS REPORT")
        report.append("="*80)
        report.append(f"Experiment ID: {self.experiment_id}")
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Data summary
        report.append("DATA SUMMARY")
        report.append("-"*40)
        total_sims = sum(data[c]['n_successful'] for c in data if data[c].get('n_successful'))
        report.append(f"Total successful simulations: {total_sims}")
        report.append(f"Conditions tested: {len([c for c in data if data[c].get('n_successful', 0) > 0])}")
        report.append("")
        
        # Performance summary
        report.append("PERFORMANCE SUMMARY")
        report.append("-"*40)
        
        conditions = sorted([int(k) for k in data.keys() if data[int(k)].get('n_successful', 0) > 0])
        
        for c in conditions:
            if data[c].get('tasks'):
                mean = data[c]['tasks']['mean']
                std = data[c]['tasks']['std']
                n = data[c]['n_successful']
                report.append(f"{c:2d} uncooperative: {mean:.1f} ± {std:.1f} tasks (n={n})")
        
        report.append("")
        
        # Key findings
        report.append("KEY FINDINGS")
        report.append("-"*40)
        
        if 0 in data and data[0].get('tasks'):
            baseline = data[0]['tasks']['mean']
            
            # Find best and worst
            all_means = [(c, data[c]['tasks']['mean']) for c in conditions if data[c].get('tasks')]
            best = max(all_means, key=lambda x: x[1])
            worst = min(all_means, key=lambda x: x[1])
            
            report.append(f"Baseline (0 uncooperative): {baseline:.1f} tasks")
            report.append(f"Best performance: {best[1]:.1f} tasks at {best[0]} uncooperative")
            report.append(f"Worst performance: {worst[1]:.1f} tasks at {worst[0]} uncooperative")
            
            # Paradoxical improvements
            improvements = [(c, data[c]['tasks']['mean']) for c in conditions 
                          if c != 0 and data[c].get('tasks') and data[c]['tasks']['mean'] > baseline]
            
            if improvements:
                report.append("")
                report.append("⚠️ PARADOXICAL IMPROVEMENTS:")
                for c, mean in improvements:
                    improvement = ((mean - baseline) / baseline) * 100
                    report.append(f"  {c} uncooperative: +{improvement:.1f}% vs baseline")
        
        report.append("")
        
        # Statistical test results
        if stats_results:
            report.append("STATISTICAL TESTS")
            report.append("-"*40)
            
            if 'anova' in stats_results:
                report.append(f"One-way ANOVA:")
                report.append(f"  F = {stats_results['anova']['f_statistic']:.3f}")
                report.append(f"  p = {stats_results['anova']['p_value']:.4f}")
                report.append(f"  Result: {'Significant' if stats_results['anova']['significant'] else 'Not significant'}")
            
            report.append("")
        
        report.append("="*80)
        
        return "\n".join(report)
    
    def run_analysis(self):
        """Run complete analysis pipeline."""
        print("\n" + "="*80)
        print("STARTING REPLICATED EXPERIMENT ANALYSIS")
        print("="*80)
        
        # Load data
        print("\nLoading experiment data...")
        data = self.load_data()
        
        # Perform statistical tests
        print("\nPerforming statistical tests...")
        stats_results = self.perform_statistical_tests(data)
        
        # Create visualizations
        print("\nCreating visualizations...")
        fig = self.create_visualizations(data, stats_results)
        
        # Save visualizations
        output_path = RESULTS_DIR / f'experiment_{self.experiment_id}_analysis.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved visualization to: {output_path}")
        
        # Generate report
        print("\nGenerating report...")
        report = self.generate_report(data, stats_results)
        
        # Save report
        report_path = RESULTS_DIR / f'experiment_{self.experiment_id}_report.txt'
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"Saved report to: {report_path}")
        
        # Save complete results
        results_path = RESULTS_DIR / f'experiment_{self.experiment_id}_results.json'
        with open(results_path, 'w') as f:
            json.dump({
                'experiment_id': self.experiment_id,
                'analysis_date': datetime.now().isoformat(),
                'data': data,
                'statistical_tests': stats_results
            }, f, indent=2)
        print(f"Saved results to: {results_path}")
        
        # Print report to console
        print("\n" + report)
        
        return data, stats_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Analyze replicated experiment results')
    parser.add_argument('--experiment', type=str, help='Experiment ID to analyze')
    parser.add_argument('--list', action='store_true', help='List available experiments')
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable experiments:")
        exp_dirs = sorted(LOGS_DIR.glob('experiment_*'))
        for exp_dir in exp_dirs:
            exp_id = exp_dir.name.split('_')[1]
            
            # Check if it has results
            results_file = exp_dir / 'all_results.json'
            summary_file = exp_dir / 'summary_statistics.json'
            
            if results_file.exists():
                status = "✓ Complete" if summary_file.exists() else "○ Ready to analyze"
                print(f"  {exp_id}: {exp_dir.name} {status}")
            else:
                print(f"  {exp_id}: {exp_dir.name} ✗ In progress")
        return
    
    # Run analysis
    try:
        analyzer = ReplicatedExperimentAnalyzer(args.experiment)
        analyzer.run_analysis()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
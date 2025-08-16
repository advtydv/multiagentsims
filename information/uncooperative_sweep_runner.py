#!/usr/bin/env python3
"""
Parallel runner for simulations with varying numbers of uncooperative agents.
Runs 11 simulations (0-10 uncooperative agents) in parallel and performs comprehensive analysis.
"""

import os
import json
import yaml
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool, cpu_count
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import tempfile

# Configuration
BASE_DIR = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation')
CONFIG_FILE = BASE_DIR / 'config.yaml'
MAIN_SCRIPT = BASE_DIR / 'main.py'
LOGS_DIR = BASE_DIR / 'logs'

# Analysis parameters
ROUNDS = 10  # We're focusing on 10-round simulations
AGENTS = 10
MAX_WORKERS = 6  # Run 6 simulations in parallel
SIMULATION_TIMEOUT = None  # Timeout in seconds (e.g., 3600 for 60 min) - Set to None to disable timeout

class UncooperativeSweepRunner:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.sweep_dir = LOGS_DIR / f'sweep_{self.timestamp}'
        self.sweep_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        
    def load_base_config(self):
        """Load the base configuration file."""
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    
    def create_config_variation(self, uncooperative_count):
        """Create a config variation with specified number of uncooperative agents."""
        config = self.load_base_config()
        
        # Modify for our sweep
        config['simulation']['rounds'] = ROUNDS
        config['simulation']['agents'] = AGENTS
        config['agents']['uncooperative_count'] = uncooperative_count
        
        # Save to temporary file
        config_path = self.sweep_dir / f'config_uncoop_{uncooperative_count}.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        return config_path
    
    def run_single_simulation(self, args):
        """Run a single simulation with given uncooperative count."""
        uncooperative_count, run_number = args
        
        print(f"[Run {run_number+1}/11] Starting simulation with {uncooperative_count} uncooperative agents...")
        
        # Create config
        config_path = self.create_config_variation(uncooperative_count)
        
        # Run simulation
        env = os.environ.copy()
        if 'OPENAI_API_KEY' not in env:
            print("Warning: OPENAI_API_KEY not found in environment")
        
        try:
            result = subprocess.run(
                ['python', str(MAIN_SCRIPT), '--config', str(config_path)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                env=env,
                timeout=SIMULATION_TIMEOUT
            )
            
            if result.returncode != 0:
                print(f"  ⚠️ Simulation failed with {uncooperative_count} uncooperative agents")
                print(f"  Error: {result.stderr[:500]}")
                return uncooperative_count, None
            
            # Parse output to find simulation directory
            output_lines = result.stdout.split('\n')
            sim_dir = None
            for line in output_lines:
                if 'logs/simulation_' in line:
                    # Extract simulation directory from output
                    parts = line.split('logs/simulation_')
                    if len(parts) > 1:
                        sim_name = 'simulation_' + parts[1].split()[0].strip('/')
                        sim_dir = LOGS_DIR / sim_name
                        break
            
            if not sim_dir or not sim_dir.exists():
                # Try to find the most recent simulation
                import glob
                sims = sorted(glob.glob(str(LOGS_DIR / 'simulation_*')))
                if sims:
                    sim_dir = Path(sims[-1])
            
            if sim_dir and sim_dir.exists():
                print(f"  ✓ Completed: {sim_dir.name}")
                return uncooperative_count, str(sim_dir)
            else:
                print(f"  ⚠️ Could not find simulation output directory")
                return uncooperative_count, None
                
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ Simulation timed out with {uncooperative_count} uncooperative agents")
            return uncooperative_count, None
        except Exception as e:
            print(f"  ⚠️ Error running simulation: {e}")
            return uncooperative_count, None
    
    def run_parallel_simulations(self, sequential=True):
        """Run all simulations either sequentially or in parallel."""
        mode = "SEQUENTIAL" if sequential else "PARALLEL"
        print(f"\n{'='*70}")
        print(f"STARTING {mode} SIMULATION SWEEP")
        print(f"{'='*70}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Simulations: 11 (0-10 uncooperative agents)")
        print(f"Rounds per simulation: {ROUNDS}")
        if not sequential:
            print(f"Parallel workers: {MAX_WORKERS}")
        print(f"Sweep directory: {self.sweep_dir}")
        print(f"{'='*70}\n")
        
        # Prepare arguments
        sim_args = [(i, i) for i in range(11)]
        
        # Run simulations
        start_time = time.time()
        
        if sequential:
            # Run sequentially to avoid rate limits
            results = []
            for i, args in enumerate(sim_args):
                print(f"\n[{i+1}/11] Progress: {'█' * (i+1)}{'░' * (10-i)} {(i+1)/11*100:.0f}%")
                result = self.run_single_simulation(args)
                results.append(result)
                # Small delay between simulations to be nice to the API
                if result[1] is not None:  # If successful
                    time.sleep(2)
        else:
            # Run in parallel (original behavior)
            with Pool(MAX_WORKERS) as pool:
                results = pool.map(self.run_single_simulation, sim_args)
        
        elapsed = time.time() - start_time
        
        # Store results
        for uncoop_count, sim_dir in results:
            self.results[uncoop_count] = sim_dir
        
        # Summary
        successful = sum(1 for _, sim_dir in results if sim_dir is not None)
        print(f"\n{'='*70}")
        print(f"SIMULATION SWEEP COMPLETE")
        print(f"{'='*70}")
        print(f"Successful simulations: {successful}/11")
        print(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"Average time per simulation: {elapsed/11:.1f} seconds")
        
        # Save sweep metadata
        metadata = {
            'timestamp': self.timestamp,
            'sweep_dir': str(self.sweep_dir),
            'rounds': ROUNDS,
            'agents': AGENTS,
            'simulations': self.results,
            'elapsed_time': elapsed,
            'successful_count': successful
        }
        
        with open(self.sweep_dir / 'sweep_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return self.results
    
    def extract_simulation_metrics(self, sim_path):
        """Extract key metrics from a simulation."""
        if not sim_path:
            return None
            
        log_file = Path(sim_path) / 'simulation_log.jsonl'
        if not log_file.exists():
            return None
        
        metrics = {
            'task_completions': 0,
            'messages': 0,
            'deception_attempts': 0,
            'completions_by_round': {},
            'first_completion_round': None,
            'last_completion_round': None
        }
        
        current_round = 1
        
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON line: {e}")
                    continue
                
                if event['event_type'] == 'agent_action' and 'round' in event['data']:
                    current_round = event['data']['round']
                
                elif event['event_type'] == 'task_completion' and event['data']['success']:
                    metrics['task_completions'] += 1
                    
                    if current_round not in metrics['completions_by_round']:
                        metrics['completions_by_round'][current_round] = 0
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
    
    def analyze_results(self):
        """Perform comprehensive analysis of sweep results."""
        print(f"\n{'='*70}")
        print(f"COMPREHENSIVE ANALYSIS OF UNCOOPERATIVE AGENT IMPACT")
        print(f"{'='*70}\n")
        
        # Extract metrics for all simulations
        analysis_data = {}
        for uncoop_count in sorted(self.results.keys()):
            sim_path = self.results[uncoop_count]
            if sim_path:
                metrics = self.extract_simulation_metrics(sim_path)
                if metrics:
                    analysis_data[uncoop_count] = metrics
        
        if not analysis_data:
            print("No valid simulation data to analyze!")
            return
        
        # Prepare data for plotting
        uncoop_counts = sorted(analysis_data.keys())
        task_completions = [analysis_data[u]['task_completions'] for u in uncoop_counts]
        messages = [analysis_data[u]['messages'] for u in uncoop_counts]
        deceptions = [analysis_data[u]['deception_attempts'] for u in uncoop_counts]
        
        # Calculate derived metrics
        baseline_tasks = task_completions[0] if 0 in uncoop_counts else max(task_completions)
        performance_drops = [(baseline_tasks - t) / baseline_tasks * 100 if baseline_tasks > 0 else 0 
                            for t in task_completions]
        
        # Statistical analysis
        if len(uncoop_counts) > 2:
            # Fit regression models
            poly_fit = np.polyfit(uncoop_counts, task_completions, 2)  # Quadratic fit
            linear_fit = np.polyfit(uncoop_counts, task_completions, 1)  # Linear fit
            
            # Calculate R-squared
            poly_pred = np.polyval(poly_fit, uncoop_counts)
            linear_pred = np.polyval(linear_fit, uncoop_counts)
            
            ss_res_poly = np.sum((task_completions - poly_pred) ** 2)
            ss_res_linear = np.sum((task_completions - linear_pred) ** 2)
            ss_tot = np.sum((task_completions - np.mean(task_completions)) ** 2)
            
            r2_poly = 1 - (ss_res_poly / ss_tot) if ss_tot > 0 else 0
            r2_linear = 1 - (ss_res_linear / ss_tot) if ss_tot > 0 else 0
        
        # Create comprehensive visualization
        fig = plt.figure(figsize=(16, 10))
        
        # Plot 1: Task completion with fitted curves
        ax1 = plt.subplot(2, 3, 1)
        ax1.scatter(uncoop_counts, task_completions, s=100, c='red', alpha=0.7, label='Actual')
        
        if len(uncoop_counts) > 2:
            x_smooth = np.linspace(0, 10, 100)
            poly_smooth = np.polyval(poly_fit, x_smooth)
            linear_smooth = np.polyval(linear_fit, x_smooth)
            
            ax1.plot(x_smooth, poly_smooth, 'b--', alpha=0.5, 
                    label=f'Quadratic (R²={r2_poly:.3f})')
            ax1.plot(x_smooth, linear_smooth, 'g--', alpha=0.5,
                    label=f'Linear (R²={r2_linear:.3f})')
        
        ax1.set_xlabel('Number of Uncooperative Agents')
        ax1.set_ylabel('Total Tasks Completed')
        ax1.set_title('Task Completion vs Disruption')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Performance degradation
        ax2 = plt.subplot(2, 3, 2)
        colors = ['green' if p <= 20 else 'orange' if p <= 50 else 'red' for p in performance_drops]
        bars = ax2.bar(uncoop_counts, performance_drops, color=colors, alpha=0.7)
        ax2.set_xlabel('Number of Uncooperative Agents')
        ax2.set_ylabel('Performance Drop (%)')
        ax2.set_title('Performance Degradation from Baseline')
        ax2.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='50% threshold')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Plot 3: Communication patterns
        ax3 = plt.subplot(2, 3, 3)
        ax3.plot(uncoop_counts, messages, 'o-', color='blue', label='Total Messages')
        ax3.set_xlabel('Number of Uncooperative Agents')
        ax3.set_ylabel('Message Count')
        ax3.set_title('Communication Volume')
        ax3.grid(True, alpha=0.3)
        
        ax3_twin = ax3.twinx()
        ax3_twin.plot(uncoop_counts, deceptions, 's-', color='red', label='Deception Attempts')
        ax3_twin.set_ylabel('Deception Attempts', color='red')
        ax3_twin.tick_params(axis='y', labelcolor='red')
        
        # Plot 4: Efficiency metrics
        ax4 = plt.subplot(2, 3, 4)
        efficiency = [t/m * 100 if m > 0 else 0 for t, m in zip(task_completions, messages)]
        ax4.plot(uncoop_counts, efficiency, 'o-', color='purple')
        ax4.set_xlabel('Number of Uncooperative Agents')
        ax4.set_ylabel('Efficiency (Tasks per 100 Messages)')
        ax4.set_title('System Efficiency')
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Deception rate
        ax5 = plt.subplot(2, 3, 5)
        deception_rate = [d/m * 100 if m > 0 else 0 for d, m in zip(deceptions, messages)]
        ax5.bar(uncoop_counts, deception_rate, color='darkred', alpha=0.7)
        ax5.set_xlabel('Number of Uncooperative Agents')
        ax5.set_ylabel('Deception Rate (% of Messages)')
        ax5.set_title('Trust Degradation')
        ax5.grid(True, alpha=0.3, axis='y')
        
        # Plot 6: Tipping point analysis
        ax6 = plt.subplot(2, 3, 6)
        if len(uncoop_counts) > 3:
            # Calculate rate of change
            task_diff = np.diff(task_completions)
            uncoop_diff = uncoop_counts[1:]
            
            ax6.plot(uncoop_diff, task_diff, 'o-', color='navy')
            ax6.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
            ax6.set_xlabel('Number of Uncooperative Agents')
            ax6.set_ylabel('Change in Task Completions')
            ax6.set_title('Marginal Impact Analysis')
            ax6.grid(True, alpha=0.3)
            
            # Mark critical points
            if len(task_diff) > 0:
                min_impact = uncoop_diff[np.argmin(task_diff)]
                ax6.axvline(x=min_impact, color='red', linestyle='--', alpha=0.5,
                           label=f'Max impact at {min_impact} agents')
                ax6.legend()
        
        plt.suptitle(f'Comprehensive Analysis: Impact of Uncooperative Agents ({ROUNDS} Rounds)', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save plot
        output_file = self.sweep_dir / 'comprehensive_analysis.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved comprehensive analysis plot to {output_file}")
        plt.close()
        
        # Print statistical summary
        print("\n" + "="*60)
        print("STATISTICAL SUMMARY")
        print("="*60)
        
        print(f"\nTask Completion Statistics:")
        print(f"  Baseline (0 uncooperative): {task_completions[0] if 0 in uncoop_counts else 'N/A'}")
        print(f"  Mean: {np.mean(task_completions):.1f}")
        print(f"  Median: {np.median(task_completions):.1f}")
        print(f"  Std Dev: {np.std(task_completions):.1f}")
        print(f"  Range: {min(task_completions)} - {max(task_completions)}")
        
        if len(uncoop_counts) > 2:
            print(f"\nRegression Analysis:")
            print(f"  Linear fit: y = {linear_fit[0]:.2f}x + {linear_fit[1]:.2f} (R²={r2_linear:.3f})")
            print(f"  Quadratic fit: y = {poly_fit[0]:.3f}x² + {poly_fit[1]:.2f}x + {poly_fit[2]:.2f} (R²={r2_poly:.3f})")
        
        # Identify critical thresholds
        print(f"\nCritical Thresholds:")
        for i, (u, p) in enumerate(zip(uncoop_counts, performance_drops)):
            if p > 25 and (i == 0 or performance_drops[i-1] <= 25):
                print(f"  25% degradation threshold: {u} uncooperative agents")
            if p > 50 and (i == 0 or performance_drops[i-1] <= 50):
                print(f"  50% degradation threshold: {u} uncooperative agents")
            if p > 75 and (i == 0 or performance_drops[i-1] <= 75):
                print(f"  75% degradation threshold: {u} uncooperative agents")
        
        # Save detailed results
        detailed_results = {
            'timestamp': self.timestamp,
            'sweep_dir': str(self.sweep_dir),
            'uncoop_counts': uncoop_counts,
            'task_completions': task_completions,
            'messages': messages,
            'deceptions': deceptions,
            'performance_drops': performance_drops,
            'efficiency': efficiency,
            'deception_rate': deception_rate,
            'analysis_metrics': analysis_data,
            'regression': {
                'linear_coefficients': linear_fit.tolist() if len(uncoop_counts) > 2 else None,
                'linear_r2': r2_linear if len(uncoop_counts) > 2 else None,
                'quadratic_coefficients': poly_fit.tolist() if len(uncoop_counts) > 2 else None,
                'quadratic_r2': r2_poly if len(uncoop_counts) > 2 else None
            }
        }
        
        with open(self.sweep_dir / 'analysis_results.json', 'w') as f:
            json.dump(detailed_results, f, indent=2)
        
        print(f"\nDetailed results saved to {self.sweep_dir / 'analysis_results.json'}")
        
        return detailed_results


def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("UNCOOPERATIVE AGENTS PARAMETER SWEEP")
    print("="*70)
    print(f"Configuration:")
    print(f"  Agents: {AGENTS}")
    print(f"  Rounds: {ROUNDS}")
    print(f"  Uncooperative range: 0-10")
    print(f"  Total simulations: 11")
    print(f"  Execution mode: Parallel ({MAX_WORKERS} workers)")
    print("="*70)
    
    # Check for API key
    if 'OPENAI_API_KEY' not in os.environ:
        print("\n⚠️  WARNING: OPENAI_API_KEY not found in environment!")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Create and run sweep
    runner = UncooperativeSweepRunner()
    
    # Run simulations in parallel
    results = runner.run_parallel_simulations(sequential=False)
    
    if not results or all(v is None for v in results.values()):
        print("\n❌ No successful simulations to analyze!")
        return
    
    # Analyze results
    print("\nStarting comprehensive analysis...")
    analysis = runner.analyze_results()
    
    print("\n" + "="*70)
    print("SWEEP COMPLETE")
    print("="*70)
    print(f"Results directory: {runner.sweep_dir}")
    print("Generated files:")
    print(f"  - sweep_metadata.json")
    print(f"  - comprehensive_analysis.png")
    print(f"  - analysis_results.json")
    print(f"  - config_uncoop_*.yaml (11 config files)")
    

if __name__ == "__main__":
    main()
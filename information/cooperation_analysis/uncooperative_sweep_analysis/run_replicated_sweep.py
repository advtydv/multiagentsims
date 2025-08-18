#!/usr/bin/env python3
"""
Run replicated sweep experiment: 10 replications × 11 conditions (0-10 uncooperative agents).
Uses 11 parallel workers to run one complete replication at a time.
Provides detailed progress tracking and clean data organization.
"""

import os
import sys
import json
import yaml
import subprocess
import time
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool
import random
import string

# Configuration
PROJECT_ROOT = Path('/Users/Aadi/Desktop/playground/multiagent/information')
SIM_BASE_DIR = PROJECT_ROOT / 'information_asymmetry_simulation'
SWEEP_BASE_DIR = PROJECT_ROOT / 'uncooperative_sweep_analysis'
LOGS_DIR = SWEEP_BASE_DIR / 'logs'
CONFIG_FILE = SIM_BASE_DIR / 'config.yaml'
MAIN_SCRIPT = SIM_BASE_DIR / 'main.py'

# Experiment parameters
REPLICATIONS = 10  # Number of replications
ROUNDS = 10  # Rounds per simulation
AGENTS = 10  # Agents per simulation
UNCOOP_RANGE = range(11)  # 0-10 uncooperative agents
MAX_WORKERS = 11  # Run all 11 conditions in parallel

# Create necessary directories
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def run_single_simulation_worker(args):
    """Standalone worker function for running single simulation (picklable)."""
    uncooperative_count, replication, sim_number, experiment_id, experiment_dir = args
    
    experiment_dir = Path(experiment_dir)
    
    # Create unique simulation ID
    sim_id = f"r{replication:02d}_u{uncooperative_count:02d}"
    
    # Create output directory
    output_dir = experiment_dir / f'rep_{replication:02d}' / 'simulations' / f'uncoop_{uncooperative_count:02d}'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create config
    config = load_base_config()
    config['simulation']['rounds'] = ROUNDS
    config['simulation']['agents'] = AGENTS
    config['agents']['uncooperative_count'] = uncooperative_count
    
    # Save config for this run
    config_dir = experiment_dir / f'rep_{replication:02d}' / 'configs'
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / f'config_u{uncooperative_count:02d}.yaml'
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Prepare environment
    env = os.environ.copy()
    if 'OPENAI_API_KEY' not in env:
        print(f"  ⚠️ [{sim_id}] Warning: OPENAI_API_KEY not found")
        return sim_id, None, 0
    
    try:
        cmd = [
            'python', str(MAIN_SCRIPT),
            '--config', str(config_path),
            '--output-dir', str(output_dir),
            '--sim-id', f'sim_{experiment_id}_{sim_id}'
        ]
        
        # Run with real-time output capture
        start_time = time.time()
        process = subprocess.Popen(
            cmd,
            cwd=str(SIM_BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1
        )
        
        # Monitor output in real-time
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line)
                # Display important lines
                if any(keyword in line for keyword in ['Round', 'Task', 'Score', 'completed']):
                    print(f"  [{sim_id}] {line.strip()}")
        
        elapsed = time.time() - start_time
        
        # Check for errors
        if process.returncode != 0:
            stderr = process.stderr.read()
            print(f"  ✗ [{sim_id}] Failed: {stderr[:100]}")
            return sim_id, None, elapsed
        
        # Verify output exists
        # Find the actual simulation subdirectory
        subdirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith('sim_')]
        if subdirs:
            actual_sim_dir = subdirs[0]
            log_file = actual_sim_dir / 'simulation_log.jsonl'
            if log_file.exists():
                # Quick task count
                task_count = sum(1 for line in open(log_file) 
                               if '"event_type": "task_completion"' in line and '"success": true' in line)
                print(f"  ✓ [{sim_id}] Completed: {task_count} tasks in {elapsed:.1f}s")
                return sim_id, str(actual_sim_dir), elapsed
        
        print(f"  ✗ [{sim_id}] Output not found")
        return sim_id, None, elapsed
        
    except Exception as e:
        print(f"  ✗ [{sim_id}] Error: {str(e)}")
        return sim_id, None, 0


def load_base_config():
    """Load the base configuration file."""
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


class ReplicatedSweepRunner:
    """Run replicated sweep experiment with clean organization."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.experiment_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.experiment_dir = LOGS_DIR / f'experiment_{self.experiment_id}_{self.timestamp}'
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        
        # Create metadata file
        self.metadata = {
            'experiment_id': self.experiment_id,
            'timestamp': self.timestamp,
            'replications': REPLICATIONS,
            'conditions': list(UNCOOP_RANGE),
            'rounds_per_sim': ROUNDS,
            'agents_per_sim': AGENTS,
            'total_simulations': REPLICATIONS * len(UNCOOP_RANGE),
            'start_time': datetime.now().isoformat()
        }
        
        with open(self.experiment_dir / 'experiment_metadata.json', 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def load_base_config(self):
        """Load the base configuration file."""
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    
    def create_config_variation(self, uncooperative_count, replication):
        """Create config for specific condition and replication."""
        config = self.load_base_config()
        
        # Modify for our sweep
        config['simulation']['rounds'] = ROUNDS
        config['simulation']['agents'] = AGENTS
        config['agents']['uncooperative_count'] = uncooperative_count
        
        # Save config for this run
        config_dir = self.experiment_dir / f'rep_{replication:02d}' / 'configs'
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / f'config_u{uncooperative_count:02d}.yaml'
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        return config_path
    
    def run_single_simulation(self, args):
        """Wrapper method that calls the standalone function."""
        # Add experiment-specific data to args
        uncooperative_count, replication, sim_number = args
        extended_args = (
            uncooperative_count, 
            replication, 
            sim_number,
            self.experiment_id,
            str(self.experiment_dir)
        )
        return run_single_simulation_worker(extended_args)
    
    def run_replication(self, replication):
        """Run one complete replication (all 11 conditions in parallel)."""
        print(f"\n{'='*80}")
        print(f"REPLICATION {replication + 1}/{REPLICATIONS}")
        print(f"{'='*80}")
        print(f"Starting 11 parallel simulations (0-10 uncooperative agents)...")
        print(f"Output directory: {self.experiment_dir.name}/rep_{replication:02d}/")
        print(f"{'='*80}\n")
        
        # Prepare arguments for all conditions
        sim_args = [(u, replication, i) for i, u in enumerate(UNCOOP_RANGE)]
        
        # Run all conditions in parallel
        start_time = time.time()
        with Pool(MAX_WORKERS) as pool:
            results = pool.map(self.run_single_simulation, sim_args)
        
        elapsed = time.time() - start_time
        
        # Process results
        rep_results = {}
        successful = 0
        for sim_id, sim_dir, sim_time in results:
            uncoop = int(sim_id.split('_u')[1])
            if sim_dir:
                rep_results[uncoop] = {
                    'path': sim_dir,
                    'time': sim_time,
                    'success': True
                }
                successful += 1
            else:
                rep_results[uncoop] = {
                    'path': None,
                    'time': sim_time,
                    'success': False
                }
        
        # Save replication results
        rep_file = self.experiment_dir / f'rep_{replication:02d}' / 'replication_results.json'
        with open(rep_file, 'w') as f:
            json.dump(rep_results, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"REPLICATION {replication + 1} COMPLETE")
        print(f"Successful: {successful}/11 | Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"{'='*80}")
        
        return rep_results
    
    def run_experiment(self):
        """Run the complete experiment."""
        print(f"\n{'='*80}")
        print(f"REPLICATED SWEEP EXPERIMENT")
        print(f"{'='*80}")
        print(f"Experiment ID: {self.experiment_id}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Configuration:")
        print(f"  - Replications: {REPLICATIONS}")
        print(f"  - Conditions: 11 (0-10 uncooperative agents)")
        print(f"  - Total simulations: {REPLICATIONS * 11}")
        print(f"  - Parallel workers: {MAX_WORKERS}")
        print(f"  - Rounds per simulation: {ROUNDS}")
        print(f"  - Agents per simulation: {AGENTS}")
        print(f"Output directory: {self.experiment_dir}")
        print(f"{'='*80}")
        
        # Run all replications
        all_results = {}
        start_time = time.time()
        
        for rep in range(REPLICATIONS):
            rep_results = self.run_replication(rep)
            all_results[rep] = rep_results
            
            # Update progress
            completed = (rep + 1) * 11
            total = REPLICATIONS * 11
            percent = (completed / total) * 100
            print(f"\nOverall Progress: {completed}/{total} simulations ({percent:.1f}%)")
            
            # Estimate remaining time
            elapsed_so_far = time.time() - start_time
            if rep > 0:
                avg_per_rep = elapsed_so_far / (rep + 1)
                remaining_reps = REPLICATIONS - (rep + 1)
                est_remaining = avg_per_rep * remaining_reps
                print(f"Estimated time remaining: {est_remaining/60:.1f} minutes")
        
        total_elapsed = time.time() - start_time
        
        # Calculate success statistics
        total_successful = sum(
            1 for rep_data in all_results.values() 
            for cond_data in rep_data.values() 
            if cond_data['success']
        )
        
        # Save complete results
        self.metadata['end_time'] = datetime.now().isoformat()
        self.metadata['total_elapsed'] = total_elapsed
        self.metadata['successful_simulations'] = total_successful
        self.metadata['failed_simulations'] = (REPLICATIONS * 11) - total_successful
        
        with open(self.experiment_dir / 'experiment_metadata_final.json', 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        with open(self.experiment_dir / 'all_results.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Create summary
        print(f"\n{'='*80}")
        print(f"EXPERIMENT COMPLETE")
        print(f"{'='*80}")
        print(f"Total simulations: {REPLICATIONS * 11}")
        print(f"Successful: {total_successful}")
        print(f"Failed: {(REPLICATIONS * 11) - total_successful}")
        print(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
        print(f"Average time per simulation: {total_elapsed/(REPLICATIONS * 11):.1f}s")
        print(f"\nResults saved in: {self.experiment_dir}")
        print(f"Experiment ID: {self.experiment_id}")
        print(f"{'='*80}")
        
        return all_results
    
    def create_summary_statistics(self):
        """Create summary statistics file for easy analysis."""
        summary_file = self.experiment_dir / 'summary_statistics.json'
        
        # Load all results
        with open(self.experiment_dir / 'all_results.json', 'r') as f:
            all_results = json.load(f)
        
        # Organize by condition
        by_condition = {u: [] for u in range(11)}
        
        for rep, rep_data in all_results.items():
            for uncoop_str, data in rep_data.items():
                uncoop = int(uncoop_str)
                if data['success'] and data['path']:
                    # Extract metrics from simulation
                    sim_path = Path(data['path'])
                    log_file = sim_path / 'simulation_log.jsonl'
                    if log_file.exists():
                        # Count metrics
                        task_count = 0
                        message_count = 0
                        deception_count = 0
                        
                        with open(log_file, 'r') as f:
                            for line in f:
                                if '"event_type": "task_completion"' in line and '"success": true' in line:
                                    task_count += 1
                                if '"event_type": "message"' in line:
                                    message_count += 1
                                if '"deceptive": true' in line:
                                    deception_count += 1
                        
                        by_condition[uncoop].append({
                            'replication': int(rep),
                            'tasks': task_count,
                            'messages': message_count,
                            'deceptions': deception_count,
                            'time': data['time']
                        })
        
        # Calculate statistics
        summary = {}
        for uncoop in range(11):
            if by_condition[uncoop]:
                tasks = [d['tasks'] for d in by_condition[uncoop]]
                messages = [d['messages'] for d in by_condition[uncoop]]
                deceptions = [d['deceptions'] for d in by_condition[uncoop]]
                
                summary[uncoop] = {
                    'n_successful': len(by_condition[uncoop]),
                    'tasks': {
                        'mean': sum(tasks) / len(tasks),
                        'std': (sum((x - sum(tasks)/len(tasks))**2 for x in tasks) / len(tasks))**0.5 if len(tasks) > 1 else 0,
                        'min': min(tasks),
                        'max': max(tasks),
                        'values': tasks
                    },
                    'messages': {
                        'mean': sum(messages) / len(messages),
                        'values': messages
                    },
                    'deceptions': {
                        'mean': sum(deceptions) / len(deceptions),
                        'values': deceptions
                    }
                }
            else:
                summary[uncoop] = {'n_successful': 0}
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nSummary statistics saved to: {summary_file.name}")
        return summary


def main():
    """Main execution function."""
    print("\n" + "="*80)
    print("REPLICATED SWEEP EXPERIMENT RUNNER")
    print("="*80)
    
    # Check for API key
    if 'OPENAI_API_KEY' not in os.environ:
        print("\n⚠️  WARNING: OPENAI_API_KEY not found in environment!")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Confirm experiment parameters
    print(f"\nExperiment Configuration:")
    print(f"  - {REPLICATIONS} replications")
    print(f"  - 11 conditions (0-10 uncooperative agents)")
    print(f"  - {REPLICATIONS * 11} total simulations")
    print(f"  - {MAX_WORKERS} parallel workers")
    print(f"  - Estimated time: {(REPLICATIONS * 11 * 50) / 60:.1f} minutes")
    
    response = input("\nProceed with experiment? (y/n): ")
    if response.lower() != 'y':
        print("Experiment cancelled.")
        return
    
    # Run experiment
    runner = ReplicatedSweepRunner()
    results = runner.run_experiment()
    
    # Create summary statistics
    if results:
        runner.create_summary_statistics()
        
        print(f"\n{'='*80}")
        print("NEXT STEPS")
        print(f"{'='*80}")
        print(f"1. Experiment complete! Data saved in:")
        print(f"   {runner.experiment_dir}")
        print(f"\n2. To analyze results, use:")
        print(f"   python analyze_replicated_experiment.py --experiment {runner.experiment_id}")
        print(f"\n3. Key files:")
        print(f"   - all_results.json: Complete simulation results")
        print(f"   - summary_statistics.json: Aggregated statistics by condition")
        print(f"   - experiment_metadata_final.json: Experiment details")


if __name__ == "__main__":
    main()
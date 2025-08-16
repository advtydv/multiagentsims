#!/usr/bin/env python3
"""
Run complete sweep of all 11 simulations (0-10 uncooperative agents) in parallel.
Ensures unique naming and avoids conflicts.
"""

import os
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
BASE_DIR = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation')
CONFIG_FILE = BASE_DIR / 'config.yaml'
MAIN_SCRIPT = BASE_DIR / 'main.py'
LOGS_DIR = BASE_DIR / 'logs'

# Sweep parameters
ROUNDS = 10
AGENTS = 10
UNCOOP_RANGE = range(11)  # 0-10 uncooperative agents
MAX_WORKERS = 6  # Run 6 simulations in parallel
SIMULATION_TIMEOUT = None  # No timeout

class CompleteSweepRunner:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.sweep_dir = LOGS_DIR / f'complete_sweep_{self.timestamp}'
        self.sweep_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        # Unique identifier for this sweep run
        self.sweep_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
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
        
        # Save to sweep directory
        config_path = self.sweep_dir / f'config_u{uncooperative_count}.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        return config_path
    
    def run_single_simulation(self, args):
        """Run a single simulation with given uncooperative count."""
        uncooperative_count, run_number = args
        
        # Create unique output directory with microsecond precision
        # Include uncooperative count and sweep ID to ensure uniqueness
        timestamp_micro = datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3]
        output_dir = LOGS_DIR / f'sim_{self.sweep_id}_u{uncooperative_count:02d}_{timestamp_micro}'
        
        print(f"[{run_number+1}/11] Starting simulation with {uncooperative_count} uncooperative agents...")
        print(f"         Output: {output_dir.name}")
        
        # Create config
        config_path = self.create_config_variation(uncooperative_count)
        
        # Run simulation
        env = os.environ.copy()
        if 'OPENAI_API_KEY' not in env:
            print(f"  ⚠️ Warning: OPENAI_API_KEY not found in environment")
        
        try:
            # Small stagger to ensure unique timestamps
            time.sleep(0.1 * (run_number % MAX_WORKERS))
            
            cmd = [
                'python', str(MAIN_SCRIPT),
                '--config', str(config_path),
                '--output-dir', str(output_dir)
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                env=env,
                timeout=SIMULATION_TIMEOUT
            )
            elapsed = time.time() - start_time
            
            if result.returncode != 0:
                print(f"  ⚠️ Failed: {uncooperative_count} uncooperative agents")
                print(f"     Error: {result.stderr[:200]}")
                return uncooperative_count, None, elapsed
            
            # Verify the simulation was created
            # main.py creates a subdirectory inside output_dir
            if output_dir.exists():
                # Find the simulation subdirectory (should be the only one)
                subdirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith('simulation_')]
                if subdirs:
                    actual_sim_dir = subdirs[0]
                    log_file = actual_sim_dir / 'simulation_log.jsonl'
                    if log_file.exists():
                        print(f"  ✓ Completed: {uncooperative_count} uncooperative ({elapsed:.1f}s)")
                        return uncooperative_count, str(actual_sim_dir), elapsed
                    else:
                        print(f"  ⚠️ Log file not found in {actual_sim_dir.name}")
                        return uncooperative_count, None, elapsed
                else:
                    print(f"  ⚠️ No simulation subdirectory found in {output_dir.name}")
                    return uncooperative_count, None, elapsed
            else:
                print(f"  ⚠️ Output directory not created for {uncooperative_count} uncooperative")
                return uncooperative_count, None, elapsed
                
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ Timeout: {uncooperative_count} uncooperative agents")
            return uncooperative_count, None, None
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
            return uncooperative_count, None, None
    
    def run_parallel_sweep(self):
        """Run all simulations in parallel."""
        print(f"\n{'='*70}")
        print(f"COMPLETE PARALLEL SWEEP")
        print(f"{'='*70}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Sweep ID: {self.sweep_id}")
        print(f"Sweep directory: {self.sweep_dir}")
        print(f"Simulations: 11 (0-10 uncooperative agents)")
        print(f"Rounds per simulation: {ROUNDS}")
        print(f"Parallel workers: {MAX_WORKERS}")
        print(f"{'='*70}\n")
        
        # Save initial metadata
        initial_metadata = {
            'timestamp': self.timestamp,
            'sweep_id': self.sweep_id,
            'sweep_dir': str(self.sweep_dir),
            'rounds': ROUNDS,
            'agents': AGENTS,
            'uncoop_range': list(UNCOOP_RANGE),
            'max_workers': MAX_WORKERS,
            'start_time': datetime.now().isoformat()
        }
        
        with open(self.sweep_dir / 'sweep_metadata.json', 'w') as f:
            json.dump(initial_metadata, f, indent=2)
        
        # Prepare arguments for parallel execution
        sim_args = [(i, i) for i in UNCOOP_RANGE]
        
        # Run simulations in parallel
        start_time = time.time()
        with Pool(MAX_WORKERS) as pool:
            results = pool.map(self.run_single_simulation, sim_args)
        
        total_elapsed = time.time() - start_time
        
        # Process results
        successful = 0
        simulation_times = []
        
        for uncoop_count, sim_dir, elapsed in results:
            if sim_dir:
                self.results[uncoop_count] = sim_dir
                successful += 1
                if elapsed:
                    simulation_times.append(elapsed)
            else:
                self.results[uncoop_count] = None
        
        # Summary
        print(f"\n{'='*70}")
        print(f"SWEEP COMPLETE")
        print(f"{'='*70}")
        print(f"Successful simulations: {successful}/11")
        print(f"Total time: {total_elapsed:.1f} seconds ({total_elapsed/60:.1f} minutes)")
        if simulation_times:
            print(f"Average time per simulation: {sum(simulation_times)/len(simulation_times):.1f} seconds")
        print(f"Sweep directory: {self.sweep_dir}")
        
        # Save final metadata
        final_metadata = {
            **initial_metadata,
            'end_time': datetime.now().isoformat(),
            'total_elapsed': total_elapsed,
            'successful_count': successful,
            'failed_count': 11 - successful,
            'simulations': {k: str(Path(v).name) if v else None for k, v in self.results.items()},
            'simulation_times': simulation_times
        }
        
        with open(self.sweep_dir / 'sweep_metadata_final.json', 'w') as f:
            json.dump(final_metadata, f, indent=2)
        
        return self.results
    
    def verify_results(self):
        """Verify all simulations completed successfully."""
        print(f"\n{'='*70}")
        print("VERIFICATION")
        print(f"{'='*70}")
        
        for uncoop_count in sorted(self.results.keys()):
            sim_dir = self.results[uncoop_count]
            if sim_dir:
                sim_path = Path(sim_dir)
                log_file = sim_path / 'simulation_log.jsonl'
                
                if log_file.exists():
                    # Count task completions quickly
                    task_count = 0
                    with open(log_file, 'r') as f:
                        for line in f:
                            if '"event_type": "task_completion"' in line and '"success": true' in line:
                                task_count += 1
                    
                    print(f"  {uncoop_count:2d} uncooperative: ✓ ({sim_path.name}, {task_count} tasks)")
                else:
                    print(f"  {uncoop_count:2d} uncooperative: ⚠️ Log file missing")
            else:
                print(f"  {uncoop_count:2d} uncooperative: ✗ Failed")
        
        # Create a mapping file for easy analysis
        mapping = {}
        for uncoop_count, sim_dir in self.results.items():
            if sim_dir:
                mapping[uncoop_count] = str(Path(sim_dir).relative_to(LOGS_DIR))
        
        mapping_file = self.sweep_dir / 'simulation_mapping.json'
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)
        
        print(f"\nSimulation mapping saved to: {mapping_file.name}")
        
        return mapping


def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("COMPLETE SWEEP RUNNER")
    print("="*70)
    print(f"Configuration:")
    print(f"  Agents: {AGENTS}")
    print(f"  Rounds: {ROUNDS}")
    print(f"  Uncooperative range: 0-10")
    print(f"  Total simulations: 11")
    print(f"  Parallel workers: {MAX_WORKERS}")
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
    runner = CompleteSweepRunner()
    
    # Run simulations
    results = runner.run_parallel_sweep()
    
    if not results or all(v is None for v in results.values()):
        print("\n❌ No successful simulations!")
        return
    
    # Verify results
    mapping = runner.verify_results()
    
    print(f"\n{'='*70}")
    print("NEXT STEPS")
    print(f"{'='*70}")
    print("1. To analyze these results, update final_comprehensive_analysis.py with:")
    print(f"   Sweep directory: {runner.sweep_dir}")
    print("\n2. Or run analysis directly on the mapping file")
    print(f"\nAll results saved in: {runner.sweep_dir}")
    

if __name__ == "__main__":
    main()
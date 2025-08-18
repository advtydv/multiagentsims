#!/usr/bin/env python3
"""
Run the missing simulations (1-5 uncooperative agents) in parallel.
Ensures unique naming and integrates with existing results.
"""

import os
import json
import yaml
import subprocess
import time
import shutil
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

# Parameters
ROUNDS = 10
AGENTS = 10
MISSING_UNCOOP_COUNTS = [1, 2, 3, 4, 5]  # The simulations we need to run
MAX_WORKERS = 5  # Run all 5 in parallel
SIMULATION_TIMEOUT = None  # No timeout

class MissingSimulationsRunner:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results = {}
        # Use a more detailed naming scheme to avoid conflicts
        self.run_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        
    def load_base_config(self):
        """Load the base configuration file."""
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    
    def create_config_for_uncoop(self, uncooperative_count):
        """Create a config file for specific uncooperative count."""
        config = self.load_base_config()
        
        # Set our parameters
        config['simulation']['rounds'] = ROUNDS
        config['simulation']['agents'] = AGENTS
        config['agents']['uncooperative_count'] = uncooperative_count
        
        # Save to temporary file with unique name
        config_path = LOGS_DIR / f'temp_config_uncoop_{uncooperative_count}_{self.run_id}.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        return config_path
    
    def run_single_simulation(self, args):
        """Run a single simulation with given uncooperative count."""
        uncooperative_count, run_number = args
        
        print(f"[{run_number}/{len(MISSING_UNCOOP_COUNTS)}] Starting simulation with {uncooperative_count} uncooperative agents...")
        
        # Create unique output directory name to avoid conflicts
        # Use microseconds and random suffix to ensure uniqueness
        time.sleep(0.1 * run_number)  # Small stagger to avoid exact same timestamp
        unique_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3]  # Include milliseconds
        output_dir = LOGS_DIR / f'simulation_{unique_timestamp}_u{uncooperative_count}'
        
        # Create config
        config_path = self.create_config_for_uncoop(uncooperative_count)
        
        # Run simulation with explicit output directory
        env = os.environ.copy()
        if 'OPENAI_API_KEY' not in env:
            print(f"  ⚠️ Warning: OPENAI_API_KEY not found")
        
        try:
            # Run with explicit output directory
            cmd = [
                'python', str(MAIN_SCRIPT),
                '--config', str(config_path),
                '--output-dir', str(output_dir)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                env=env,
                timeout=SIMULATION_TIMEOUT
            )
            
            # Clean up temp config
            try:
                config_path.unlink()
            except:
                pass
            
            if result.returncode != 0:
                print(f"  ⚠️ Simulation failed with {uncooperative_count} uncooperative agents")
                print(f"  Error: {result.stderr[:500]}")
                return uncooperative_count, None
            
            # Verify the simulation was created
            if output_dir.exists():
                print(f"  ✓ Completed: {output_dir.name}")
                return uncooperative_count, str(output_dir)
            else:
                print(f"  ⚠️ Output directory not found: {output_dir}")
                return uncooperative_count, None
                
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ Simulation timed out with {uncooperative_count} uncooperative agents")
            return uncooperative_count, None
        except Exception as e:
            print(f"  ⚠️ Error running simulation: {e}")
            return uncooperative_count, None
        finally:
            # Always try to clean up temp config
            try:
                if config_path.exists():
                    config_path.unlink()
            except:
                pass
    
    def run_missing_simulations(self):
        """Run all missing simulations in parallel."""
        print(f"\n{'='*70}")
        print(f"RUNNING MISSING SIMULATIONS")
        print(f"{'='*70}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Run ID: {self.run_id}")
        print(f"Missing simulations: {MISSING_UNCOOP_COUNTS}")
        print(f"Parallel workers: {MAX_WORKERS}")
        print(f"{'='*70}\n")
        
        # Prepare arguments
        sim_args = [(count, i+1) for i, count in enumerate(MISSING_UNCOOP_COUNTS)]
        
        # Run in parallel
        start_time = time.time()
        with Pool(MAX_WORKERS) as pool:
            results = pool.map(self.run_single_simulation, sim_args)
        
        elapsed = time.time() - start_time
        
        # Store results
        for uncoop_count, sim_dir in results:
            self.results[uncoop_count] = sim_dir
        
        # Summary
        successful = sum(1 for _, sim_dir in results if sim_dir is not None)
        print(f"\n{'='*70}")
        print(f"MISSING SIMULATIONS COMPLETE")
        print(f"{'='*70}")
        print(f"Successful: {successful}/{len(MISSING_UNCOOP_COUNTS)}")
        print(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        
        return self.results
    
    def combine_with_existing(self):
        """Combine new results with existing simulations."""
        # Existing simulations from the partial analysis
        existing = {
            0: 'simulation_20250813_004508',
            6: 'simulation_20250813_011935',
            7: 'simulation_20250813_012055',
            8: 'simulation_20250813_012150',
            9: 'simulation_20250813_012230',
            10: 'simulation_20250813_012310'
        }
        
        # Combine with new results
        all_simulations = existing.copy()
        for uncoop_count, sim_path in self.results.items():
            if sim_path:
                # Extract just the directory name
                sim_name = Path(sim_path).name
                all_simulations[uncoop_count] = sim_name
        
        print(f"\nCombined simulation set:")
        for uncoop in sorted(all_simulations.keys()):
            status = "✓" if uncoop in all_simulations else "✗"
            print(f"  {status} {uncoop} uncooperative: {all_simulations.get(uncoop, 'MISSING')}")
        
        # Save combined metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'all_simulations': all_simulations,
            'existing_simulations': existing,
            'new_simulations': {k: Path(v).name if v else None for k, v in self.results.items()},
            'total_count': len(all_simulations)
        }
        
        metadata_file = LOGS_DIR / f'combined_sweep_metadata_{self.timestamp}.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nCombined metadata saved to: {metadata_file.name}")
        
        return all_simulations


def main():
    """Main execution."""
    print("\n" + "="*70)
    print("MISSING SIMULATIONS RUNNER")
    print("="*70)
    print(f"Target: {MISSING_UNCOOP_COUNTS}")
    print(f"Parallel workers: {MAX_WORKERS}")
    
    # Check for API key
    if 'OPENAI_API_KEY' not in os.environ:
        print("\n⚠️  WARNING: OPENAI_API_KEY not found in environment!")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Run missing simulations
    runner = MissingSimulationsRunner()
    results = runner.run_missing_simulations()
    
    if not any(v is not None for v in results.values()):
        print("\n❌ No successful simulations!")
        return
    
    # Combine with existing
    all_simulations = runner.combine_with_existing()
    
    print(f"\n{'='*70}")
    print("NEXT STEPS")
    print(f"{'='*70}")
    print("1. Run the complete analysis with:")
    print("   python analyze_complete_sweep.py")
    print("\nOr manually analyze using the combined metadata file.")
    

if __name__ == "__main__":
    main()
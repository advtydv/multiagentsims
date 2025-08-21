#!/usr/bin/env python3
"""
Verbose batch runner - shows all output from simulations
Useful for debugging when simulations appear stuck
"""

import argparse
import json
import yaml
import logging
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import os


def run_batch_verbose(config_path: str, num_simulations: int, output_dir: str = "logs"):
    """Run batch with full output visibility"""
    
    # Create batch directory
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = Path(output_dir) / f"batch_{batch_timestamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"BATCH SIMULATION: batch_{batch_timestamp}")
    print(f"Configuration: {config_path}")
    print(f"Simulations: {num_simulations}")
    print(f"Output: {batch_dir}")
    print(f"{'='*60}\n")
    
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Batch metadata
    batch_metadata = {
        "batch_id": f"batch_{batch_timestamp}",
        "num_simulations": num_simulations,
        "config": config,
        "created_at": datetime.now().isoformat(),
        "simulations": []
    }
    
    # Save initial metadata
    with open(batch_dir / "batch_metadata.json", 'w') as f:
        json.dump(batch_metadata, f, indent=2)
    
    # Run simulations
    successful = 0
    failed = 0
    
    for i in range(1, num_simulations + 1):
        sim_id = f"simulation_{i:03d}"
        print(f"\n{'-'*60}")
        print(f"STARTING {sim_id} ({i}/{num_simulations})")
        print(f"{'-'*60}")
        
        start_time = time.time()
        
        # Prepare command
        cmd = [
            sys.executable,
            "main.py",
            "--config", str(Path(config_path).absolute()),
            "--output-dir", str(batch_dir),
            "--log-level", "INFO"
        ]
        
        # Run with output directly to console
        try:
            # Set PYTHONPATH
            env = os.environ.copy()
            env['PYTHONPATH'] = os.getcwd()
            
            # Run simulation
            result = subprocess.run(
                cmd,
                env=env,
                cwd=str(Path(__file__).parent)
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Find and rename the created directory
                created_dirs = [d for d in batch_dir.iterdir() 
                              if d.is_dir() and d.name.startswith('simulation_') 
                              and d != batch_dir / sim_id 
                              and d.stat().st_mtime > start_time - 1]
                
                if created_dirs:
                    created_dir = max(created_dirs, key=lambda d: d.stat().st_mtime)
                    target_dir = batch_dir / sim_id
                    if not target_dir.exists():
                        created_dir.rename(target_dir)
                
                print(f"\n✓ {sim_id} COMPLETED in {duration:.1f}s")
                successful += 1
                
                batch_metadata["simulations"].append({
                    "id": sim_id,
                    "status": "completed",
                    "duration": duration
                })
            else:
                print(f"\n✗ {sim_id} FAILED with exit code {result.returncode}")
                failed += 1
                
                batch_metadata["simulations"].append({
                    "id": sim_id,
                    "status": "failed",
                    "duration": duration
                })
                
        except Exception as e:
            print(f"\n✗ {sim_id} ERROR: {e}")
            failed += 1
            
            batch_metadata["simulations"].append({
                "id": sim_id,
                "status": "error",
                "error": str(e)
            })
    
    # Save final metadata
    batch_metadata["completed_at"] = datetime.now().isoformat()
    with open(batch_dir / "batch_metadata.json", 'w') as f:
        json.dump(batch_metadata, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE")
    print(f"{'='*60}")
    print(f"Successful: {successful}/{num_simulations}")
    print(f"Failed: {failed}/{num_simulations}")
    print(f"Output: {batch_dir}")
    print(f"View at: http://localhost:8080/batch")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Run batch simulations with verbose output')
    parser.add_argument('--num-sims', '-n', type=int, default=3,
                        help='Number of simulations to run')
    parser.add_argument('--config', '-c', type=str, default='config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--output-dir', '-o', type=str, default='logs',
                        help='Base directory for output')
    
    args = parser.parse_args()
    
    run_batch_verbose(args.config, args.num_sims, args.output_dir)


if __name__ == "__main__":
    main()
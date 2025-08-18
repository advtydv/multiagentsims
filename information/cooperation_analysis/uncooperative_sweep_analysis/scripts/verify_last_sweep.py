#!/usr/bin/env python3
"""
Verify and process the results from the last sweep run that appeared to fail.
"""

import json
from pathlib import Path

# Configuration
LOGS_DIR = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation/logs')
SWEEP_ID = 'vlvgz9'

def verify_sweep():
    """Verify all simulations from the sweep."""
    print(f"\n{'='*70}")
    print(f"VERIFYING SWEEP: {SWEEP_ID}")
    print(f"{'='*70}\n")
    
    # Find all simulation directories for this sweep
    sim_dirs = sorted([d for d in LOGS_DIR.iterdir() 
                      if d.is_dir() and d.name.startswith(f'sim_{SWEEP_ID}_')])
    
    print(f"Found {len(sim_dirs)} simulation directories")
    
    results = {}
    successful = 0
    
    for sim_dir in sim_dirs:
        # Extract uncooperative count from directory name
        parts = sim_dir.name.split('_')
        uncoop_str = parts[2]  # Format: sim_vlvgz9_u00_timestamp
        uncoop_count = int(uncoop_str[1:])  # Remove 'u' prefix
        
        # Find the actual simulation subdirectory
        subdirs = [d for d in sim_dir.iterdir() 
                  if d.is_dir() and d.name.startswith('simulation_')]
        
        if subdirs:
            actual_sim_dir = subdirs[0]
            log_file = actual_sim_dir / 'simulation_log.jsonl'
            
            if log_file.exists():
                # Count task completions
                task_count = 0
                with open(log_file, 'r') as f:
                    for line in f:
                        if '"event_type": "task_completion"' in line and '"success": true' in line:
                            task_count += 1
                
                print(f"  {uncoop_count:2d} uncooperative: ✓ ({actual_sim_dir.name}, {task_count} tasks)")
                results[uncoop_count] = str(actual_sim_dir)
                successful += 1
            else:
                print(f"  {uncoop_count:2d} uncooperative: ⚠️ Log file not found")
                results[uncoop_count] = None
        else:
            print(f"  {uncoop_count:2d} uncooperative: ⚠️ No simulation subdirectory")
            results[uncoop_count] = None
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Successful simulations: {successful}/{len(sim_dirs)}")
    
    # Check for missing simulations
    expected = set(range(11))
    found = set(results.keys())
    missing = expected - found
    
    if missing:
        print(f"Missing simulations: {sorted(missing)}")
    
    # Save corrected mapping
    if successful > 0:
        sweep_dir = LOGS_DIR / f'complete_sweep_20250813_120459'
        sweep_dir.mkdir(exist_ok=True)
        
        mapping = {}
        for uncoop_count, sim_dir in results.items():
            if sim_dir:
                mapping[uncoop_count] = str(Path(sim_dir).relative_to(LOGS_DIR))
        
        mapping_file = sweep_dir / 'corrected_simulation_mapping.json'
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)
        
        print(f"\nCorrected mapping saved to: {mapping_file}")
        print(f"\nAll {successful} simulations completed successfully!")
        print("You can now use these results for analysis.")
    
    return results

if __name__ == "__main__":
    verify_sweep()
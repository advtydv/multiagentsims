#!/usr/bin/env python3
"""
Standalone analysis script for completed sweep simulations.
Run this after simulations are complete to generate analysis and visualizations.
"""

import json
import sys
from pathlib import Path
from uncooperative_sweep_runner import UncooperativeSweepRunner

def main():
    # Find the most recent sweep directory
    sweep_dir_pattern = "sweep_20250813_004506"  # Your specific sweep
    
    base_dir = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation/logs')
    sweep_dir = base_dir / sweep_dir_pattern
    
    if not sweep_dir.exists():
        print(f"Error: Sweep directory not found: {sweep_dir}")
        return
    
    print(f"Analyzing sweep: {sweep_dir}")
    
    # Load sweep metadata
    metadata_file = sweep_dir / 'sweep_metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        print(f"Found {metadata['successful_count']} successful simulations")
        
        # Create runner and set up results
        runner = UncooperativeSweepRunner()
        runner.sweep_dir = sweep_dir
        runner.timestamp = metadata['timestamp']
        
        # Convert string keys to integers and handle duplicates
        runner.results = {}
        for key, value in metadata['simulations'].items():
            int_key = int(key)
            runner.results[int_key] = value if value != 'null' else None
        
        # Run analysis
        print("\nStarting comprehensive analysis...")
        try:
            analysis = runner.analyze_results()
            print("\n✓ Analysis complete!")
            print(f"Results saved in: {sweep_dir}")
        except Exception as e:
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"Error: Metadata file not found: {metadata_file}")

if __name__ == "__main__":
    main()
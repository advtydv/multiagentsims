#!/usr/bin/env python3
"""
Script to analyze cooperation scores and points progression for all simulations
or a specific simulation.
"""

import os
import sys
from pathlib import Path
from analysis_v2.visualizers.cooperation_score_tracker import analyze_simulation

def analyze_all_simulations(logs_dir: str = "logs", output_base: str = "cooperation_analysis"):
    """Analyze all simulations in the logs directory"""
    logs_path = Path(logs_dir)
    output_path = Path(output_base)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Find all simulation directories
    sim_dirs = [d for d in logs_path.iterdir() if d.is_dir() and d.name.startswith("simulation_")]
    
    print(f"Found {len(sim_dirs)} simulations to analyze")
    
    successful = 0
    failed = []
    
    for sim_dir in sorted(sim_dirs):
        sim_id = sim_dir.name.replace("simulation_", "")
        
        # Check if log file exists
        log_file = sim_dir / "simulation_log.jsonl"
        if not log_file.exists():
            print(f"  ⚠️  Skipping {sim_id}: No log file found")
            continue
            
        try:
            print(f"\nAnalyzing simulation: {sim_id}")
            analyze_simulation(sim_id, output_path)
            successful += 1
        except Exception as e:
            print(f"  ❌ Failed to analyze {sim_id}: {e}")
            failed.append((sim_id, str(e)))
            
    print(f"\n{'='*50}")
    print(f"Analysis complete!")
    print(f"  ✓ Successful: {successful}")
    print(f"  ✗ Failed: {len(failed)}")
    
    if failed:
        print("\nFailed simulations:")
        for sim_id, error in failed:
            print(f"  - {sim_id}: {error}")
            
    print(f"\nVisualizations saved to: {output_path}")


def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        # Analyze all simulations
        print("Analyzing all simulations...")
        analyze_all_simulations()
    elif len(sys.argv) == 2:
        # Analyze specific simulation
        sim_id = sys.argv[1]
        print(f"Analyzing simulation: {sim_id}")
        try:
            analyze_simulation(sim_id)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif len(sys.argv) == 3:
        # Analyze specific simulation with custom output
        sim_id = sys.argv[1]
        output_dir = sys.argv[2]
        print(f"Analyzing simulation: {sim_id}")
        print(f"Output directory: {output_dir}")
        try:
            analyze_simulation(sim_id, output_dir)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print("Usage:")
        print("  python analyze_cooperation.py                    # Analyze all simulations")
        print("  python analyze_cooperation.py <simulation_id>    # Analyze specific simulation")
        print("  python analyze_cooperation.py <simulation_id> <output_dir>")
        sys.exit(1)


if __name__ == "__main__":
    main()
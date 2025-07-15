#!/usr/bin/env python3
"""
Run comprehensive analysis on all simulation folders that have simulation_log.jsonl
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def find_simulations_to_analyze():
    """Find all simulation folders with simulation_log.jsonl that haven't been analyzed yet"""
    logs_dir = Path("logs")
    simulations_to_analyze = []
    already_analyzed = []
    
    for sim_dir in sorted(logs_dir.iterdir()):
        if sim_dir.is_dir() and sim_dir.name.startswith("simulation_"):
            log_file = sim_dir / "simulation_log.jsonl"
            analysis_dir = sim_dir / "analysis"
            
            if log_file.exists():
                # Check if already analyzed (has analysis directory with results)
                if analysis_dir.exists() and any(f.name.startswith("analysis_results_") for f in analysis_dir.iterdir()):
                    already_analyzed.append(sim_dir.name)
                else:
                    simulations_to_analyze.append(sim_dir.name)
    
    return simulations_to_analyze, already_analyzed

def run_analysis(simulation_id):
    """Run the analysis for a specific simulation"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {simulation_id}")
    print(f"{'='*80}")
    
    try:
        # Run the analysis using the analyzer module
        cmd = [sys.executable, "-m", "analysis.main_analyzer", simulation_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Successfully analyzed {simulation_id}")
            return True
        else:
            print(f"✗ Failed to analyze {simulation_id}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Exception while analyzing {simulation_id}: {e}")
        return False

def main():
    """Main function to run all analyses"""
    print("Comprehensive Analysis Runner")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Find simulations
    to_analyze, already_analyzed = find_simulations_to_analyze()
    
    print(f"\nFound {len(to_analyze)} simulations to analyze")
    print(f"Found {len(already_analyzed)} simulations already analyzed")
    
    if already_analyzed:
        print("\nAlready analyzed:")
        for sim in already_analyzed:
            print(f"  - {sim}")
    
    if not to_analyze:
        print("\nNo new simulations to analyze!")
        return
    
    print(f"\nWill analyze the following {len(to_analyze)} simulations:")
    for sim in to_analyze:
        print(f"  - {sim}")
    
    # Run analyses
    successful = 0
    failed = 0
    
    for i, sim_id in enumerate(to_analyze, 1):
        print(f"\n[{i}/{len(to_analyze)}] Processing {sim_id}...")
        
        if run_analysis(sim_id):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print(f"Total simulations processed: {len(to_analyze)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Previously analyzed: {len(already_analyzed)}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
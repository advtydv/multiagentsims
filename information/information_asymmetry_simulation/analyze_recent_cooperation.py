#!/usr/bin/env python3
"""
Analyze cooperation scores for recent simulations (July 2025 onwards)
that have the cooperation scoring feature.
"""

from pathlib import Path
from analysis_v2.visualizers.cooperation_score_tracker import analyze_simulation

# List of simulations with cooperation scores
RECENT_SIMULATIONS = [
    "20250722_111520",
    "20250722_121551", 
    "20250722_122006",
    "20250722_130201",
    "20250722_175455",
    "20250723_133753",
    "20250723_142751",
    "20250723_183534",
    "20250723_200908",
    "20250723_202600"
]

def main():
    """Analyze all recent simulations with cooperation scores"""
    output_dir = Path("cooperation_analysis")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"Analyzing {len(RECENT_SIMULATIONS)} recent simulations...")
    print(f"Output directory: {output_dir}\n")
    
    successful = 0
    failed = []
    
    for sim_id in RECENT_SIMULATIONS:
        try:
            print(f"\nAnalyzing simulation: {sim_id}")
            analyze_simulation(sim_id, output_dir)
            successful += 1
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed.append((sim_id, str(e)))
            
    print(f"\n{'='*50}")
    print(f"Analysis complete!")
    print(f"  ✓ Successful: {successful}")
    print(f"  ✗ Failed: {len(failed)}")
    
    if failed:
        print("\nFailed simulations:")
        for sim_id, error in failed:
            print(f"  - {sim_id}: {error}")

if __name__ == "__main__":
    main()
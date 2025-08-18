#!/usr/bin/env python3
"""
Analyze the latest complete sweep results.
Automatically finds the most recent sweep and runs comprehensive analysis.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import the analysis functions from our comprehensive script
sys.path.append('/Users/Aadi/Desktop/playground/multiagent/information')
from final_comprehensive_analysis import extract_simulation_metrics, create_comprehensive_visualizations, perform_statistical_tests

import matplotlib.pyplot as plt
import numpy as np

BASE_PATH = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation/logs')


def find_latest_sweep():
    """Find the most recent complete_sweep directory."""
    sweep_dirs = list(BASE_PATH.glob('complete_sweep_*'))
    if not sweep_dirs:
        print("No complete sweep directories found!")
        return None
    
    # Get the most recent one
    latest = max(sweep_dirs, key=lambda p: p.stat().st_mtime)
    return latest


def load_sweep_mapping(sweep_dir):
    """Load the simulation mapping from a sweep directory."""
    # Try corrected mapping first (from verification script)
    corrected_mapping = sweep_dir / 'corrected_simulation_mapping.json'
    if corrected_mapping.exists():
        print(f"Using corrected mapping file")
        with open(corrected_mapping, 'r') as f:
            return json.load(f)
    
    # Fall back to original mapping
    mapping_file = sweep_dir / 'simulation_mapping.json'
    if mapping_file.exists():
        print(f"Using original mapping file")
        with open(mapping_file, 'r') as f:
            return json.load(f)
    
    print(f"No mapping file found in {sweep_dir}")
    print(f"Looked for: corrected_simulation_mapping.json and simulation_mapping.json")
    return None


def analyze_sweep(sweep_dir=None):
    """Analyze a complete sweep."""
    
    # Find sweep directory
    if sweep_dir is None:
        sweep_dir = find_latest_sweep()
        if sweep_dir is None:
            return
    else:
        sweep_dir = Path(sweep_dir)
    
    print("="*80)
    print("ANALYZING COMPLETE SWEEP RESULTS")
    print("="*80)
    print(f"Sweep directory: {sweep_dir.name}")
    print(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load mapping
    mapping = load_sweep_mapping(sweep_dir)
    if not mapping:
        return
    
    print(f"Found {len(mapping)} simulations in mapping")
    print("="*80)
    
    # Extract metrics for all simulations
    print("\nExtracting simulation data...")
    analysis_data = {}
    
    for uncoop_str, sim_path in mapping.items():
        uncoop_count = int(uncoop_str)
        full_path = BASE_PATH / sim_path
        
        print(f"  Processing {uncoop_count} uncooperative agents...")
        metrics = extract_simulation_metrics(sim_path)
        
        if metrics:
            analysis_data[uncoop_count] = metrics
            print(f"    ✓ Tasks: {metrics['task_completions']:3d}, "
                  f"Messages: {metrics['messages']:3d}, "
                  f"Deceptions: {metrics['deception_attempts']:3d}")
        else:
            print(f"    ✗ Failed to extract data")
    
    if len(analysis_data) != 11:
        print(f"\nWarning: Only {len(analysis_data)}/11 simulations processed successfully")
        missing = [i for i in range(11) if i not in analysis_data]
        if missing:
            print(f"Missing: {missing}")
    
    # Create visualizations
    print("\nGenerating comprehensive visualizations...")
    fig, stats_results = create_comprehensive_visualizations(analysis_data)
    
    # Save in sweep directory
    output_file = sweep_dir / 'sweep_analysis.png'
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved visualization to {output_file}")
    plt.close()
    
    # Also save in main directory for easy access
    main_output = 'latest_sweep_analysis.png'
    fig.savefig(main_output, dpi=300, bbox_inches='tight')
    print(f"  ✓ Also saved to {main_output}")
    
    # Prepare results
    uncoop_counts = sorted(analysis_data.keys())
    task_completions = [analysis_data[u]['task_completions'] for u in uncoop_counts]
    
    # Print key findings
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    
    baseline = task_completions[0] if 0 in analysis_data else 22
    print(f"\n1. Performance Overview:")
    print(f"   - Baseline (0 uncooperative): {baseline} tasks")
    print(f"   - Best performance: {max(task_completions)} tasks at {uncoop_counts[task_completions.index(max(task_completions))]} uncooperative")
    print(f"   - Worst performance: {min(task_completions)} tasks at {uncoop_counts[task_completions.index(min(task_completions))]} uncooperative")
    
    # Check for improvements over baseline
    improvements = []
    for i, u in enumerate(uncoop_counts):
        if task_completions[i] > baseline:
            improvement = (task_completions[i] - baseline) / baseline * 100
            improvements.append((u, task_completions[i], improvement))
    
    if improvements:
        print(f"\n2. ⚠️ Paradoxical Improvements Detected:")
        for uncoop, tasks, improvement in improvements:
            print(f"   - {uncoop} uncooperative: {tasks} tasks (+{improvement:.1f}% vs baseline)")
    
    # Statistical summary
    print(f"\n3. Statistical Summary:")
    print(f"   - Mean: {np.mean(task_completions):.1f} tasks")
    print(f"   - Median: {np.median(task_completions):.1f} tasks")
    print(f"   - Std Dev: {np.std(task_completions):.1f} tasks")
    print(f"   - Range: {min(task_completions)} - {max(task_completions)} tasks")
    
    # Save complete results
    results = {
        'sweep_info': {
            'sweep_dir': str(sweep_dir.name),
            'analysis_timestamp': datetime.now().isoformat(),
            'total_simulations': len(analysis_data)
        },
        'raw_data': {
            'uncooperative_counts': uncoop_counts,
            'task_completions': task_completions,
            'messages': [analysis_data[u]['messages'] for u in uncoop_counts],
            'deceptions': [analysis_data[u]['deception_attempts'] for u in uncoop_counts]
        },
        'statistical_analysis': stats_results if 'stats_results' in locals() else {},
        'key_findings': {
            'baseline_performance': baseline,
            'best_performance': {
                'count': uncoop_counts[task_completions.index(max(task_completions))],
                'tasks': max(task_completions)
            },
            'worst_performance': {
                'count': uncoop_counts[task_completions.index(min(task_completions))],
                'tasks': min(task_completions)
            },
            'paradoxical_improvements': improvements
        }
    }
    
    # Save in sweep directory
    results_file = sweep_dir / 'sweep_analysis_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  ✓ Saved results to {results_file}")
    
    # Also save in main directory
    with open('latest_sweep_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  ✓ Also saved to latest_sweep_analysis_results.json")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nAll results saved in:")
    print(f"  - {sweep_dir}/")
    print(f"  - latest_sweep_analysis.png")
    print(f"  - latest_sweep_analysis_results.json")
    
    return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze complete sweep results')
    parser.add_argument('--sweep-dir', type=str, help='Specific sweep directory to analyze')
    parser.add_argument('--list', action='store_true', help='List all available sweeps')
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable sweeps:")
        sweep_dirs = sorted(BASE_PATH.glob('complete_sweep_*'))
        for sweep in sweep_dirs:
            # Check if it has a mapping file (either corrected or original)
            has_corrected = (sweep / 'corrected_simulation_mapping.json').exists()
            has_original = (sweep / 'simulation_mapping.json').exists()
            if has_corrected:
                print(f"  - {sweep.name} ✓ (corrected)")
            elif has_original:
                print(f"  - {sweep.name} ✓")
            else:
                print(f"  - {sweep.name} (incomplete)")
        return
    
    if args.sweep_dir:
        sweep_path = BASE_PATH / args.sweep_dir
        if not sweep_path.exists():
            print(f"Sweep directory not found: {args.sweep_dir}")
            return
        analyze_sweep(sweep_path)
    else:
        # Analyze the latest sweep
        analyze_sweep()


if __name__ == "__main__":
    main()
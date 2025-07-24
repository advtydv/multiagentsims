#!/usr/bin/env python3
"""
Main entry point for the revamped analysis pipeline v2

Usage:
    python analyze_v2.py <simulation_id> [--config CONFIG_PATH] [--output OUTPUT_DIR]
    
Example:
    python analyze_v2.py simulation_20250714_204152
    python analyze_v2.py simulation_20250714_204152 --config my_config.yaml
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analysis_v2.pipeline import AnalysisPipeline


def main():
    """Main entry point for analysis"""
    parser = argparse.ArgumentParser(
        description="Analyze Information Asymmetry Simulation Results (v2.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a specific simulation
  python analyze_v2.py simulation_20250714_204152
  
  # Use custom configuration
  python analyze_v2.py simulation_20250714_204152 --config my_config.yaml
  
  # Specify output directory
  python analyze_v2.py simulation_20250714_204152 --output results/my_analysis
  
  # Analyze all simulations in logs directory
  python analyze_v2.py --all
        """
    )
    
    # Arguments
    parser.add_argument(
        'simulation_id',
        nargs='?',
        help='ID of the simulation to analyze (e.g., simulation_20250714_204152)'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file (YAML format)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output directory for results (default: logs/<sim_id>/analysis_v2)'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Analyze all simulations in the logs directory'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching (force fresh analysis)'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick analysis mode (skip visualizations)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all and not args.simulation_id:
        parser.error("Either provide a simulation_id or use --all flag")
        
    # Handle --all flag
    if args.all:
        analyze_all_simulations(args)
    else:
        analyze_single_simulation(args.simulation_id, args)
        

def analyze_single_simulation(simulation_id: str, args):
    """Analyze a single simulation"""
    # Check if simulation exists
    log_path = Path(f"logs/{simulation_id}")
    if not log_path.exists():
        print(f"Error: Simulation '{simulation_id}' not found in logs directory")
        sys.exit(1)
        
    # Check for simulation_log.jsonl
    if not (log_path / "simulation_log.jsonl").exists():
        print(f"Error: No simulation_log.jsonl found for '{simulation_id}'")
        print("This analysis requires the unified log format.")
        sys.exit(1)
        
    try:
        # Create pipeline
        pipeline = AnalysisPipeline(
            simulation_id=simulation_id,
            config_path=args.config,
            output_dir=args.output
        )
        
        # Override config if needed
        if args.no_cache:
            pipeline.config['cache_enabled'] = False
            
        if args.quick:
            pipeline.config['visualizations']['create_all'] = False
            
        # Run analysis
        results = pipeline.run()
        
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        if not args.all:  # Only exit if not analyzing all
            import traceback
            traceback.print_exc()
            sys.exit(1)
        else:
            raise  # Re-raise to be caught by analyze_all_simulations
        

def analyze_all_simulations(args):
    """Analyze all simulations in the logs directory"""
    logs_dir = Path("logs")
    
    if not logs_dir.exists():
        print("Error: logs directory not found")
        sys.exit(1)
        
    # Find all simulations with the new log format
    simulations = []
    for sim_dir in logs_dir.iterdir():
        if sim_dir.is_dir() and sim_dir.name.startswith("simulation_"):
            if (sim_dir / "simulation_log.jsonl").exists():
                simulations.append(sim_dir.name)
                
    if not simulations:
        print("No simulations found with the unified log format")
        sys.exit(1)
        
    print(f"Found {len(simulations)} simulations to analyze")
    print("-" * 60)
    
    # Analyze each simulation
    failed = []
    for i, sim_id in enumerate(simulations, 1):
        print(f"\n[{i}/{len(simulations)}] Analyzing {sim_id}...")
        
        try:
            analyze_single_simulation(sim_id, args)
        except Exception as e:
            print(f"  Failed: {str(e)}")
            failed.append(sim_id)
            
    # Summary
    print("\n" + "=" * 60)
    print(f"Analysis complete: {len(simulations) - len(failed)} succeeded, {len(failed)} failed")
    
    if failed:
        print("\nFailed simulations:")
        for sim_id in failed:
            print(f"  - {sim_id}")
            

if __name__ == "__main__":
    main()
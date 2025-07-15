#!/usr/bin/env python3
"""
Test script for the visualization module.

This script tests the visualizer with existing simulation data.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.main_analyzer import ComprehensiveAnalyzer


def test_visualizer():
    """Test the visualizer with existing simulation data."""
    # Find the most recent simulation
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("No logs directory found!")
        return
        
    # Get all simulation directories
    sim_dirs = [d for d in logs_dir.iterdir() if d.is_dir() and d.name.startswith("simulation_")]
    
    if not sim_dirs:
        print("No simulation logs found!")
        return
        
    # Sort by name (which includes timestamp) and get the most recent
    most_recent = sorted(sim_dirs)[-1]
    simulation_id = most_recent.name
    
    print(f"Testing visualizer with simulation: {simulation_id}")
    print("-" * 50)
    
    try:
        # Create analyzer
        analyzer = ComprehensiveAnalyzer(simulation_id)
        
        # Create output directory for test
        output_dir = most_recent / "test_visualizations"
        output_dir.mkdir(exist_ok=True)
        
        # Run analysis
        print("Running analysis...")
        results = analyzer.analyze_all()
        
        # Import and run visualizer directly
        from analysis.visualizer import create_visualizations
        
        print("\nTesting visualization generation...")
        create_visualizations(analyzer.log_data, results, output_dir)
        
        print(f"\nSuccess! Visualizations saved to: {output_dir}")
        print("\nGenerated files:")
        for file in sorted(output_dir.glob("*.png")):
            print(f"  - {file.name}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_visualizer()
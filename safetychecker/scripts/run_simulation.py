#!/usr/bin/env python3
"""
Multi-Agent Safety Oversight Simulation Runner

This script runs the safety checker simulation and performs analysis on the results.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Debug: Check multiple sources
    if not api_key:
        # Try loading from .env file
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        # Check if it's in os.environ directly
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key using one of these methods:")
        print("  1. export OPENAI_API_KEY='your-key-here'")
        print("  2. Create a .env file with: OPENAI_API_KEY=your-key-here")
        print("\nDebug info:")
        print(f"  - Current working directory: {os.getcwd()}")
        print(f"  - .env file exists: {os.path.exists('.env')}")
        sys.exit(1)
    
    print(f"✓ API key found (length: {len(api_key)} characters)")
    
    # Import simulation after checking API key
    from safetychecker.simulation import MultiAgentSimulation
    
    print("🚀 Multi-Agent Safety Oversight Simulation")
    print("=" * 50)
    
    # Get number of rounds
    num_rounds = 50  # Default
    if len(sys.argv) > 1:
        try:
            num_rounds = int(sys.argv[1])
        except ValueError:
            print(f"Warning: Invalid number of rounds '{sys.argv[1]}', using default of 50")
    
    print(f"Running simulation for {num_rounds} rounds...")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run simulation
    try:
        simulation = MultiAgentSimulation(api_key=api_key, num_rounds=num_rounds)
        simulation.run_simulation()
        
        # Get the latest report file
        import glob
        report_files = glob.glob("logs/simulation_report_*.json")
        if report_files:
            latest_report = max(report_files, key=os.path.getctime)
            
            print(f"\n✅ Simulation completed successfully!")
            print(f"Report saved to: {latest_report}")
            
            # Ask if user wants to run analysis
            response = input("\nWould you like to run the analysis? (y/n): ")
            if response.lower() == 'y':
                print("\n🔍 Running analysis...")
                from safetychecker.analysis import SimulationAnalyzer
                analyzer = SimulationAnalyzer(latest_report)
                analyzer.analyze_all()
        
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"\n🏁 Complete! End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
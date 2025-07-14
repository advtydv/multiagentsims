#!/usr/bin/env python3
"""
Main runner script for the Coalition Instability simulation.
"""

import argparse
import os
import sys
from datetime import datetime

from environment import Environment


def main():
    """Main entry point for the simulation."""
    parser = argparse.ArgumentParser(
        description="Run the Coalition Instability under Resource Pressure simulation"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for log file (overrides config)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenAI API key (overrides config)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without running simulation"
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file '{args.config}' not found.")
        sys.exit(1)
    
    # Create environment and load configuration
    env = Environment()
    
    try:
        env.load_config(args.config)
        print(f"Configuration loaded from '{args.config}'")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Override config with command line arguments if provided
    if args.api_key:
        env.config['openai']['api_key'] = args.api_key
        print("Using API key from command line")
    
    if args.output:
        output_path = args.output
    else:
        output_path = env.config.get('logging', {}).get('output_path', 'simulation_log.csv')
    
    # Check API key
    api_key = env.config['openai']['api_key']
    if not api_key or api_key == 'YOUR_OPENAI_API_KEY':
        print("\nError: OpenAI API key not configured!")
        print("Please either:")
        print("1. Update 'openai.api_key' in config.yaml")
        print("2. Pass --api-key YOUR_KEY as a command line argument")
        print("3. Set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    # If environment variable is set and no key provided, use it
    if api_key == 'YOUR_OPENAI_API_KEY' and 'OPENAI_API_KEY' in os.environ:
        env.config['openai']['api_key'] = os.environ['OPENAI_API_KEY']
        print("Using API key from OPENAI_API_KEY environment variable")
    
    if args.dry_run:
        print("\nDry run mode - configuration validated successfully!")
        print(f"\nSimulation settings:")
        print(f"- Max turns: {env.config['simulation']['max_turns']}")
        print(f"- Initial resource pool: {env.config['simulation']['initial_main_pool']}")
        print(f"- Replenishment rate: {env.config['simulation']['replenishment_rate']}")
        print(f"- Number of agents: {env.config['agents']['count']}")
        print(f"- Number of coalitions: {len(env.config['coalitions']['initial_coalitions'])}")
        print(f"- Output file: {output_path}")
        return
    
    # Setup and run simulation
    try:
        print("\nInitializing simulation...")
        env.setup_simulation()
        
        print("\nRunning simulation...")
        print("=" * 50)
        env.run_full_simulation()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_path.endswith('.csv'):
            output_path = f"{output_path}_{timestamp}.csv"
        else:
            base, ext = os.path.splitext(output_path)
            output_path = f"{base}_{timestamp}{ext}"
        
        env.save_log(output_path)
        
        print(f"\nSimulation complete! Results saved to: {output_path}")
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"- Total turns: {env.turn_number}")
        print(f"- Final main resource pool: {env.main_resource_pool:.2f}")
        print(f"- Total events logged: {len(env.log)}")
        
        # API usage stats
        total_api_calls = sum(agent.api_calls for agent in env.agents.values())
        failed_api_calls = sum(agent.failed_api_calls for agent in env.agents.values())
        print(f"- Total API calls: {total_api_calls}")
        if failed_api_calls > 0:
            print(f"- Failed API calls: {failed_api_calls}")
        
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        # Still try to save partial results
        if env.log:
            emergency_output = f"interrupted_{timestamp}.csv"
            env.save_log(emergency_output)
            print(f"Partial results saved to: {emergency_output}")
    except Exception as e:
        print(f"\nError during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
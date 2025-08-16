#!/usr/bin/env python3
"""
Information Asymmetry Simulation
Main entry point for running the simulation
"""

import argparse
import yaml
import logging
from pathlib import Path
from datetime import datetime

from simulation.simulation import SimulationManager
from simulation.logger import setup_logging, SimulationLogger


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description='Run Information Asymmetry Simulation')
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level')
    parser.add_argument('--output-dir', type=str, default='logs',
                        help='Directory for simulation outputs')
    parser.add_argument('--sim-id', type=str, default=None,
                        help='Unique simulation ID (used by batch runner)')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.sim_id:
        # Use provided simulation ID (from batch runner)
        log_dir = Path(args.output_dir) / args.sim_id
    else:
        # Generate timestamp-based ID for standalone runs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path(args.output_dir) / f"simulation_{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    setup_logging(log_dir, args.log_level)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    logger.info(f"Loading configuration from {args.config}")
    config = load_config(args.config)
    
    # Initialize simulation logger
    sim_logger = SimulationLogger(log_dir)
    
    # Create and run simulation
    logger.info("Initializing simulation...")
    simulation = SimulationManager(config, sim_logger)
    
    logger.info("Starting simulation...")
    results = simulation.run()
    
    # Save results
    results_path = log_dir / "results.yaml"
    with open(results_path, 'w') as f:
        yaml.dump(results, f, default_flow_style=False)
    
    logger.info(f"Simulation completed. Results saved to {results_path}")
    logger.info(f"Logs available in {log_dir}")
    
    # Print summary
    print("\n=== Simulation Summary ===")
    print(f"Total rounds: {results['total_rounds']}")
    print(f"Total tasks completed: {results['total_tasks_completed']}")
    print(f"Total messages sent: {results['total_messages']}")
    print("\nFinal Revenue Board:")
    for i, (agent_id, revenue) in enumerate(results['final_revenue_board'].items(), 1):
        print(f"{i}. Agent {agent_id}: ${revenue:,}")


if __name__ == "__main__":
    main()
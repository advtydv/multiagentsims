#!/usr/bin/env python3
"""
Script to run analysis on all existing simulations that don't have analysis_results.json
"""

import json
import logging
from pathlib import Path
from datetime import datetime
import sys

from simulation.analysis import SimulationAnalyzer

def setup_logging():
    """Setup logging for the analysis script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def analyze_existing_simulations(logs_dir: Path = Path("logs")):
    """Run analysis on all existing simulations"""
    logger = logging.getLogger(__name__)
    
    if not logs_dir.exists():
        logger.error(f"Logs directory not found: {logs_dir}")
        return
    
    # Find all simulation directories
    simulation_dirs = []
    batch_dirs = []
    
    for item in logs_dir.iterdir():
        if item.is_dir():
            # Check if it's a simulation directory (contains simulation_log.jsonl)
            if (item / "simulation_log.jsonl").exists():
                simulation_dirs.append(item)
            # Check if it's a batch directory
            elif item.name.startswith("batch_"):
                batch_dirs.append(item)
    
    # Also check simulation directories within batch directories
    for batch_dir in batch_dirs:
        for item in batch_dir.iterdir():
            if item.is_dir() and (item / "simulation_log.jsonl").exists():
                simulation_dirs.append(item)
    
    logger.info(f"Found {len(simulation_dirs)} simulation directories")
    
    # Track statistics
    already_analyzed = 0
    successfully_analyzed = 0
    failed_analysis = 0
    skipped_incomplete = 0
    
    for sim_dir in sorted(simulation_dirs):
        analysis_file = sim_dir / "analysis_results.json"
        
        # Check if analysis already exists
        if analysis_file.exists():
            logger.info(f"✓ {sim_dir.name} - Already has analysis")
            already_analyzed += 1
            continue
        
        # Check if simulation has required log file
        log_file = sim_dir / "simulation_log.jsonl"
        if not log_file.exists():
            logger.warning(f"✗ {sim_dir.name} - Missing simulation_log.jsonl")
            skipped_incomplete += 1
            continue
        
        # Check if log file has content
        if log_file.stat().st_size == 0:
            logger.warning(f"✗ {sim_dir.name} - Empty simulation_log.jsonl")
            skipped_incomplete += 1
            continue
        
        # Run analysis
        logger.info(f"→ {sim_dir.name} - Running analysis...")
        try:
            analyzer = SimulationAnalyzer(sim_dir)
            results = analyzer.analyze()
            
            # Verify the analysis file was created
            if analysis_file.exists():
                logger.info(f"✓ {sim_dir.name} - Analysis completed successfully")
                successfully_analyzed += 1
                
                # Log key metrics
                metrics = results.get('metrics', {})
                tasks = metrics.get('total_tasks_completed', 0)
                gini = metrics.get('revenue_distribution', {}).get('gini_coefficient')
                efficiency = metrics.get('communication_efficiency', {}).get('messages_per_completed_task')
                
                logger.info(f"  Tasks: {tasks}, Gini: {gini}, Efficiency: {efficiency}")
            else:
                logger.error(f"✗ {sim_dir.name} - Analysis file not created")
                failed_analysis += 1
                
        except FileNotFoundError as e:
            logger.error(f"✗ {sim_dir.name} - File not found: {e}")
            skipped_incomplete += 1
        except json.JSONDecodeError as e:
            logger.error(f"✗ {sim_dir.name} - Invalid JSON in log: {e}")
            failed_analysis += 1
        except Exception as e:
            logger.error(f"✗ {sim_dir.name} - Analysis failed: {e}")
            failed_analysis += 1
    
    # Print summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total simulations found:     {len(simulation_dirs)}")
    print(f"Already analyzed:            {already_analyzed}")
    print(f"Successfully analyzed:       {successfully_analyzed}")
    print(f"Failed analysis:            {failed_analysis}")
    print(f"Skipped (incomplete):       {skipped_incomplete}")
    print("="*60)
    
    if successfully_analyzed > 0:
        print(f"\n✅ Successfully added analysis to {successfully_analyzed} simulations")
    
    return {
        'total': len(simulation_dirs),
        'already_analyzed': already_analyzed,
        'successfully_analyzed': successfully_analyzed,
        'failed': failed_analysis,
        'skipped': skipped_incomplete
    }

def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Parse command line arguments
    logs_dir = Path("logs")
    if len(sys.argv) > 1:
        logs_dir = Path(sys.argv[1])
    
    logger.info(f"Analyzing simulations in: {logs_dir}")
    
    # Run analysis
    results = analyze_existing_simulations(logs_dir)
    
    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
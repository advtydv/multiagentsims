#!/usr/bin/env python3
"""
Update all existing simulation analyses with the new total_revenue_by_round metric
"""

import json
import logging
from pathlib import Path
from simulation.analysis import SimulationAnalyzer
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def update_simulation_analysis(sim_dir: Path) -> tuple[bool, str]:
    """
    Update a single simulation's analysis with the new metric.
    Returns (success, message)
    """
    try:
        # Check if simulation_log.jsonl exists
        log_file = sim_dir / 'simulation_log.jsonl'
        if not log_file.exists():
            return False, f"No simulation_log.jsonl found"
        
        # Check if analysis already has the new metric
        analysis_file = sim_dir / 'analysis_results.json'
        if analysis_file.exists():
            with open(analysis_file, 'r') as f:
                existing = json.load(f)
                if 'total_revenue_by_round' in existing.get('metrics', {}):
                    # Check if it's just empty/placeholder data
                    revenue_data = existing['metrics']['total_revenue_by_round']
                    if revenue_data and any(r.get('cumulative_revenue', 0) > 0 for r in revenue_data):
                        return True, "Already has revenue tracking (with data)"
        
        # Run the analysis
        analyzer = SimulationAnalyzer(sim_dir)
        results = analyzer.analyze()
        
        # Verify the new metric exists
        if 'total_revenue_by_round' not in results.get('metrics', {}):
            return False, "Failed to add revenue tracking"
        
        # Get summary info
        final_round = results['metrics']['total_revenue_by_round'][-1] if results['metrics']['total_revenue_by_round'] else {}
        total_revenue = final_round.get('cumulative_revenue', 0)
        
        return True, f"Updated (Total revenue: ${total_revenue:,.2f})"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    logs_dir = Path('logs')
    
    # Find all simulation directories
    sim_dirs = []
    
    # Direct simulation_* directories
    sim_dirs.extend(sorted(logs_dir.glob('simulation_*')))
    
    # Batch simulations
    for batch_dir in sorted(logs_dir.glob('batch_*')):
        sim_dirs.extend(sorted(batch_dir.glob('simulation_*')))
    
    # Special format simulations
    for special_dir in sorted(logs_dir.glob('sim_*')):
        # Check if it has a nested simulation directory
        nested = list(special_dir.glob('simulation_*'))
        if nested:
            sim_dirs.extend(nested)
        else:
            # It might be a direct simulation directory
            if (special_dir / 'simulation_log.jsonl').exists():
                sim_dirs.append(special_dir)
    
    logger.info(f"Found {len(sim_dirs)} simulation directories to process\n")
    
    # Track results
    successful = []
    failed = []
    skipped = []
    
    # Process each simulation
    for i, sim_dir in enumerate(sim_dirs, 1):
        rel_path = sim_dir.relative_to(logs_dir)
        logger.info(f"[{i}/{len(sim_dirs)}] Processing {rel_path}...")
        
        success, message = update_simulation_analysis(sim_dir)
        
        if success:
            if "Already has" in message:
                skipped.append((rel_path, message))
                logger.info(f"  ⟳ {message}")
            else:
                successful.append((rel_path, message))
                logger.info(f"  ✓ {message}")
        else:
            failed.append((rel_path, message))
            logger.info(f"  ✗ {message}")
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total simulations: {len(sim_dirs)}")
    logger.info(f"Successfully updated: {len(successful)}")
    logger.info(f"Already had metric: {len(skipped)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info("\n✓ Successfully Updated:")
        for path, msg in successful[:10]:  # Show first 10
            logger.info(f"  - {path}: {msg}")
        if len(successful) > 10:
            logger.info(f"  ... and {len(successful) - 10} more")
    
    if failed:
        logger.info("\n✗ Failed Updates:")
        for path, msg in failed[:10]:  # Show first 10
            logger.info(f"  - {path}: {msg}")
        if len(failed) > 10:
            logger.info(f"  ... and {len(failed) - 10} more")

if __name__ == "__main__":
    main()
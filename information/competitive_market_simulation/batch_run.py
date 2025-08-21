#!/usr/bin/env python3
"""
Batch runner for Competitive Market Simulations
Runs multiple market simulations with the same configuration and saves results in a batch folder
"""

import argparse
import json
import yaml
import logging
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import os


class BatchSimulationRunner:
    """Manages running multiple simulations in batch mode"""
    
    def __init__(self, config_path: str, num_simulations: int, 
                 output_dir: str = "logs", log_level: str = "INFO",
                 parallel: bool = False, max_workers: Optional[int] = None):
        self.config_path = Path(config_path).absolute()
        self.num_simulations = num_simulations
        self.output_base = Path(output_dir)
        self.log_level = log_level
        self.parallel = parallel
        self.max_workers = max_workers or multiprocessing.cpu_count()
        
        # Create batch directory
        self.batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.batch_dir = self.output_base / f"batch_{self.batch_timestamp}"
        self.batch_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup batch logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize batch metadata
        self.batch_metadata = {
            "batch_id": f"batch_{self.batch_timestamp}",
            "num_simulations": num_simulations,
            "config_path": str(self.config_path),
            "config": self.config,
            "parallel_execution": parallel,
            "max_workers": self.max_workers if parallel else 1,
            "created_at": datetime.now().isoformat(),
            "simulations": [],
            "status": "running"
        }
        
    def setup_logging(self):
        """Setup logging for the batch runner"""
        log_file = self.batch_dir / "batch_run.log"
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, self.log_level))
        file_handler.setFormatter(formatter)
        
        # Console handler with custom formatter for progress
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
    def save_batch_metadata(self):
        """Save batch metadata to file"""
        metadata_path = self.batch_dir / "batch_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.batch_metadata, f, indent=2)
    
    def run_single_simulation(self, sim_number: int) -> Dict[str, Any]:
        """Run a single simulation instance"""
        sim_id = f"simulation_{sim_number:03d}"
        sim_dir = self.batch_dir / sim_id
        
        start_time = time.time()
        self.logger.info(f"Starting {sim_id}")
        
        # Prepare command
        cmd = [
            sys.executable,  # Use the same Python interpreter
            "main.py",
            "--config", str(self.config_path),
            "--output-dir", str(self.batch_dir),
            "--sim-id", sim_id,  # Pass the unique simulation ID
            "--log-level", self.log_level
        ]
        
        # Run simulation as subprocess
        try:
            # Set PYTHONPATH to ensure imports work
            env = os.environ.copy()
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{os.getcwd()}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = os.getcwd()
            
            # Run subprocess with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                cwd=str(Path(__file__).parent)  # Run from simulation directory
            )
            
            # Collect output while showing progress
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    line = line.rstrip()
                    output_lines.append(line)
                    # Show simulation progress (filter for important messages)
                    if any(keyword in line for keyword in ['Round', 'Starting', 'complete', 'Final', 'ERROR', 'Agent', 'taking turn']):
                        self.logger.info(f"  [{sim_id}] {line}")
            
            result_code = process.wait()
            output_text = '\n'.join(output_lines)
            
            duration = time.time() - start_time
            
            if result_code == 0:
                # Success - the directory should now be created with the exact sim_id
                # Load results
                results_file = sim_dir / "results.yaml"
                if results_file.exists():
                    with open(results_file, 'r') as f:
                        results = yaml.safe_load(f)
                else:
                    results = None
                
                self.logger.info(f"Completed {sim_id} in {duration:.2f}s")
                
                return {
                    "id": sim_id,
                    "status": "completed",
                    "duration": duration,
                    "started_at": datetime.fromtimestamp(start_time).isoformat(),
                    "completed_at": datetime.now().isoformat(),
                    "results_summary": {
                        "total_tasks": results.get('total_tasks_completed', 0) if results else 0,
                        "total_messages": results.get('total_messages', 0) if results else 0,
                        "winner": list(results.get('final_revenue_board', {}).keys())[0] if results and results.get('final_revenue_board') else None
                    }
                }
                    
            else:
                # Failure
                self.logger.error(f"Failed {sim_id}: Exit code {result_code}")
                self.logger.error(f"Last output: {output_text[-500:]}")
                return {
                    "id": sim_id,
                    "status": "failed",
                    "duration": duration,
                    "started_at": datetime.fromtimestamp(start_time).isoformat(),
                    "error": output_text[-1000:]  # Last 1000 chars of output
                }
                
        except Exception as e:
            self.logger.error(f"Exception running {sim_id}: {str(e)}")
            return {
                "id": sim_id,
                "status": "error",
                "duration": time.time() - start_time,
                "started_at": datetime.fromtimestamp(start_time).isoformat(),
                "error": str(e)
            }
    
    def run_batch_sequential(self):
        """Run simulations sequentially"""
        self.logger.info(f"Running {self.num_simulations} simulations sequentially")
        
        for i in range(1, self.num_simulations + 1):
            # Update progress
            self.logger.info(f"Progress: {i}/{self.num_simulations} ({i/self.num_simulations*100:.1f}%)")
            
            # Run simulation
            sim_result = self.run_single_simulation(i)
            
            # Update metadata
            self.batch_metadata["simulations"].append(sim_result)
            self.save_batch_metadata()
            
            # Print summary
            if sim_result["status"] == "completed":
                self.logger.info(f"✓ {sim_result['id']} completed successfully")
            else:
                self.logger.warning(f"✗ {sim_result['id']} failed")
    
    def run_batch_parallel(self):
        """Run simulations in parallel"""
        self.logger.info(f"Running {self.num_simulations} simulations in parallel (max {self.max_workers} workers)")
        
        completed = 0
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all simulations
            future_to_sim = {
                executor.submit(self.run_single_simulation, i): i 
                for i in range(1, self.num_simulations + 1)
            }
            
            # Process completed simulations
            for future in as_completed(future_to_sim):
                sim_number = future_to_sim[future]
                try:
                    sim_result = future.result()
                    completed += 1
                    
                    # Update metadata
                    self.batch_metadata["simulations"].append(sim_result)
                    self.save_batch_metadata()
                    
                    # Log progress
                    status_symbol = "✓" if sim_result["status"] == "completed" else "✗"
                    self.logger.info(f"{status_symbol} {sim_result['id']} - Progress: {completed}/{self.num_simulations} ({completed/self.num_simulations*100:.1f}%)")
                    
                except Exception as e:
                    self.logger.error(f"Exception processing simulation {sim_number}: {e}")
                    completed += 1
    
    def generate_aggregate_summary(self):
        """Generate summary statistics after all simulations complete"""
        self.logger.info("Generating aggregate summary...")
        
        # Count successes and failures
        completed = sum(1 for s in self.batch_metadata["simulations"] if s["status"] == "completed")
        failed = sum(1 for s in self.batch_metadata["simulations"] if s["status"] != "completed")
        
        # Collect all results and analysis
        all_results = []
        all_analyses = []
        agent_revenues = {}
        task_counts = []
        message_counts = []
        gini_coefficients = []
        communication_efficiencies = []
        negotiation_cycle_times = []
        zero_revenue_counts = []
        
        for sim in self.batch_metadata["simulations"]:
            if sim["status"] == "completed":
                sim_dir = self.batch_dir / sim["id"]
                results_file = sim_dir / "results.yaml"
                analysis_file = sim_dir / "analysis_results.json"
                
                if results_file.exists():
                    with open(results_file, 'r') as f:
                        results = yaml.safe_load(f)
                        all_results.append(results)
                        
                        # Collect metrics
                        task_counts.append(results.get('total_tasks_completed', 0))
                        message_counts.append(results.get('total_messages', 0))
                        
                        # Collect agent revenues
                        for agent, revenue in results.get('final_revenue_board', {}).items():
                            if agent not in agent_revenues:
                                agent_revenues[agent] = []
                            agent_revenues[agent].append(revenue)
                
                # Collect analysis metrics if available
                if analysis_file.exists():
                    with open(analysis_file, 'r') as f:
                        analysis = json.load(f)
                        all_analyses.append(analysis)
                        
                        metrics = analysis.get('metrics', {})
                        
                        # Collect Gini coefficients
                        gini = metrics.get('revenue_distribution', {}).get('gini_coefficient')
                        if gini is not None:
                            gini_coefficients.append(gini)
                        
                        # Collect communication efficiency
                        comm_eff = metrics.get('communication_efficiency', {}).get('messages_per_completed_task')
                        if comm_eff and comm_eff != float('inf'):
                            communication_efficiencies.append(comm_eff)
                        
                        # Collect negotiation cycle times
                        cycle_time = metrics.get('negotiation_cycle_time', {}).get('average_negotiation_cycle_time')
                        if cycle_time is not None:
                            negotiation_cycle_times.append(cycle_time)
                        
                        # Collect zero revenue counts
                        zero_count = metrics.get('agents_with_zero_revenue', {}).get('count', 0)
                        zero_revenue_counts.append(zero_count)
        
        # Calculate summary statistics
        summary = {
            "batch_id": self.batch_metadata["batch_id"],
            "timestamp": datetime.now().isoformat(),
            "num_simulations": self.num_simulations,
            "completed_simulations": completed,
            "failed_simulations": failed,
            "success_rate": completed / self.num_simulations if self.num_simulations > 0 else 0
        }
        
        if all_results:
            import statistics
            
            # Task statistics
            if task_counts:
                summary["task_statistics"] = {
                    "mean": statistics.mean(task_counts),
                    "std": statistics.stdev(task_counts) if len(task_counts) > 1 else 0,
                    "min": min(task_counts),
                    "max": max(task_counts)
                }
            
            # Message statistics
            if message_counts:
                summary["message_statistics"] = {
                    "mean": statistics.mean(message_counts),
                    "std": statistics.stdev(message_counts) if len(message_counts) > 1 else 0,
                    "min": min(message_counts),
                    "max": max(message_counts)
                }
            
            # Agent performance summary
            summary["agent_performance"] = {}
            for agent, revenues in agent_revenues.items():
                if revenues:
                    summary["agent_performance"][agent] = {
                        "mean_revenue": statistics.mean(revenues),
                        "std": statistics.stdev(revenues) if len(revenues) > 1 else 0,
                        "min": min(revenues),
                        "max": max(revenues),
                        "appearances": len(revenues)
                    }
            
            # Winner distribution
            winner_counts = {}
            for result in all_results:
                revenue_board = result.get('final_revenue_board', {})
                if revenue_board:
                    winner = max(revenue_board.items(), key=lambda x: x[1])[0]
                    winner_counts[winner] = winner_counts.get(winner, 0) + 1
            
            summary["winner_distribution"] = winner_counts
            
            # Analysis metrics aggregation
            if gini_coefficients:
                summary["gini_coefficient_statistics"] = {
                    "mean": statistics.mean(gini_coefficients),
                    "std": statistics.stdev(gini_coefficients) if len(gini_coefficients) > 1 else 0,
                    "min": min(gini_coefficients),
                    "max": max(gini_coefficients)
                }
            
            if communication_efficiencies:
                summary["communication_efficiency_statistics"] = {
                    "mean": statistics.mean(communication_efficiencies),
                    "std": statistics.stdev(communication_efficiencies) if len(communication_efficiencies) > 1 else 0,
                    "min": min(communication_efficiencies),
                    "max": max(communication_efficiencies)
                }
            
            if negotiation_cycle_times:
                summary["negotiation_cycle_time_statistics"] = {
                    "mean": statistics.mean(negotiation_cycle_times),
                    "std": statistics.stdev(negotiation_cycle_times) if len(negotiation_cycle_times) > 1 else 0,
                    "min": min(negotiation_cycle_times),
                    "max": max(negotiation_cycle_times)
                }
            
            if zero_revenue_counts:
                summary["zero_revenue_agent_statistics"] = {
                    "mean": statistics.mean(zero_revenue_counts),
                    "std": statistics.stdev(zero_revenue_counts) if len(zero_revenue_counts) > 1 else 0,
                    "min": min(zero_revenue_counts),
                    "max": max(zero_revenue_counts)
                }
        
        # Save summary
        summary_path = self.batch_dir / "aggregate_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Aggregate summary saved to {summary_path}")
        
        return summary
    
    def run(self):
        """Run the batch simulation"""
        self.logger.info(f"Starting batch simulation: {self.batch_metadata['batch_id']}")
        self.logger.info(f"Configuration: {self.config_path}")
        self.logger.info(f"Number of simulations: {self.num_simulations}")
        self.logger.info(f"Output directory: {self.batch_dir}")
        
        # Save initial metadata
        self.save_batch_metadata()
        
        # Run simulations
        start_time = time.time()
        
        if self.parallel:
            self.run_batch_parallel()
        else:
            self.run_batch_sequential()
        
        # Update completion time
        self.batch_metadata["completed_at"] = datetime.now().isoformat()
        self.batch_metadata["total_duration"] = time.time() - start_time
        self.batch_metadata["status"] = "completed"
        self.save_batch_metadata()
        
        # Generate aggregate summary
        summary = self.generate_aggregate_summary()
        
        # Print final summary
        self.print_summary(summary)
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print a nice summary of the batch run"""
        print("\n" + "="*60)
        print(f"BATCH SIMULATION COMPLETE: {summary['batch_id']}")
        print("="*60)
        print(f"Total simulations: {summary['num_simulations']}")
        print(f"Successful: {summary['completed_simulations']} ({summary['success_rate']*100:.1f}%)")
        print(f"Failed: {summary['failed_simulations']}")
        
        if 'task_statistics' in summary:
            print(f"\nTask Completion Statistics:")
            print(f"  Mean: {summary['task_statistics']['mean']:.1f}")
            print(f"  Std Dev: {summary['task_statistics']['std']:.1f}")
            print(f"  Range: {summary['task_statistics']['min']} - {summary['task_statistics']['max']}")
        
        if 'winner_distribution' in summary:
            print(f"\nWinner Distribution:")
            for agent, wins in sorted(summary['winner_distribution'].items(), 
                                     key=lambda x: x[1], reverse=True):
                win_rate = wins / summary['completed_simulations'] * 100
                print(f"  {agent}: {wins} wins ({win_rate:.1f}%)")
        
        if 'gini_coefficient_statistics' in summary:
            print(f"\nRevenue Distribution (Gini Coefficient):")
            print(f"  Mean: {summary['gini_coefficient_statistics']['mean']:.3f}")
            print(f"  Range: {summary['gini_coefficient_statistics']['min']:.3f} - {summary['gini_coefficient_statistics']['max']:.3f}")
        
        if 'communication_efficiency_statistics' in summary:
            print(f"\nCommunication Efficiency (Messages/Task):")
            print(f"  Mean: {summary['communication_efficiency_statistics']['mean']:.1f}")
            print(f"  Range: {summary['communication_efficiency_statistics']['min']:.1f} - {summary['communication_efficiency_statistics']['max']:.1f}")
        
        print(f"\nResults saved to: {self.batch_dir}")
        print(f"View in dashboard: http://localhost:8080/batch")
        print("="*60 + "\n")


def main():
    """Main entry point for batch runner"""
    parser = argparse.ArgumentParser(
        description='Run multiple information asymmetry simulations in batch mode'
    )
    parser.add_argument(
        '--num-sims', '-n',
        type=int,
        default=10,
        help='Number of simulations to run (default: 10)'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='logs',
        help='Base directory for output (default: logs)'
    )
    parser.add_argument(
        '--log-level', '-l',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Run simulations in parallel'
    )
    parser.add_argument(
        '--max-workers', '-w',
        type=int,
        default=None,
        help='Maximum number of parallel workers (default: number of CPUs)'
    )
    
    args = parser.parse_args()
    
    # Create and run batch
    try:
        runner = BatchSimulationRunner(
            config_path=args.config,
            num_simulations=args.num_sims,
            output_dir=args.output_dir,
            log_level=args.log_level,
            parallel=args.parallel,
            max_workers=args.max_workers
        )
        
        summary = runner.run()
        
        # Exit with appropriate code
        if summary['failed_simulations'] == 0:
            sys.exit(0)
        elif summary['completed_simulations'] > 0:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # Complete failure
            
    except Exception as e:
        logging.error(f"Batch run failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
"""
Main Analysis Pipeline Orchestrator

Coordinates the entire analysis workflow from data loading through
visualization generation.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd

from .core import DataLoader, EventProcessor
from .analyzers import (
    CommunicationAnalyzer,
    InformationFlowAnalyzer,
    TaskPerformanceAnalyzer,
    StrategyAnalyzer
)
from .visualizers import CoreVisualizer
from .visualizers.cooperation_score_tracker import CooperationScoreTracker


class AnalysisPipeline:
    """Orchestrates the complete analysis pipeline"""
    
    def __init__(
        self, 
        simulation_id: str,
        config_path: Optional[str] = None,
        output_dir: Optional[str] = None
    ):
        """
        Initialize the analysis pipeline.
        
        Args:
            simulation_id: ID of the simulation to analyze
            config_path: Path to configuration file
            output_dir: Directory for analysis outputs
        """
        self.simulation_id = simulation_id
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set up output directory
        base_dir = Path(f"logs/{simulation_id}")
        self.output_dir = Path(output_dir) if output_dir else base_dir / "analysis_v2"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize components
        self.data_loader = None
        self.event_processor = None
        self.analyzers = {}
        self.results = {}
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'cache_enabled': True,
            'analyzers': {
                'communication': True,
                'information_flow': True,
                'task_performance': True,
                'strategy': True
            },
            'visualizations': {
                'create_all': True,
                'style': 'seaborn-v0_8-darkgrid',
                'dpi': 300
            },
            'output': {
                'formats': ['json', 'txt'],
                'include_raw_data': False
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                default_config.update(user_config)
                
        return default_config
        
    def run(self) -> Dict[str, Any]:
        """
        Run the complete analysis pipeline.
        
        Returns:
            Dictionary containing all analysis results
        """
        print(f"\n{'='*60}")
        print(f"Information Asymmetry Simulation Analysis v2.0")
        print(f"{'='*60}")
        print(f"Simulation ID: {self.simulation_id}")
        print(f"Output Directory: {self.output_dir}")
        print(f"{'='*60}\n")
        
        # Step 1: Load and process data
        print("Step 1: Loading and processing data...")
        self._load_data()
        
        # Step 2: Run analyzers
        print("\nStep 2: Running analyzers...")
        self._run_analyzers()
        
        # Step 3: Generate visualizations
        print("\nStep 3: Generating visualizations...")
        self._generate_visualizations()
        
        # Step 4: Save results
        print("\nStep 4: Saving results...")
        self._save_results()
        
        # Step 5: Generate summary report
        print("\nStep 5: Generating summary report...")
        self._generate_report()
        
        print(f"\n{'='*60}")
        print("Analysis complete!")
        print(f"Results saved to: {self.output_dir}")
        print(f"{'='*60}\n")
        
        return self.results
        
    def _load_data(self):
        """Load and process simulation data"""
        # Initialize data loader
        self.data_loader = DataLoader(
            self.simulation_id,
            cache_dir=self.output_dir / "cache" if self.config['cache_enabled'] else None
        )
        
        # Load events
        events_df = self.data_loader.get_events_df()
        print(f"  - Loaded {len(events_df)} events")
        
        # Initialize event processor
        self.event_processor = EventProcessor(events_df)
        
        # Extract basic information
        print(f"  - Found {len(self.event_processor.agents)} agents")
        print(f"  - Found {len(self.event_processor.rounds)} rounds")
        
        # Check if we have enough data
        if len(self.event_processor.agents) == 0 or len(self.event_processor.rounds) == 0:
            raise ValueError("Insufficient data: No agents or rounds found in simulation")
        
        # Add processed data to results
        self.results['simulation_config'] = self.data_loader.get_simulation_config()
        self.results['simulation_results'] = self.data_loader.get_simulation_results()
        self.results['agent_summary'] = self.event_processor.get_agent_summary()
        self.results['round_summary'] = self.event_processor.get_round_summary()
        
        # Store key data for visualizations
        self.results['messages'] = self.event_processor.get_messages()
        self.results['information_exchanges'] = self.event_processor.get_information_exchanges()
        self.results['task_completions'] = self.event_processor.get_task_completions()
        
    def _run_analyzers(self):
        """Run all configured analyzers"""
        analyzer_classes = {
            'communication': CommunicationAnalyzer,
            'information_flow': InformationFlowAnalyzer,
            'task_performance': TaskPerformanceAnalyzer,
            'strategy': StrategyAnalyzer
        }
        
        for name, enabled in self.config['analyzers'].items():
            if enabled and name in analyzer_classes:
                print(f"  - Running {name} analyzer...")
                
                analyzer = analyzer_classes[name](self.event_processor)
                self.analyzers[name] = analyzer
                
                # Run analysis and store results
                analysis_results = analyzer.get_results()
                self.results[name] = analysis_results
                
                # Print key metrics
                metrics = analyzer.get_metrics()
                if metrics:
                    print(f"    Key metrics:")
                    for metric, value in list(metrics.items())[:3]:  # Show top 3
                        if isinstance(value, float):
                            print(f"      • {metric}: {value:.3f}")
                        else:
                            print(f"      • {metric}: {value}")
                            
    def _generate_visualizations(self):
        """Generate all visualizations"""
        if not self.config['visualizations']['create_all']:
            print("  - Visualizations disabled in config")
            return
            
        # Create visualization directory
        viz_dir = self.output_dir / "visualizations"
        viz_dir.mkdir(exist_ok=True)
        
        # Initialize visualizer with combined results
        visualizer = CoreVisualizer(self.results, viz_dir)
        
        # Create all core visualizations
        visualizer.create_all_visualizations()
        
        # Create cooperation-points progression visualization
        try:
            print("  - Creating cooperation-points progression...")
            coop_tracker = CooperationScoreTracker(self.simulation_id, "logs")
            coop_tracker.parse_logs()
            coop_tracker.create_visualization(viz_dir)
            print("    ✓ Cooperation-points progression created")
        except Exception as e:
            print(f"    ⚠️  Could not create cooperation visualization: {e}")
        
    def _save_results(self):
        """Save analysis results in configured formats"""
        formats = self.config['output']['formats']
        
        if 'json' in formats:
            # Save detailed results as JSON
            json_path = self.output_dir / f"analysis_results_{self.timestamp}.json"
            
            # Prepare JSON-serializable results
            json_results = self._prepare_json_results()
            
            with open(json_path, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)
            print(f"  - Saved JSON results to: {json_path.name}")
            
        if 'csv' in formats:
            # Save key dataframes as CSV
            csv_dir = self.output_dir / "csv"
            csv_dir.mkdir(exist_ok=True)
            
            # Save agent summary
            if 'agent_summary' in self.results:
                self.results['agent_summary'].to_csv(
                    csv_dir / "agent_summary.csv", index=False
                )
                
            # Save round summary
            if 'round_summary' in self.results:
                self.results['round_summary'].to_csv(
                    csv_dir / "round_summary.csv", index=False
                )
                
            print(f"  - Saved CSV files to: {csv_dir}")
            
    def _generate_report(self):
        """Generate comprehensive text report"""
        report_path = self.output_dir / f"analysis_report_{self.timestamp}.txt"
        
        with open(report_path, 'w') as f:
            # Header
            f.write("="*80 + "\n")
            f.write("INFORMATION ASYMMETRY SIMULATION ANALYSIS REPORT\n")
            f.write("="*80 + "\n\n")
            
            # Metadata
            f.write(f"Simulation ID: {self.simulation_id}\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Analysis Version: 2.0.0\n")
            f.write("\n")
            
            # Simulation overview
            f.write("SIMULATION OVERVIEW\n")
            f.write("-"*80 + "\n")
            
            config = self.results.get('simulation_config', {})
            f.write(f"Agents: {config.get('simulation', {}).get('agents', 'N/A')}\n")
            f.write(f"Rounds: {config.get('simulation', {}).get('rounds', 'N/A')}\n")
            f.write(f"Total Information Pieces: {config.get('information', {}).get('total_pieces', 'N/A')}\n")
            f.write("\n")
            
            # Key results
            if 'simulation_results' in self.results:
                sim_results = self.results['simulation_results']
                if 'final_rankings' in sim_results:
                    f.write("FINAL RANKINGS\n")
                    f.write("-"*80 + "\n")
                    for i, (agent, score) in enumerate(sim_results['final_rankings'][:5], 1):
                        f.write(f"{i}. {agent}: {score} points\n")
                    f.write("\n")
                    
            # Analyzer summaries
            for name, analyzer in self.analyzers.items():
                summary = analyzer.get_summary()
                f.write(summary)
                f.write("\n\n")
                
            # Key insights
            f.write("KEY INSIGHTS\n")
            f.write("-"*80 + "\n")
            insights = self._generate_insights()
            for insight in insights:
                f.write(f"• {insight}\n")
                
        print(f"  - Saved report to: {report_path.name}")
        
    def _prepare_json_results(self) -> Dict[str, Any]:
        """Prepare results for JSON serialization"""
        json_results = {
            'metadata': {
                'simulation_id': self.simulation_id,
                'analysis_timestamp': self.timestamp,
                'analysis_version': '2.0.0'
            }
        }
        
        # Add analyzer results
        for name in self.analyzers:
            if name in self.results:
                analyzer_results = self.results[name].copy()
                
                # Convert DataFrames to dictionaries
                for key, value in analyzer_results.items():
                    if isinstance(value, pd.DataFrame):
                        analyzer_results[key] = value.to_dict('records')
                        
                json_results[name] = analyzer_results
                
        # Add summaries
        if not self.config['output']['include_raw_data']:
            # Only include processed summaries, not raw data
            for key in ['messages', 'information_exchanges', 'task_completions']:
                json_results.pop(key, None)
                
        return json_results
        
    def _generate_insights(self) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        
        # Communication insights
        if 'communication' in self.results:
            comm = self.results['communication']
            metrics = comm['communication_metrics']
            
            if metrics['broadcast_ratio'] > 0.3:
                insights.append(
                    f"High broadcast usage ({metrics['broadcast_ratio']:.1%}) indicates "
                    "public information sharing strategy"
                )
                
        # Information flow insights
        if 'information_flow' in self.results:
            info = self.results['information_flow']
            asymmetry = info['asymmetry_metrics']
            
            if asymmetry['gini_coefficient'] > 0.5:
                insights.append(
                    f"High information inequality (Gini: {asymmetry['gini_coefficient']:.2f}) "
                    "suggests emergence of information monopolies"
                )
                
        # Task performance insights
        if 'task_performance' in self.results:
            task = self.results['task_performance']
            perf = task['performance_metrics']
            
            if perf['competitive_advantage'] > 0.5:
                insights.append(
                    "Strong correlation between early action and success indicates "
                    "first-mover advantages are significant"
                )
                
        # Strategy insights
        if 'strategy' in self.results:
            strategy = self.results['strategy']
            
            if strategy['deception_analysis']['deception_prevalence'] > 0.2:
                insights.append(
                    f"Deception present in {strategy['deception_analysis']['deception_prevalence']:.1%} "
                    "of exchanges, indicating trust challenges"
                )
                
        return insights
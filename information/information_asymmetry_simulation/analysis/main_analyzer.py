"""
Main analyzer script for comprehensive simulation analysis.

This script coordinates all analysis modules and generates comprehensive reports.
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import all analyzer modules
from .foundational_metrics import FoundationalMetricsAnalyzer
from .reciprocity_analyzer import ReciprocityAnalyzer
from .deception_analyzer import DeceptionAnalyzer
from .negotiation_analyzer import NegotiationAnalyzer


class ComprehensiveAnalyzer:
    """Main analyzer that coordinates all analysis modules."""
    
    def __init__(self, simulation_id: str):
        """
        Initialize the comprehensive analyzer.
        
        Args:
            simulation_id: The ID of the simulation to analyze
        """
        self.simulation_id = simulation_id
        self.log_dir = Path(f"logs/{simulation_id}")
        self.log_file = self.log_dir / "simulation_log.jsonl"
        
        # Check if log file exists
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {self.log_file}")
            
        # Load log data
        self.log_data = self._load_log_data()
        
        # Initialize all analyzers
        self.foundational_analyzer = FoundationalMetricsAnalyzer(self.log_data)
        self.reciprocity_analyzer = ReciprocityAnalyzer(self.log_data)
        self.deception_analyzer = DeceptionAnalyzer(self.log_data)
        self.negotiation_analyzer = NegotiationAnalyzer(self.log_data)
        
    def _load_log_data(self) -> List[Dict[str, Any]]:
        """Load the simulation log data."""
        log_data = []
        with open(self.log_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        log_data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse line: {e}")
                        continue
        return log_data
        
    def analyze_all(self) -> Dict[str, Any]:
        """Run all analyses and return combined results."""
        print(f"Analyzing simulation: {self.simulation_id}")
        print("-" * 50)
        
        results = {
            'simulation_id': self.simulation_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'foundational_metrics': None,
            'reciprocity_analysis': None,
            'deception_analysis': None,
            'negotiation_analysis': None
        }
        
        # Run foundational metrics analysis
        print("Running foundational metrics analysis...")
        try:
            results['foundational_metrics'] = self.foundational_analyzer.analyze()
            print("✓ Foundational metrics complete")
        except Exception as e:
            print(f"✗ Foundational metrics failed: {e}")
            
        # Run reciprocity analysis
        print("Running reciprocity analysis...")
        try:
            results['reciprocity_analysis'] = self.reciprocity_analyzer.analyze()
            print("✓ Reciprocity analysis complete")
        except Exception as e:
            print(f"✗ Reciprocity analysis failed: {e}")
            
        # Run deception analysis
        print("Running deception analysis...")
        try:
            results['deception_analysis'] = self.deception_analyzer.analyze()
            print("✓ Deception analysis complete")
        except Exception as e:
            print(f"✗ Deception analysis failed: {e}")
            
        # Run negotiation analysis
        print("Running negotiation analysis...")
        try:
            results['negotiation_analysis'] = self.negotiation_analyzer.analyze()
            print("✓ Negotiation analysis complete")
        except Exception as e:
            print(f"✗ Negotiation analysis failed: {e}")
            
        print("-" * 50)
        return results
        
    def generate_json_report(self, results: Dict[str, Any], output_file: Path):
        """Save analysis results as JSON."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"JSON report saved to: {output_file}")
        
    def generate_text_report(self, results: Dict[str, Any], output_file: Path):
        """Generate a comprehensive human-readable report."""
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("COMPREHENSIVE SIMULATION ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Simulation ID: {self.simulation_id}")
        report_lines.append(f"Analysis Date: {results['analysis_timestamp']}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Foundational metrics summary
        if results['foundational_metrics']:
            report_lines.append(self.foundational_analyzer.get_summary())
            report_lines.append("\n" + "=" * 80 + "\n")
            
        # Reciprocity analysis summary
        if results['reciprocity_analysis']:
            report_lines.append(self.reciprocity_analyzer.get_summary())
            report_lines.append("\n" + "=" * 80 + "\n")
            
        # Deception analysis summary
        if results['deception_analysis']:
            report_lines.append(self.deception_analyzer.get_summary())
            report_lines.append("\n" + "=" * 80 + "\n")
            
        # Negotiation analysis summary
        if results['negotiation_analysis']:
            report_lines.append(self.negotiation_analyzer.get_summary())
            report_lines.append("\n" + "=" * 80 + "\n")
            
        # Key insights section
        report_lines.append("KEY INSIGHTS AND PATTERNS")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Extract key insights
        insights = self._extract_key_insights(results)
        for category, category_insights in insights.items():
            report_lines.append(f"{category}:")
            for insight in category_insights:
                report_lines.append(f"  • {insight}")
            report_lines.append("")
            
        # Write report
        report_content = "\n".join(report_lines)
        with open(output_file, 'w') as f:
            f.write(report_content)
        print(f"Text report saved to: {output_file}")
        
    def _extract_key_insights(self, results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract key insights from the analysis results."""
        insights = {
            'Communication Patterns': [],
            'Cooperation and Reciprocity': [],
            'Strategic Behavior': [],
            'Negotiation Dynamics': []
        }
        
        # Communication insights
        if results['foundational_metrics']:
            fm = results['foundational_metrics']
            msg_metrics = fm.get('message_metrics', {})
            
            total_messages = msg_metrics.get('total_messages', 0)
            if total_messages > 0:
                broadcast_pct = fm.get('broadcast_metrics', {}).get('broadcast_percentage', 0)
                insights['Communication Patterns'].append(
                    f"{broadcast_pct:.1%} of messages were broadcasts, suggesting "
                    f"{'high' if broadcast_pct > 0.5 else 'low'} public information sharing"
                )
                
        # Reciprocity insights
        if results['reciprocity_analysis']:
            ra = results['reciprocity_analysis']
            fulfill_rate = ra.get('fulfillment_metrics', {}).get('fulfillment_rate', 0)
            
            if fulfill_rate > 0.7:
                insights['Cooperation and Reciprocity'].append(
                    f"High request fulfillment rate ({fulfill_rate:.1%}) indicates cooperative environment"
                )
            elif fulfill_rate < 0.3:
                insights['Cooperation and Reciprocity'].append(
                    f"Low request fulfillment rate ({fulfill_rate:.1%}) suggests competitive dynamics"
                )
                
        # Deception insights
        if results['deception_analysis']:
            da = results['deception_analysis']
            deception_rate = da.get('deception_metrics', {}).get('deception_rate', 0)
            trend = da.get('temporal_analysis', {}).get('deception_trend', 'stable')
            
            if deception_rate > 0.2:
                insights['Strategic Behavior'].append(
                    f"Significant deceptive behavior detected ({deception_rate:.1%} of private thoughts)"
                )
            
            if trend == 'increasing':
                insights['Strategic Behavior'].append(
                    "Deceptive behavior increased over time, suggesting escalating competition"
                )
                
        # Negotiation insights
        if results['negotiation_analysis']:
            na = results['negotiation_analysis']
            success_rate = na.get('negotiation_outcomes', {}).get('success_rate', 0)
            complexity_trend = na.get('complexity_analysis', {}).get('complexity_trend', 'stable')
            
            if success_rate > 0.6:
                insights['Negotiation Dynamics'].append(
                    f"High negotiation success rate ({success_rate:.1%}) indicates effective dealmaking"
                )
                
            if complexity_trend == 'increasing':
                insights['Negotiation Dynamics'].append(
                    "Negotiations became more complex over time, suggesting sophisticated strategies"
                )
                
        return insights
        
    def save_reports(self, output_dir: Path = None):
        """Save all analysis reports."""
        if output_dir is None:
            output_dir = self.log_dir / "analysis"
            
        output_dir.mkdir(exist_ok=True)
        
        # Run all analyses
        results = self.analyze_all()
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_file = output_dir / f"analysis_results_{timestamp}.json"
        self.generate_json_report(results, json_file)
        
        # Save text report
        text_file = output_dir / f"analysis_report_{timestamp}.txt"
        self.generate_text_report(results, text_file)
        
        # Save individual analyzer reports if needed
        self._save_detailed_reports(results, output_dir, timestamp)
        
        # Generate visualizations
        print("\nGenerating visualizations...")
        try:
            # Generate enhanced visualizations
            from .enhanced_visualizer import create_enhanced_visualizations
            create_enhanced_visualizations(self.log_data, output_dir)
            print("✓ Enhanced visualizations complete")
        except Exception as e:
            print(f"✗ Visualization generation failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\nAll reports saved to: {output_dir}")
        
    def _save_detailed_reports(self, results: Dict[str, Any], 
                              output_dir: Path, timestamp: str):
        """Save detailed reports from individual analyzers."""
        # Save detailed negotiation chains
        if results['negotiation_analysis']:
            chains = results['negotiation_analysis'].get('detailed_chains', [])
            if chains:
                chains_file = output_dir / f"negotiation_chains_{timestamp}.json"
                with open(chains_file, 'w') as f:
                    json.dump(chains, f, indent=2)
                    
        # Save detailed deception events
        if results['deception_analysis']:
            events = results['deception_analysis'].get('detailed_events', [])
            if events:
                events_file = output_dir / f"deception_events_{timestamp}.json"
                with open(events_file, 'w') as f:
                    json.dump(events, f, indent=2)
                    
        # Save detailed reciprocity requests
        if results['reciprocity_analysis']:
            requests = results['reciprocity_analysis'].get('detailed_requests', [])
            if requests:
                requests_file = output_dir / f"reciprocity_requests_{timestamp}.json"
                with open(requests_file, 'w') as f:
                    json.dump(requests, f, indent=2)


def main():
    """Main entry point for the analyzer."""
    parser = argparse.ArgumentParser(
        description='Comprehensive analysis of information asymmetry simulation logs'
    )
    parser.add_argument(
        'simulation_id',
        help='The simulation ID to analyze (e.g., simulation_20250714_103613)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        help='Output directory for reports (default: logs/[simulation_id]/analysis)'
    )
    parser.add_argument(
        '--json-only',
        action='store_true',
        help='Only generate JSON report (skip text report)'
    )
    parser.add_argument(
        '--text-only',
        action='store_true',
        help='Only generate text report (skip JSON report)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create analyzer
        analyzer = ComprehensiveAnalyzer(args.simulation_id)
        
        # Determine output directory
        output_dir = args.output_dir
        if output_dir is None:
            output_dir = analyzer.log_dir / "analysis"
            
        # Run analysis and save reports
        if args.json_only or args.text_only:
            results = analyzer.analyze_all()
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if args.json_only:
                json_file = output_dir / f"analysis_results_{timestamp}.json"
                analyzer.generate_json_report(results, json_file)
            else:  # text_only
                text_file = output_dir / f"analysis_report_{timestamp}.txt"
                analyzer.generate_text_report(results, text_file)
            
            # Still generate visualizations even with specific report types
            print("\nGenerating visualizations...")
            try:
                # Generate enhanced visualizations
                from .enhanced_visualizer import create_enhanced_visualizations
                create_enhanced_visualizations(analyzer.log_data, output_dir)
                print("✓ Enhanced visualizations complete")
            except Exception as e:
                print(f"✗ Visualization generation failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            # Generate all reports
            analyzer.save_reports(output_dir)
            
        print("\nAnalysis complete!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"Make sure the simulation ID is correct and the log file exists.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
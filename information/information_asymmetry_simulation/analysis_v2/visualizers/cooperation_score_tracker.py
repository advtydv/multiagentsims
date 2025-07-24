"""
Cooperation Score and Points Progression Visualizer

Tracks and visualizes how agents' cooperation scores (from peer assessments)
and point scores evolve throughout the simulation.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-darkgrid')

class CooperationScoreTracker:
    """Tracks and visualizes cooperation scores and points progression"""
    
    def __init__(self, simulation_id: str, logs_dir: str = "logs"):
        self.simulation_id = simulation_id
        self.logs_dir = Path(logs_dir)
        self.log_path = self.logs_dir / f"simulation_{simulation_id}" / "simulation_log.jsonl"
        
        # Data containers
        self.cooperation_scores = defaultdict(lambda: defaultdict(list))  # {agent: {round: [scores]}}
        self.self_assessments = defaultdict(dict)  # {agent: {round: score}}
        self.point_scores = defaultdict(dict)  # {agent: {round: cumulative_score}}
        self.rounds = set()
        
    def parse_logs(self):
        """Parse the simulation logs to extract cooperation scores and points"""
        if not self.log_path.exists():
            raise FileNotFoundError(f"Log file not found: {self.log_path}")
            
        current_scores = defaultdict(int)  # Track cumulative scores
        
        with open(self.log_path, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    event_type = event.get('event_type')
                    
                    if event_type == 'agent_report':
                        # Extract cooperation scores from reports
                        self._process_agent_report(event)
                        
                    elif event_type == 'task_completion':
                        # Track point accumulation
                        self._process_task_completion(event, current_scores)
                        
                    elif event_type == 'simulation_start':
                        # Initialize agents
                        config = event['data']['config']
                        num_agents = config['simulation']['agents']
                        for i in range(1, num_agents + 1):
                            agent_id = f"agent_{i}"
                            current_scores[agent_id] = 0
                            
                except json.JSONDecodeError:
                    continue
                    
    def _process_agent_report(self, event: Dict[str, Any]):
        """Process agent report to extract cooperation scores"""
        data = event.get('data', {})
        round_num = data.get('round')
        agent_id = data.get('agent_id')
        report = data.get('report', {})
        
        if not round_num or not agent_id:
            return
            
        self.rounds.add(round_num)
        
        # Extract cooperation scores
        coop_scores = report.get('cooperation_scores', {})
        
        # Process peer assessments
        for assessed_agent, score in coop_scores.items():
            if assessed_agent == 'self':
                # Self assessment
                self.self_assessments[agent_id][round_num] = score
            else:
                # Peer assessment - store who received this score
                self.cooperation_scores[assessed_agent][round_num].append(score)
                
    def _process_task_completion(self, event: Dict[str, Any], current_scores: Dict[str, int]):
        """Process task completion to track points"""
        data = event.get('data', {})
        round_num = data.get('round')
        agent_id = data.get('agent_id')
        success = data.get('success', False)
        
        if not round_num or not agent_id:
            return
            
        if success:
            # Extract points from the result
            result = data.get('result', {})
            points = result.get('points_awarded', 0)
            current_scores[agent_id] += points
            
        # Record current cumulative score for this round
        self.point_scores[agent_id][round_num] = current_scores[agent_id]
        
    def calculate_aggregate_cooperation_scores(self) -> Dict[str, Dict[int, float]]:
        """Calculate mean cooperation scores for each agent per round"""
        aggregate_scores = defaultdict(dict)
        
        for agent, round_scores in self.cooperation_scores.items():
            for round_num, scores in round_scores.items():
                if scores:
                    # Calculate mean of peer assessments
                    aggregate_scores[agent][round_num] = np.mean(scores)
                    
        return aggregate_scores
        
    def create_visualization(self, output_dir: str = None):
        """Create the combined visualization of cooperation scores and points"""
        # Calculate aggregate cooperation scores
        agg_coop_scores = self.calculate_aggregate_cooperation_scores()
        
        # Prepare data
        sorted_rounds = sorted(self.rounds)
        agents = sorted(set(list(agg_coop_scores.keys()) + list(self.point_scores.keys())))
        
        # Create figure with two y-axes
        fig, ax1 = plt.subplots(figsize=(14, 8))
        ax2 = ax1.twinx()
        
        # Color palette
        colors = plt.cm.tab10(np.linspace(0, 1, len(agents)))
        
        # Plot cooperation scores (left axis)
        for i, agent in enumerate(agents):
            if agent in agg_coop_scores:
                rounds_with_scores = sorted(agg_coop_scores[agent].keys())
                coop_values = [agg_coop_scores[agent][r] for r in rounds_with_scores]
                
                # Plot cooperation scores with solid lines
                ax1.plot(rounds_with_scores, coop_values, 
                        color=colors[i], linewidth=2.5, alpha=0.8,
                        marker='o', markersize=8, 
                        label=f"{agent} (coop)")
                        
        # Plot point scores (right axis)
        for i, agent in enumerate(agents):
            if agent in self.point_scores:
                rounds_with_points = sorted(self.point_scores[agent].keys())
                point_values = [self.point_scores[agent][r] for r in rounds_with_points]
                
                # Interpolate missing rounds
                all_rounds = list(range(1, max(sorted_rounds) + 1))
                interpolated_points = []
                last_score = 0
                
                for r in all_rounds:
                    if r in self.point_scores[agent]:
                        last_score = self.point_scores[agent][r]
                    interpolated_points.append(last_score)
                
                # Plot points with dashed lines
                ax2.plot(all_rounds, interpolated_points,
                        color=colors[i], linewidth=2, alpha=0.6,
                        linestyle='--', marker='s', markersize=6,
                        label=f"{agent} (points)")
                        
        # Formatting
        ax1.set_xlabel('Round', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Cooperation Score (1-10)', fontsize=12, fontweight='bold', color='darkblue')
        ax2.set_ylabel('Cumulative Points', fontsize=12, fontweight='bold', color='darkgreen')
        
        # Set cooperation score limits
        ax1.set_ylim(0, 10.5)
        
        # Title
        plt.title(f'Agent Cooperation Scores and Points Progression\nSimulation: {self.simulation_id}', 
                 fontsize=14, fontweight='bold', pad=20)
        
        # Color the y-axis labels
        ax1.tick_params(axis='y', labelcolor='darkblue')
        ax2.tick_params(axis='y', labelcolor='darkgreen')
        
        # Grid
        ax1.grid(True, alpha=0.3)
        
        # Create custom legend
        # Cooperation scores legend
        coop_handles = []
        point_handles = []
        
        for i, agent in enumerate(agents):
            if agent in agg_coop_scores:
                coop_line = plt.Line2D([0], [0], color=colors[i], linewidth=2.5, 
                                      marker='o', markersize=8, label=agent)
                coop_handles.append(coop_line)
            if agent in self.point_scores:
                point_line = plt.Line2D([0], [0], color=colors[i], linewidth=2, 
                                       linestyle='--', marker='s', markersize=6, label=agent)
                point_handles.append(point_line)
        
        # Add legends
        legend1 = ax1.legend(coop_handles, [h.get_label() for h in coop_handles], 
                           loc='upper left', title='Cooperation Scores', 
                           framealpha=0.9, fontsize=9)
        legend2 = ax2.legend(point_handles, [h.get_label() for h in point_handles], 
                           loc='upper right', title='Point Scores', 
                           framealpha=0.9, fontsize=9)
        
        # Add legends to plot
        ax1.add_artist(legend1)
        
        # Add cooperation score reference lines
        ax1.axhline(y=5, color='gray', linestyle=':', alpha=0.5, label='Neutral (5)')
        ax1.axhline(y=8, color='green', linestyle=':', alpha=0.5, label='Cooperative (8)')
        ax1.axhline(y=3, color='red', linestyle=':', alpha=0.5, label='Uncooperative (3)')
        
        # Tight layout
        plt.tight_layout()
        
        # Save figure
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True, parents=True)
            filename = output_path / f"cooperation_points_progression_{self.simulation_id}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Saved visualization to: {filename}")
        else:
            # Save to simulation directory
            output_path = self.logs_dir / f"simulation_{self.simulation_id}" / "analysis_v2"
            output_path.mkdir(exist_ok=True, parents=True)
            filename = output_path / "cooperation_points_progression.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Saved visualization to: {filename}")
            
        plt.close()
        
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about cooperation and points"""
        agg_coop_scores = self.calculate_aggregate_cooperation_scores()
        
        summary = {
            'simulation_id': self.simulation_id,
            'num_rounds': len(self.rounds),
            'agents_analyzed': len(agg_coop_scores),
            'cooperation_trends': {},
            'point_leaders': {},
            'correlation_analysis': {}
        }
        
        # Analyze cooperation trends
        for agent in agg_coop_scores:
            scores = list(agg_coop_scores[agent].values())
            if len(scores) >= 2:
                # Calculate trend (positive = improving, negative = declining)
                trend = (scores[-1] - scores[0]) / len(scores)
                summary['cooperation_trends'][agent] = {
                    'start': scores[0],
                    'end': scores[-1],
                    'trend': trend,
                    'mean': np.mean(scores),
                    'std': np.std(scores)
                }
                
        # Identify point leaders per round
        for round_num in sorted(self.rounds):
            round_scores = {}
            for agent, scores in self.point_scores.items():
                if round_num in scores:
                    round_scores[agent] = scores[round_num]
            
            if round_scores:
                leader = max(round_scores, key=round_scores.get)
                summary['point_leaders'][round_num] = {
                    'leader': leader,
                    'score': round_scores[leader]
                }
                
        # Calculate correlation between cooperation and success
        for agent in agg_coop_scores:
            if agent in agg_coop_scores and agent in self.point_scores:
                # Get overlapping rounds
                coop_rounds = set(agg_coop_scores[agent].keys())
                point_rounds = set(self.point_scores[agent].keys())
                common_rounds = sorted(coop_rounds & point_rounds)
                
                if len(common_rounds) >= 3:
                    coop_values = [agg_coop_scores[agent][r] for r in common_rounds]
                    point_values = [self.point_scores[agent][r] for r in common_rounds]
                    
                    # Calculate correlation
                    if len(set(coop_values)) > 1:  # Avoid constant values
                        correlation = np.corrcoef(coop_values, point_values)[0, 1]
                        summary['correlation_analysis'][agent] = {
                            'correlation': correlation,
                            'interpretation': 'positive' if correlation > 0.3 else 'negative' if correlation < -0.3 else 'neutral'
                        }
                        
        return summary


def analyze_simulation(simulation_id: str, output_dir: str = None):
    """Convenience function to analyze a single simulation"""
    tracker = CooperationScoreTracker(simulation_id)
    tracker.parse_logs()
    tracker.create_visualization(output_dir)
    
    # Print summary
    summary = tracker.get_summary_stats()
    print(f"\n=== Cooperation & Points Analysis Summary ===")
    print(f"Simulation: {summary['simulation_id']}")
    print(f"Rounds analyzed: {summary['num_rounds']}")
    print(f"Agents tracked: {summary['agents_analyzed']}")
    
    print("\nCooperation Trends:")
    for agent, trend in summary['cooperation_trends'].items():
        direction = "↑" if trend['trend'] > 0 else "↓" if trend['trend'] < 0 else "→"
        print(f"  {agent}: {trend['start']:.1f} → {trend['end']:.1f} {direction} (mean: {trend['mean']:.1f})")
    
    print("\nCooperation-Success Correlation:")
    for agent, corr in summary['correlation_analysis'].items():
        print(f"  {agent}: {corr['correlation']:.3f} ({corr['interpretation']})")
    
    return tracker


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        sim_id = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else None
        analyze_simulation(sim_id, output)
    else:
        print("Usage: python cooperation_score_tracker.py <simulation_id> [output_dir]")
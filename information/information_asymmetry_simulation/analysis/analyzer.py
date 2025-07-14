"""
Post-simulation analysis tools
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import pandas as pd


class SimulationAnalyzer:
    """Analyzes simulation results and logs"""
    
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        
        # Load comprehensive log
        self.all_events = self._load_jsonl('simulation_log.jsonl')
        
        # Separate events by type
        self.events = [e for e in self.all_events if e['event_type'] not in ['message', 'agent_action', 'round_state']]
        self.messages = [e['data'] for e in self.all_events if e['event_type'] == 'message']
        self.actions = [e['data'] for e in self.all_events if e['event_type'] == 'agent_action']
        self.states = [e['data'] for e in self.all_events if e['event_type'] == 'round_state']
        
        # Load results
        results_path = self.log_dir / 'results.yaml'
        with open(results_path, 'r') as f:
            self.results = yaml.safe_load(f)
            
    def _load_jsonl(self, filename: str) -> List[Dict[str, Any]]:
        """Load a JSONL file"""
        filepath = self.log_dir / filename
        if not filepath.exists():
            return []
            
        data = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
        
    def analyze_communication_patterns(self) -> Dict[str, Any]:
        """Analyze communication patterns between agents"""
        analysis = {
            'total_messages': len(self.messages),
            'messages_by_type': Counter(),
            'messages_by_agent': defaultdict(int),
            'communication_matrix': defaultdict(lambda: defaultdict(int)),
            'deception_attempts': []
        }
        
        for msg in self.messages:
            msg_type = msg['type']
            from_agent = msg['from']
            
            analysis['messages_by_type'][msg_type] += 1
            analysis['messages_by_agent'][from_agent] += 1
            
            if msg_type == 'direct':
                to_agent = msg['to']
                analysis['communication_matrix'][from_agent][to_agent] += 1
                
        # Analyze deception
        for event in self.events:
            if event['event_type'] == 'deception_attempt':
                analysis['deception_attempts'].append(event['data'])
                
        return analysis
        
    def analyze_task_completion(self) -> Dict[str, Any]:
        """Analyze task completion patterns"""
        analysis = {
            'total_tasks_attempted': 0,
            'total_tasks_completed': 0,
            'completion_by_agent': defaultdict(lambda: {'attempted': 0, 'completed': 0}),
            'completion_by_round': defaultdict(int),
            'average_completion_time': None
        }
        
        for event in self.events:
            if event['event_type'] == 'task_completion':
                data = event['data']
                agent_id = data['agent_id']
                success = data['success']
                
                analysis['total_tasks_attempted'] += 1
                analysis['completion_by_agent'][agent_id]['attempted'] += 1
                
                if success:
                    analysis['total_tasks_completed'] += 1
                    analysis['completion_by_agent'][agent_id]['completed'] += 1
                    
        # Get completion by round from results
        for round_data in self.results['rounds']:
            round_num = round_data['round']
            completions = round_data['tasks_completed']
            analysis['completion_by_round'][round_num] = completions
            
        # Calculate success rate
        if analysis['total_tasks_attempted'] > 0:
            analysis['overall_success_rate'] = (
                analysis['total_tasks_completed'] / analysis['total_tasks_attempted']
            )
        else:
            analysis['overall_success_rate'] = 0
            
        return analysis
        
    def analyze_information_flow(self) -> Dict[str, Any]:
        """Analyze how information flows between agents"""
        analysis = {
            'information_requests': [],
            'information_shares': [],
            'information_withholding': [],
            'misinformation': []
        }
        
        # Analyze messages for information-related content
        for msg in self.messages:
            content = msg['content'].lower()
            
            # Simple heuristics for categorization
            if any(word in content for word in ['need', 'require', 'looking for', 'do you have']):
                analysis['information_requests'].append({
                    'from': msg['from'],
                    'to': msg.get('to', 'all'),
                    'content': msg['content']
                })
            elif any(word in content for word in ['here is', 'i have', 'the answer']):
                analysis['information_shares'].append({
                    'from': msg['from'],
                    'to': msg.get('to', 'all'),
                    'content': msg['content']
                })
                
        return analysis
        
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report"""
        comm_analysis = self.analyze_communication_patterns()
        task_analysis = self.analyze_task_completion()
        info_analysis = self.analyze_information_flow()
        
        report = f"""
# Information Asymmetry Simulation Analysis Report

## Overview
- Total Rounds: {self.results['total_rounds']}
- Total Agents: {len(self.results['final_rankings'])}
- Simulation Duration: {self.results['start_time']} to {self.results['end_time']}

## Final Rankings
"""
        for rank, (agent_id, score) in enumerate(self.results['final_rankings'].items(), 1):
            report += f"{rank}. {agent_id}: {score} points\n"
            
        report += f"""
## Communication Analysis
- Total Messages: {comm_analysis['total_messages']}
- Direct Messages: {comm_analysis['messages_by_type']['direct']}
- Broadcasts: {comm_analysis['messages_by_type']['broadcast']}
- Deception Attempts: {len(comm_analysis['deception_attempts'])}

### Most Active Communicators
"""
        sorted_communicators = sorted(
            comm_analysis['messages_by_agent'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        for agent, count in sorted_communicators[:3]:
            report += f"- {agent}: {count} messages\n"
            
        report += f"""
## Task Completion Analysis
- Total Tasks Attempted: {task_analysis['total_tasks_attempted']}
- Total Tasks Completed: {task_analysis['total_tasks_completed']}
- Overall Success Rate: {task_analysis['overall_success_rate']:.2%}

### Completion by Agent
"""
        for agent, stats in task_analysis['completion_by_agent'].items():
            success_rate = stats['completed'] / stats['attempted'] if stats['attempted'] > 0 else 0
            report += f"- {agent}: {stats['completed']}/{stats['attempted']} ({success_rate:.2%})\n"
            
        report += f"""
## Information Flow Analysis
- Information Requests: {len(info_analysis['information_requests'])}
- Information Shares: {len(info_analysis['information_shares'])}
- Potential Withholding: {len(info_analysis['information_withholding'])}
- Potential Misinformation: {len(info_analysis['misinformation'])}
"""
        
        return report
        
    def plot_results(self, output_dir: str = None):
        """Generate visualization plots"""
        if output_dir is None:
            output_dir = self.log_dir
        else:
            output_dir = Path(output_dir)
            
        # Plot 1: Score progression by round
        self._plot_score_progression(output_dir)
        
        # Plot 2: Communication heatmap
        self._plot_communication_heatmap(output_dir)
        
        # Plot 3: Task completion by round
        self._plot_task_completion(output_dir)
        
    def _plot_score_progression(self, output_dir: Path):
        """Plot score progression over rounds"""
        # Extract score data from rounds
        rounds = []
        agents = list(self.results['final_rankings'].keys())
        scores_by_agent = {agent: [] for agent in agents}
        
        # This would need to be extracted from state logs
        # For now, using a simplified approach
        plt.figure(figsize=(10, 6))
        plt.title('Agent Score Progression')
        plt.xlabel('Round')
        plt.ylabel('Score')
        plt.grid(True)
        plt.savefig(output_dir / 'score_progression.png')
        plt.close()
        
    def _plot_communication_heatmap(self, output_dir: Path):
        """Plot communication patterns as heatmap"""
        comm_analysis = self.analyze_communication_patterns()
        matrix = comm_analysis['communication_matrix']
        
        # Convert to DataFrame for easier plotting
        agents = sorted(set(list(matrix.keys()) + 
                          [to for from_dict in matrix.values() for to in from_dict.keys()]))
        
        data = []
        for from_agent in agents:
            row = []
            for to_agent in agents:
                count = matrix.get(from_agent, {}).get(to_agent, 0)
                row.append(count)
            data.append(row)
            
        plt.figure(figsize=(8, 8))
        plt.imshow(data, cmap='YlOrRd')
        plt.colorbar(label='Number of Messages')
        plt.xticks(range(len(agents)), agents, rotation=45)
        plt.yticks(range(len(agents)), agents)
        plt.xlabel('To Agent')
        plt.ylabel('From Agent')
        plt.title('Communication Heatmap')
        plt.tight_layout()
        plt.savefig(output_dir / 'communication_heatmap.png')
        plt.close()
        
    def _plot_task_completion(self, output_dir: Path):
        """Plot task completion by round"""
        task_analysis = self.analyze_task_completion()
        rounds = sorted(task_analysis['completion_by_round'].keys())
        completions = [task_analysis['completion_by_round'][r] for r in rounds]
        
        plt.figure(figsize=(10, 6))
        plt.bar(rounds, completions)
        plt.xlabel('Round')
        plt.ylabel('Tasks Completed')
        plt.title('Task Completion by Round')
        plt.grid(True, axis='y')
        plt.savefig(output_dir / 'task_completion_by_round.png')
        plt.close()


def main():
    """Run analysis on simulation results"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze simulation results')
    parser.add_argument('log_dir', help='Directory containing simulation logs')
    parser.add_argument('--output', '-o', help='Output directory for plots')
    parser.add_argument('--report', '-r', help='Output file for report')
    
    args = parser.parse_args()
    
    analyzer = SimulationAnalyzer(args.log_dir)
    
    # Generate report
    report = analyzer.generate_report()
    print(report)
    
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
            
    # Generate plots
    analyzer.plot_results(args.output)
    

if __name__ == '__main__':
    main()
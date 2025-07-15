"""
Foundational metrics analyzer for simulation logs.

This module implements basic metrics including:
- Total messages sent (by agent and round)
- Total information shared
- Task completion rate
- Broadcast frequency
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
from datetime import datetime


class FoundationalMetricsAnalyzer:
    """Analyzes foundational metrics from simulation logs."""
    
    def __init__(self, log_data: List[Dict[str, Any]]):
        """
        Initialize the analyzer with log data.
        
        Args:
            log_data: List of log events from simulation_log.jsonl
        """
        self.log_data = log_data
        self.messages = [e for e in log_data if e.get('event_type') == 'message']
        self.agent_actions = [e for e in log_data if e.get('event_type') == 'agent_action']
        self.info_exchanges = [e for e in log_data if e.get('event_type') == 'information_exchange']
        self.task_completions = [e for e in log_data if e.get('event_type') == 'task_completion']
        self.simulation_start = next((e for e in log_data if e.get('event_type') == 'simulation_start'), None)
        self.simulation_end = next((e for e in log_data if e.get('event_type') == 'simulation_end'), None)
        
    def analyze(self) -> Dict[str, Any]:
        """
        Run all foundational metrics analyses.
        
        Returns:
            Dictionary containing all foundational metrics results
        """
        return {
            'message_metrics': self._analyze_messages(),
            'information_sharing_metrics': self._analyze_information_sharing(),
            'task_completion_metrics': self._analyze_task_completion(),
            'broadcast_metrics': self._analyze_broadcasts(),
            'simulation_overview': self._get_simulation_overview()
        }
        
    def _analyze_messages(self) -> Dict[str, Any]:
        """Analyze message-related metrics."""
        metrics = {
            'total_messages': len(self.messages),
            'messages_by_agent': defaultdict(int),
            'messages_by_round': defaultdict(int),
            'messages_by_type': Counter(),
            'agent_round_matrix': defaultdict(lambda: defaultdict(int))
        }
        
        for msg_event in self.messages:
            data = msg_event.get('data', {})
            agent_id = data.get('from', 'unknown')
            round_num = data.get('round', 0)
            msg_type = data.get('type', 'unknown')
            
            metrics['messages_by_agent'][agent_id] += 1
            metrics['messages_by_round'][round_num] += 1
            metrics['messages_by_type'][msg_type] += 1
            metrics['agent_round_matrix'][agent_id][round_num] += 1
            
        # Calculate averages
        if metrics['messages_by_agent']:
            metrics['avg_messages_per_agent'] = (
                metrics['total_messages'] / len(metrics['messages_by_agent'])
            )
        else:
            metrics['avg_messages_per_agent'] = 0
            
        if metrics['messages_by_round']:
            metrics['avg_messages_per_round'] = (
                metrics['total_messages'] / len(metrics['messages_by_round'])
            )
        else:
            metrics['avg_messages_per_round'] = 0
            
        return metrics
        
    def _analyze_information_sharing(self) -> Dict[str, Any]:
        """Analyze information sharing patterns."""
        metrics = {
            'total_info_shared': len(self.info_exchanges),
            'info_shared_by_agent': defaultdict(int),
            'info_received_by_agent': defaultdict(int),
            'info_shared_by_round': defaultdict(int),
            'successful_exchanges': 0,
            'failed_exchanges': 0
        }
        
        for exchange_event in self.info_exchanges:
            data = exchange_event.get('data', {})
            from_agent = data.get('from', 'unknown')
            to_agent = data.get('to', 'unknown')
            round_num = data.get('round', 0)
            success = data.get('success', False)
            
            metrics['info_shared_by_agent'][from_agent] += 1
            if to_agent != 'all':  # Not a broadcast
                metrics['info_received_by_agent'][to_agent] += 1
            metrics['info_shared_by_round'][round_num] += 1
            
            if success:
                metrics['successful_exchanges'] += 1
            else:
                metrics['failed_exchanges'] += 1
                
        # Calculate sharing rate
        if metrics['total_info_shared'] > 0:
            metrics['success_rate'] = (
                metrics['successful_exchanges'] / metrics['total_info_shared']
            )
        else:
            metrics['success_rate'] = 0
            
        return metrics
        
    def _analyze_task_completion(self) -> Dict[str, Any]:
        """Analyze task completion metrics."""
        metrics = {
            'total_tasks_attempted': len(self.task_completions),
            'total_tasks_completed': 0,
            'tasks_by_agent': defaultdict(lambda: {'attempted': 0, 'completed': 0}),
            'tasks_by_round': defaultdict(lambda: {'attempted': 0, 'completed': 0}),
            'completion_times': []
        }
        
        for task_event in self.task_completions:
            data = task_event.get('data', {})
            agent_id = data.get('agent_id', 'unknown')
            round_num = data.get('round', 0)
            success = data.get('success', False)
            
            metrics['tasks_by_agent'][agent_id]['attempted'] += 1
            metrics['tasks_by_round'][round_num]['attempted'] += 1
            
            if success:
                metrics['total_tasks_completed'] += 1
                metrics['tasks_by_agent'][agent_id]['completed'] += 1
                metrics['tasks_by_round'][round_num]['completed'] += 1
                
                # Track completion time if available
                if 'completion_time' in data:
                    metrics['completion_times'].append(data['completion_time'])
                    
        # Calculate overall completion rate
        if metrics['total_tasks_attempted'] > 0:
            metrics['overall_completion_rate'] = (
                metrics['total_tasks_completed'] / metrics['total_tasks_attempted']
            )
        else:
            metrics['overall_completion_rate'] = 0
            
        # Calculate per-agent completion rates
        metrics['agent_completion_rates'] = {}
        for agent_id, stats in metrics['tasks_by_agent'].items():
            if stats['attempted'] > 0:
                metrics['agent_completion_rates'][agent_id] = (
                    stats['completed'] / stats['attempted']
                )
            else:
                metrics['agent_completion_rates'][agent_id] = 0
                
        return metrics
        
    def _analyze_broadcasts(self) -> Dict[str, Any]:
        """Analyze broadcast message patterns."""
        metrics = {
            'total_broadcasts': 0,
            'broadcasts_by_agent': defaultdict(int),
            'broadcasts_by_round': defaultdict(int),
            'broadcast_percentage': 0
        }
        
        broadcast_messages = [
            msg for msg in self.messages 
            if msg.get('data', {}).get('type') == 'broadcast'
        ]
        
        metrics['total_broadcasts'] = len(broadcast_messages)
        
        for msg_event in broadcast_messages:
            data = msg_event.get('data', {})
            agent_id = data.get('from', 'unknown')
            round_num = data.get('round', 0)
            
            metrics['broadcasts_by_agent'][agent_id] += 1
            metrics['broadcasts_by_round'][round_num] += 1
            
        # Calculate broadcast percentage
        total_messages = len(self.messages)
        if total_messages > 0:
            metrics['broadcast_percentage'] = (
                metrics['total_broadcasts'] / total_messages
            )
            
        # Calculate broadcast frequency per agent
        metrics['broadcast_frequency_by_agent'] = {}
        for agent_id, broadcast_count in metrics['broadcasts_by_agent'].items():
            agent_total_messages = sum(
                1 for msg in self.messages 
                if msg.get('data', {}).get('from') == agent_id
            )
            if agent_total_messages > 0:
                metrics['broadcast_frequency_by_agent'][agent_id] = (
                    broadcast_count / agent_total_messages
                )
            else:
                metrics['broadcast_frequency_by_agent'][agent_id] = 0
                
        return metrics
        
    def _get_simulation_overview(self) -> Dict[str, Any]:
        """Get basic simulation overview metrics."""
        overview = {
            'total_events': len(self.log_data),
            'total_rounds': 0,
            'unique_agents': set(),
            'simulation_duration': None
        }
        
        # Extract unique agents
        for event in self.log_data:
            data = event.get('data', {})
            if 'agent_id' in data:
                overview['unique_agents'].add(data['agent_id'])
            if 'from' in data:
                overview['unique_agents'].add(data['from'])
            if 'to' in data and data['to'] != 'all':
                overview['unique_agents'].add(data['to'])
                
        overview['unique_agents'] = list(overview['unique_agents'])
        overview['num_agents'] = len(overview['unique_agents'])
        
        # Get total rounds
        if self.simulation_end:
            overview['total_rounds'] = self.simulation_end.get('data', {}).get('total_rounds', 0)
        else:
            # Fallback: find max round number
            max_round = 0
            for event in self.log_data:
                round_num = event.get('data', {}).get('round', 0)
                max_round = max(max_round, round_num)
            overview['total_rounds'] = max_round
            
        # Calculate duration if timestamps available
        if self.simulation_start and self.simulation_end:
            start_time = self.simulation_start.get('timestamp')
            end_time = self.simulation_end.get('timestamp')
            if start_time and end_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    overview['simulation_duration'] = str(end_dt - start_dt)
                except:
                    pass
                    
        return overview
        
    def get_summary(self) -> str:
        """Generate a human-readable summary of foundational metrics."""
        results = self.analyze()
        
        summary = "=== FOUNDATIONAL METRICS SUMMARY ===\n\n"
        
        # Overview
        overview = results['simulation_overview']
        summary += f"Simulation Overview:\n"
        summary += f"  - Total Events: {overview['total_events']:,}\n"
        summary += f"  - Total Rounds: {overview['total_rounds']}\n"
        summary += f"  - Number of Agents: {overview['num_agents']}\n"
        if overview['simulation_duration']:
            summary += f"  - Duration: {overview['simulation_duration']}\n"
        summary += "\n"
        
        # Message metrics
        msg_metrics = results['message_metrics']
        summary += f"Message Metrics:\n"
        summary += f"  - Total Messages: {msg_metrics['total_messages']:,}\n"
        summary += f"  - Average per Agent: {msg_metrics['avg_messages_per_agent']:.2f}\n"
        summary += f"  - Average per Round: {msg_metrics['avg_messages_per_round']:.2f}\n"
        summary += f"  - Message Types: {dict(msg_metrics['messages_by_type'])}\n"
        summary += "\n"
        
        # Information sharing
        info_metrics = results['information_sharing_metrics']
        summary += f"Information Sharing Metrics:\n"
        summary += f"  - Total Information Shared: {info_metrics['total_info_shared']:,}\n"
        summary += f"  - Successful Exchanges: {info_metrics['successful_exchanges']:,}\n"
        summary += f"  - Success Rate: {info_metrics['success_rate']:.2%}\n"
        summary += "\n"
        
        # Task completion
        task_metrics = results['task_completion_metrics']
        summary += f"Task Completion Metrics:\n"
        summary += f"  - Total Tasks Attempted: {task_metrics['total_tasks_attempted']:,}\n"
        summary += f"  - Total Tasks Completed: {task_metrics['total_tasks_completed']:,}\n"
        summary += f"  - Overall Completion Rate: {task_metrics['overall_completion_rate']:.2%}\n"
        summary += "\n"
        
        # Broadcast metrics
        broadcast_metrics = results['broadcast_metrics']
        summary += f"Broadcast Metrics:\n"
        summary += f"  - Total Broadcasts: {broadcast_metrics['total_broadcasts']:,}\n"
        summary += f"  - Broadcast Percentage: {broadcast_metrics['broadcast_percentage']:.2%}\n"
        
        return summary
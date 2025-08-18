"""
Post-simulation analysis module for Information Asymmetry Simulation
Generates comprehensive metrics after each simulation run
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime
import statistics


class SimulationAnalyzer:
    """Analyzes simulation logs and generates comprehensive metrics"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.logger = logging.getLogger(__name__)
        self.events = []
        self.config = None
        self.final_results = None
        
    def analyze(self) -> Dict[str, Any]:
        """Run complete analysis and return metrics"""
        # Load simulation data
        self._load_simulation_data()
        
        # Calculate all metrics
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'simulation_id': self.log_dir.name,
            'configuration': self._get_config_summary(),
            'metrics': {
                'total_tasks_completed': self._calculate_total_tasks_completed(),
                'agent_revenue_ranking': self._calculate_agent_revenue_ranking(),
                'revenue_distribution': self._calculate_revenue_distribution(),
                'task_completions_by_round': self._calculate_task_completions_by_round(),
                'agents_with_zero_revenue': self._calculate_agents_with_zero_revenue(),
                'communication_efficiency': self._calculate_communication_efficiency(),
                'negotiation_cycle_time': self._calculate_negotiation_cycle_time(),
                'information_leverage': self._calculate_information_leverage(),
                'network_hub_analysis': self._calculate_network_hub_analysis()
            }
        }
        
        # Save analysis results
        self._save_analysis(metrics)
        
        return metrics
    
    def _load_simulation_data(self):
        """Load all simulation events from JSONL log file"""
        log_file = self.log_dir / 'simulation_log.jsonl'
        
        if not log_file.exists():
            raise FileNotFoundError(f"Simulation log not found: {log_file}")
        
        with open(log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Skip empty lines
                    line = line.strip()
                    if not line:
                        continue
                    
                    event = json.loads(line)
                    self.events.append(event)
                    
                    # Extract config and final results
                    if event.get('event_type') == 'simulation_start':
                        self.config = event.get('data', {}).get('config', {})
                    elif event.get('event_type') == 'simulation_end':
                        self.final_results = event.get('data', {}).get('results', {})
                except json.JSONDecodeError as e:
                    # Log warning but continue processing
                    if len(line) > 100:
                        self.logger.debug(f"Line {line_num}: Failed to parse (showing first 100 chars): {line[:100]}...")
                    else:
                        self.logger.debug(f"Line {line_num}: Failed to parse: {line}")
                except Exception as e:
                    self.logger.debug(f"Line {line_num}: Unexpected error: {e}")
    
    def _get_config_summary(self) -> Dict[str, Any]:
        """Extract key configuration parameters"""
        if not self.config:
            return {}
        
        return {
            'total_rounds': self.config['simulation']['rounds'],
            'num_agents': self.config['simulation']['agents'],
            'uncooperative_count': self.config['agents'].get('uncooperative_count', 0),
            'task_completion_revenue': self.config['revenue']['task_completion'],
            'incorrect_value_penalty': self.config['revenue'].get('incorrect_value_penalty', 0),
            'max_actions_per_turn': self.config['communication'].get('max_actions_per_turn', -1)
        }
    
    def _calculate_total_tasks_completed(self) -> int:
        """Metric 1: Total number of tasks completed"""
        count = 0
        for event in self.events:
            if event.get('event_type') == 'task_completion' and event.get('data', {}).get('success'):
                count += 1
        return count
    
    def _calculate_agent_revenue_ranking(self) -> List[Dict[str, Any]]:
        """Metric 2: Agent ranking by revenue generated"""
        # Track tasks completed per agent
        tasks_per_agent = defaultdict(int)
        for event in self.events:
            if event.get('event_type') == 'task_completion' and event.get('data', {}).get('success'):
                agent_id = event.get('data', {}).get('agent_id')
                if agent_id:
                    tasks_per_agent[agent_id] += 1
        
        # Get final revenue board
        if self.final_results and 'final_revenue_board' in self.final_results:
            revenue_board = self.final_results['final_revenue_board']
        else:
            # Try to reconstruct from events if no final board
            revenue_board = defaultdict(int)
            for event in self.events:
                if event.get('event_type') == 'task_completion' and event.get('data', {}).get('success'):
                    agent_id = event.get('data', {}).get('agent_id')
                    details = event.get('data', {}).get('details', {})
                    revenue = details.get('final_revenue', details.get('revenue', 0))
                    if agent_id and revenue > 0:
                        revenue_board[agent_id] += revenue
            revenue_board = dict(revenue_board)
        
        # Create ranking
        ranking = []
        for rank, (agent_id, revenue) in enumerate(revenue_board.items(), 1):
            ranking.append({
                'rank': rank,
                'agent_id': agent_id,
                'revenue': revenue,
                'tasks_completed': tasks_per_agent.get(agent_id, 0)
            })
        
        return ranking
    
    def _calculate_revenue_distribution(self) -> Dict[str, Any]:
        """Metric 3: Revenue Distribution (Gini Coefficient)"""
        revenues = []
        
        # Try to get from final results first
        if self.final_results and 'final_revenue_board' in self.final_results:
            revenues = list(self.final_results['final_revenue_board'].values())
        else:
            # Try to reconstruct from task completion events
            agent_revenues = defaultdict(int)
            for event in self.events:
                if event.get('event_type') == 'task_completion' and event.get('data', {}).get('success'):
                    agent_id = event.get('data', {}).get('agent_id')
                    details = event.get('data', {}).get('details', {})
                    revenue = details.get('final_revenue', 0)
                    if agent_id and revenue > 0:
                        agent_revenues[agent_id] += revenue
            
            if agent_revenues:
                revenues = list(agent_revenues.values())
            else:
                return {'gini_coefficient': None, 'error': 'No revenue data available'}
        
        if not revenues or len(revenues) < 2:
            return {
                'gini_coefficient': 0.0,
                'interpretation': 'Perfect equality or insufficient data'
            }
        
        # Calculate Gini coefficient
        sorted_revenues = sorted(revenues)
        n = len(sorted_revenues)
        
        # Calculate the Gini coefficient using the formula:
        # G = (2 * sum(i * y_i)) / (n * sum(y_i)) - (n + 1) / n
        cumsum = 0
        for i, revenue in enumerate(sorted_revenues, 1):
            cumsum += i * revenue
        
        total_revenue = sum(sorted_revenues)
        if total_revenue == 0:
            gini = 0.0
        else:
            gini = (2 * cumsum) / (n * total_revenue) - (n + 1) / n
        
        # Interpret Gini coefficient
        if gini < 0.2:
            interpretation = "Very low inequality"
        elif gini < 0.3:
            interpretation = "Low inequality"
        elif gini < 0.4:
            interpretation = "Moderate inequality"
        elif gini < 0.5:
            interpretation = "High inequality"
        else:
            interpretation = "Very high inequality"
        
        return {
            'gini_coefficient': round(gini, 4),
            'interpretation': interpretation,
            'min_revenue': min(revenues),
            'max_revenue': max(revenues),
            'mean_revenue': round(statistics.mean(revenues), 2),
            'median_revenue': statistics.median(revenues),
            'std_dev': round(statistics.stdev(revenues), 2) if len(revenues) > 1 else 0
        }
    
    def _calculate_task_completions_by_round(self) -> List[Dict[str, Any]]:
        """Metric 4: Task completions by round (cumulative)"""
        total_rounds = self.config['simulation']['rounds'] if self.config else 10
        
        # Count completions per round
        completions_per_round = defaultdict(int)
        for event in self.events:
            if event.get('event_type') == 'task_completion' and event.get('data', {}).get('success'):
                # Find the round number from recent agent_action events
                round_num = self._find_round_for_event(event.get('timestamp'))
                if round_num:
                    completions_per_round[round_num] += 1
        
        # Create cumulative series
        cumulative = []
        total = 0
        for round_num in range(1, total_rounds + 1):
            total += completions_per_round.get(round_num, 0)
            cumulative.append({
                'round': round_num,
                'tasks_completed_this_round': completions_per_round.get(round_num, 0),
                'cumulative_tasks_completed': total
            })
        
        return cumulative
    
    def _find_round_for_event(self, timestamp: str) -> Optional[int]:
        """Find the round number for a given event timestamp"""
        if not timestamp:
            return None
        # Look for the most recent agent_action before this timestamp
        for event in reversed(self.events):
            event_timestamp = event.get('timestamp')
            if event_timestamp and event_timestamp <= timestamp:
                if event.get('event_type') == 'agent_action':
                    return event.get('data', {}).get('round')
                elif event.get('event_type') == 'round_state':
                    return event.get('data', {}).get('round')
        return None
    
    def _calculate_agents_with_zero_revenue(self) -> Dict[str, Any]:
        """Metric 5: Number of agents ending with 0 revenue"""
        if self.final_results and 'final_revenue_board' in self.final_results:
            revenue_board = self.final_results['final_revenue_board']
            zero_revenue_agents = [agent for agent, revenue in revenue_board.items() if revenue == 0]
            
            return {
                'count': len(zero_revenue_agents),
                'agents': zero_revenue_agents,
                'percentage': round(len(zero_revenue_agents) / len(revenue_board) * 100, 2) if revenue_board else 0
            }
        
        return {'count': 0, 'agents': [], 'percentage': 0}
    
    def _calculate_communication_efficiency(self) -> Dict[str, Any]:
        """Metric 6: Communication Efficiency (messages per completed task)"""
        total_messages = 0
        message_types = defaultdict(int)
        
        for event in self.events:
            if event.get('event_type') == 'message':
                total_messages += 1
                message_types[event.get('data', {}).get('type', 'unknown')] += 1
        
        total_tasks = self._calculate_total_tasks_completed()
        
        if total_tasks > 0:
            efficiency = round(total_messages / total_tasks, 2)
        else:
            efficiency = float('inf') if total_messages > 0 else 0
        
        return {
            'messages_per_completed_task': efficiency,
            'total_messages': total_messages,
            'total_tasks_completed': total_tasks,
            'message_breakdown': dict(message_types)
        }
    
    def _calculate_negotiation_cycle_time(self) -> Dict[str, Any]:
        """Metric 7: Negotiation cycle time"""
        # Track information requests (agent A requests from agent B)
        requests = defaultdict(list)  # {(requester, provider): [{'round': ..., 'timestamp': ..., 'content': ...}]}
        
        # Track information transfers
        transfers = []  # [{'provider': ..., 'receiver': ..., 'information': ..., 'round': ..., 'timestamp': ...}]
        
        # Parse events to identify requests and transfers
        for event in self.events:
            if event.get('event_type') == 'message':
                data = event.get('data', {})
                if data.get('type') == 'direct' and data.get('from') != 'system':
                    # Try to identify if this is a request
                    content = data.get('content', '').lower()
                    if any(keyword in content for keyword in ['need', 'require', 'looking for', 'could you share', 'please share']):
                        round_num = self._find_round_for_event(event.get('timestamp'))
                        if round_num:
                            # This looks like a request
                            requester = data.get('from')
                            provider = data.get('to')
                            if requester and provider:
                                # Store the request
                                requests[(requester, provider)].append({
                                    'round': round_num,
                                    'timestamp': event.get('timestamp'),
                                    'content': content
                                })
            
            elif event.get('event_type') == 'information_exchange':
                data = event.get('data', {})
                round_num = self._find_round_for_event(event.get('timestamp'))
                if round_num:
                    transfers.append({
                        'provider': data.get('from_agent'),
                        'receiver': data.get('to_agent'),
                        'information': data.get('information', {}).get('transferred', []),
                        'round': round_num,
                        'timestamp': event.get('timestamp')
                    })
        
        # Match requests with transfers
        successful_negotiations = []
        unmatched_requests = 0
        
        for (requester, provider), request_list in requests.items():
            matched = False
            for request in request_list:
                # Look for a transfer from provider to requester after the request
                for transfer in transfers:
                    if (transfer['provider'] == provider and 
                        transfer['receiver'] == requester and
                        transfer['timestamp'] > request['timestamp']):
                        # Found a matching transfer
                        cycle_time = transfer['round'] - request['round']
                        successful_negotiations.append({
                            'requester': requester,
                            'provider': provider,
                            'request_round': request['round'],
                            'transfer_round': transfer['round'],
                            'cycle_time': cycle_time
                        })
                        matched = True
                        break
                if matched:
                    break
            
            if not matched:
                unmatched_requests += len(request_list)
        
        # Calculate statistics
        if successful_negotiations:
            cycle_times = [n['cycle_time'] for n in successful_negotiations]
            avg_cycle_time = round(statistics.mean(cycle_times), 2)
            median_cycle_time = statistics.median(cycle_times)
            min_cycle_time = min(cycle_times)
            max_cycle_time = max(cycle_times)
        else:
            avg_cycle_time = None
            median_cycle_time = None
            min_cycle_time = None
            max_cycle_time = None
        
        return {
            'average_negotiation_cycle_time': avg_cycle_time,
            'median_cycle_time': median_cycle_time,
            'min_cycle_time': min_cycle_time,
            'max_cycle_time': max_cycle_time,
            'successful_negotiations': len(successful_negotiations),
            'failed_requests': unmatched_requests,
            'success_rate': round(len(successful_negotiations) / (len(successful_negotiations) + unmatched_requests) * 100, 2) if (len(successful_negotiations) + unmatched_requests) > 0 else 0
        }
    
    def _calculate_information_leverage(self) -> Dict[str, Any]:
        """Metric 8: Information Leverage (how many times each piece is sent)"""
        info_transfer_count = defaultdict(int)
        info_quality_map = {}
        
        for event in self.events:
            if event.get('event_type') == 'information_exchange':
                transferred = event.get('data', {}).get('information', {}).get('transferred', [])
                for info_piece in transferred:
                    info_transfer_count[info_piece] += 1
        
        # Sort by transfer count
        sorted_info = sorted(info_transfer_count.items(), key=lambda x: x[1], reverse=True)
        
        # Get top 10 most transferred
        top_transferred = []
        for info_name, count in sorted_info[:10]:
            top_transferred.append({
                'information_piece': info_name,
                'times_transferred': count
            })
        
        # Calculate statistics
        transfer_counts = list(info_transfer_count.values())
        if transfer_counts:
            avg_transfers = round(statistics.mean(transfer_counts), 2)
            max_transfers = max(transfer_counts)
            total_unique_pieces = len(info_transfer_count)
        else:
            avg_transfers = 0
            max_transfers = 0
            total_unique_pieces = 0
        
        return {
            'top_transferred_information': top_transferred,
            'average_transfers_per_piece': avg_transfers,
            'max_transfers_single_piece': max_transfers,
            'total_unique_pieces_transferred': total_unique_pieces,
            'total_transfers': sum(transfer_counts)
        }
    
    def _calculate_network_hub_analysis(self) -> Dict[str, Any]:
        """Metric 9: Network Hub Analysis (messages received by each agent)"""
        messages_received = defaultdict(int)
        messages_sent = defaultdict(int)
        
        for event in self.events:
            if event.get('event_type') == 'message':
                data = event.get('data', {})
                msg_type = data.get('type')
                
                if msg_type == 'direct':
                    # Count for specific recipient
                    if data.get('from') != 'system':
                        to_agent = data.get('to')
                        from_agent = data.get('from')
                        if to_agent:
                            messages_received[to_agent] += 1
                        if from_agent:
                            messages_sent[from_agent] += 1
                elif msg_type == 'broadcast':
                    # Count for all agents except sender
                    sender = data.get('from')
                    if sender:
                        messages_sent[sender] += 1
                    # Broadcasts are received by all other agents
                    if self.config:
                        num_agents = self.config['simulation']['agents']
                        for i in range(1, num_agents + 1):
                            agent_id = f'agent_{i}'
                            if agent_id != sender:
                                messages_received[agent_id] += 1
        
        # Create rankings
        received_ranking = sorted(messages_received.items(), key=lambda x: x[1], reverse=True)
        sent_ranking = sorted(messages_sent.items(), key=lambda x: x[1], reverse=True)
        
        # Identify hubs (agents with high message activity)
        hubs = []
        for agent_id, received_count in received_ranking[:5]:  # Top 5 agents
            sent_count = messages_sent.get(agent_id, 0)
            hubs.append({
                'agent_id': agent_id,
                'messages_received': received_count,
                'messages_sent': sent_count,
                'total_activity': received_count + sent_count
            })
        
        return {
            'network_hubs': hubs,
            'messages_received_per_agent': dict(messages_received),
            'messages_sent_per_agent': dict(messages_sent),
            'most_contacted_agent': received_ranking[0] if received_ranking else None,
            'most_active_sender': sent_ranking[0] if sent_ranking else None
        }
    
    def _save_analysis(self, metrics: Dict[str, Any]):
        """Save analysis results to JSON file"""
        output_file = self.log_dir / 'analysis_results.json'
        
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        self.logger.info(f"Analysis results saved to {output_file}")


def run_analysis(log_dir: Path) -> Dict[str, Any]:
    """Convenience function to run analysis on a simulation log directory"""
    analyzer = SimulationAnalyzer(log_dir)
    return analyzer.analyze()
"""
Real batch processor that reads actual simulation data and generates metrics
"""

import json
import yaml
import statistics
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
from log_parser import parse_simulation_log
from data_processor import process_simulation_data


def process_batch_data(batch_dir: str) -> Dict[str, Any]:
    """Process batch data by reading actual simulation logs"""
    batch_path = Path(batch_dir)
    
    # Load existing aggregate summary if available
    aggregate_file = batch_path / 'aggregate_summary.json'
    if aggregate_file.exists():
        with open(aggregate_file, 'r') as f:
            aggregate_data = json.load(f)
    else:
        aggregate_data = {}
    
    # Load batch metadata
    metadata_file = batch_path / 'batch_metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        # Infer from data
        metadata = {'config': {'simulation': {'agents': 10, 'rounds': 10}}}
    
    # Process individual simulations for detailed metrics
    simulation_data = []
    agent_scores_all = defaultdict(list)  # agent -> list of final scores
    agent_ranks_all = defaultdict(list)   # agent -> list of final ranks
    task_completions = []
    round_data = defaultdict(lambda: {'scores': defaultdict(list), 'completions': 0})
    
    # Read each simulation
    for sim_dir in sorted(batch_path.iterdir()):
        if sim_dir.is_dir() and sim_dir.name.startswith('simulation_'):
            # Read results.yaml for quick access to final data
            results_file = sim_dir / 'results.yaml'
            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = yaml.safe_load(f)
                
                # Extract final rankings
                final_rankings = results.get('final_rankings', {})
                for rank, (agent, score) in enumerate(final_rankings.items(), 1):
                    agent_scores_all[agent].append(score)
                    agent_ranks_all[agent].append(rank)
                
                # Store total tasks for this simulation
                task_completions.append(results.get('total_tasks_completed', 0))
            
            # Read JSONL for round-by-round data
            log_file = sim_dir / 'simulation_log.jsonl'
            if log_file.exists():
                events = parse_simulation_log(str(log_file))
                
                # Track scores by round
                current_scores = defaultdict(int)
                current_round = 1
                
                for event in events:
                    if 'data' in event and 'round' in event['data']:
                        # Save scores at round transition
                        if event['data']['round'] > current_round:
                            for agent, score in current_scores.items():
                                round_data[current_round]['scores'][agent].append(score)
                            current_round = event['data']['round']
                    
                    # Update scores on task completion
                    if event['event_type'] == 'task_completion' and event['data']['success']:
                        agent_id = event['data']['agent_id']
                        points = event['data'].get('details', {}).get('points_awarded', 0)
                        current_scores[agent_id] += points
                        round_data[current_round]['completions'] += 1
                
                # Save final round scores
                for agent, score in current_scores.items():
                    round_data[current_round]['scores'][agent].append(score)
            
            simulation_data.append({
                'id': sim_dir.name,
                'final_rankings': final_rankings,
                'total_tasks': results.get('total_tasks_completed', 0) if 'results' in locals() else 0
            })
    
    # Calculate statistics for each agent
    agent_stats = {}
    all_agents = sorted(set(agent_scores_all.keys()))
    
    for agent in all_agents:
        scores = agent_scores_all[agent]
        ranks = agent_ranks_all[agent]
        
        if scores:
            agent_stats[agent] = {
                'mean_score': statistics.mean(scores),
                'std_score': statistics.stdev(scores) if len(scores) > 1 else 0,
                'min_score': min(scores),
                'max_score': max(scores),
                'mean_rank': statistics.mean(ranks),
                'best_rank': min(ranks),
                'worst_rank': max(ranks),
                'scores': scores,
                'ranks': ranks,
                'consistency': 1 - (statistics.stdev(scores) / statistics.mean(scores)) if len(scores) > 1 and statistics.mean(scores) > 0 else 1
            }
    
    # Calculate round-by-round averages
    round_averages = {}
    for round_num, data in round_data.items():
        round_scores = []
        for agent_scores in data['scores'].values():
            round_scores.extend(agent_scores)
        
        if round_scores:
            round_averages[round_num] = {
                'mean_score': statistics.mean(round_scores),
                'total_completions': data['completions'],
                'active_agents': len(data['scores'])
            }
    
    # Build the summary
    summary = {
        'batch_id': batch_path.name,
        'num_simulations': len(simulation_data),
        'config': metadata.get('config', {'simulation': {'agents': 10, 'rounds': 10}}),
        
        # Basic statistics from aggregate file
        'task_statistics': aggregate_data.get('task_statistics', {
            'mean': statistics.mean(task_completions) if task_completions else 0,
            'std': statistics.stdev(task_completions) if len(task_completions) > 1 else 0,
            'min': min(task_completions) if task_completions else 0,
            'max': max(task_completions) if task_completions else 0
        }),
        
        # Agent performance
        'agent_stats': agent_stats,
        
        # Winner analysis
        'winner_distribution': aggregate_data.get('winner_distribution', {}),
        
        # Round progression
        'round_averages': round_averages,
        
        # Simple correlations
        'performance_metrics': calculate_simple_metrics(agent_stats),
        
        # Simulation list
        'simulations': simulation_data
    }
    
    return summary


def calculate_simple_metrics(agent_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate simple performance metrics"""
    
    # Identify most and least consistent agents
    consistency_scores = [(agent, stats['consistency']) for agent, stats in agent_stats.items()]
    consistency_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Calculate overall statistics
    all_mean_scores = [stats['mean_score'] for stats in agent_stats.values()]
    all_std_scores = [stats['std_score'] for stats in agent_stats.values()]
    
    metrics = {
        'most_consistent_agent': consistency_scores[0][0] if consistency_scores else None,
        'least_consistent_agent': consistency_scores[-1][0] if consistency_scores else None,
        'highest_avg_score': max(agent_stats.items(), key=lambda x: x[1]['mean_score'])[0] if agent_stats else None,
        'lowest_avg_score': min(agent_stats.items(), key=lambda x: x[1]['mean_score'])[0] if agent_stats else None,
        'overall_mean_score': statistics.mean(all_mean_scores) if all_mean_scores else 0,
        'overall_score_spread': max(all_mean_scores) - min(all_mean_scores) if all_mean_scores else 0,
        'avg_consistency': statistics.mean([c[1] for c in consistency_scores]) if consistency_scores else 0
    }
    
    return metrics
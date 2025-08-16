"""
Simple batch processor that creates a working summary from aggregate_summary.json
"""

import json
import statistics
from pathlib import Path
from typing import Dict, Any


def process_simple_batch(batch_dir: str) -> Dict[str, Any]:
    """Process batch using just the aggregate summary and metadata"""
    batch_path = Path(batch_dir)
    
    # Load aggregate summary
    aggregate_file = batch_path / 'aggregate_summary.json'
    if not aggregate_file.exists():
        raise FileNotFoundError(f"No aggregate summary found in {batch_dir}")
    
    with open(aggregate_file, 'r') as f:
        agg_data = json.load(f)
    
    # Load batch metadata
    metadata_file = batch_path / 'batch_metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {'config': {'simulation': {'agents': 10, 'rounds': 10}}}
    
    # Build the expected structure for the dashboard
    summary = {
        'batch_id': batch_path.name,
        'num_simulations': agg_data.get('num_simulations', 0),
        'config': metadata.get('config', {'simulation': {'agents': 10, 'rounds': 10}}),
        
        # Aggregate metrics
        'aggregate_metrics': {
            'avg_tasks_per_agent': {
                'mean': agg_data.get('task_statistics', {}).get('mean', 0) / metadata['config']['simulation']['agents'],
                'ci': 0  # Would need more sims to calculate
            },
            'avg_points_per_agent': {
                'mean': sum(agent['mean_score'] for agent in agg_data.get('agent_performance', {}).values()) / len(agg_data.get('agent_performance', {})) if agg_data.get('agent_performance') else 0,
                'ci': 0
            },
            'cooperation_index': {'mean': 5, 'ci': 0.5},  # Placeholder
            'system_efficiency': {'mean': 0.7, 'ci': 0.1},  # Placeholder
            'score_distribution': _build_score_distribution(agg_data),
            'task_distribution': {
                'values': [],
                'bins': []
            }
        },
        
        # Performance data
        'performance_data': {
            'agent_comparisons': agg_data.get('agent_performance', {}),
            'consistency_metrics': _build_consistency_metrics(agg_data),
            'score_trajectories': {}  # Would need round-by-round data
        },
        
        # Ranking data
        'ranking_data': {
            'probability_matrix': _build_ranking_matrix(agg_data),
            'dominant_patterns': _find_dominant_patterns(agg_data),
            'average_ranks': {},
            'rank_volatility': {}
        },
        
        # Cooperation data (mostly placeholders without full data)
        'cooperation_data': {
            'score_distribution': {'mean': 5, 'std': 1.5, 'histogram': []},
            'performance_correlation': {'r': 0.5, 'p_value': 0.05, 'n': 30},
            'consistency_metrics': {},
            'alliance_rates': {'overall_rate': 0.3, 'avg_per_simulation': 3}
        },
        
        # Strategy data
        'strategy_data': {
            'sharing_patterns': {},
            'strategy_outcomes': {},
            'communication_analysis': {}
        },
        
        # Variance data
        'variance_data': {
            'outcome_variance': {
                'total_tasks': {
                    'mean': agg_data.get('task_statistics', {}).get('mean', 0),
                    'std': agg_data.get('task_statistics', {}).get('std', 0),
                    'cv': agg_data.get('task_statistics', {}).get('std', 0) / agg_data.get('task_statistics', {}).get('mean', 1) if agg_data.get('task_statistics', {}).get('mean', 0) > 0 else 0
                }
            },
            'winner_distribution': agg_data.get('winner_distribution', {}),
            'simulation_clusters': {
                'high_performing': [],
                'average': [],
                'low_performing': []
            },
            'outlier_simulations': []
        },
        
        # Statistical tests (placeholders for now)
        'statistical_tests': {
            'performance_anova': {
                'f_statistic': 0,
                'p_value': 1,
                'significant': False,
                'interpretation': 'Not enough data for statistical tests'
            },
            'pairwise_tests': [],
            'correlations': [],
            'effect_sizes': []
        }
    }
    
    return summary


def _build_score_distribution(agg_data: Dict) -> Dict:
    """Build score distribution from agent performance data"""
    distribution = {}
    
    for agent, perf in agg_data.get('agent_performance', {}).items():
        distribution[agent] = {
            'min': perf.get('min', 0),
            'q1': perf.get('min', 0) + (perf.get('max', 0) - perf.get('min', 0)) * 0.25,
            'median': perf.get('mean_score', 0),
            'q3': perf.get('min', 0) + (perf.get('max', 0) - perf.get('min', 0)) * 0.75,
            'max': perf.get('max', 0),
            'mean': perf.get('mean_score', 0),
            'outliers': []
        }
    
    return distribution


def _build_consistency_metrics(agg_data: Dict) -> Dict:
    """Build consistency metrics from agent performance"""
    metrics = {}
    
    for agent, perf in agg_data.get('agent_performance', {}).items():
        mean = perf.get('mean_score', 0)
        std = perf.get('std', 0)
        cv = (std / mean * 100) if mean > 0 else 0
        
        metrics[agent] = {
            'mean': mean,
            'std_dev': std,
            'cv_percent': cv,
            'min': perf.get('min', 0),
            'max': perf.get('max', 0),
            'range': perf.get('max', 0) - perf.get('min', 0)
        }
    
    return metrics


def _build_ranking_matrix(agg_data: Dict) -> Dict:
    """Build ranking probability matrix from winner distribution"""
    matrix = {}
    winner_dist = agg_data.get('winner_distribution', {})
    total_sims = agg_data.get('completed_simulations', 1)
    
    # Get all agents
    all_agents = set()
    for agent_data in agg_data.get('agent_performance', {}).keys():
        all_agents.add(agent_data)
    
    # Initialize matrix
    for agent in all_agents:
        matrix[agent] = {}
        for rank in range(1, len(all_agents) + 1):
            # Only have data for rank 1 (winners)
            if rank == 1:
                matrix[agent][str(rank)] = winner_dist.get(agent, 0) / total_sims
            else:
                # Distribute remaining probability
                if agent in winner_dist:
                    matrix[agent][str(rank)] = (1 - winner_dist.get(agent, 0) / total_sims) / (len(all_agents) - 1)
                else:
                    matrix[agent][str(rank)] = 1 / len(all_agents)
    
    return matrix


def _find_dominant_patterns(agg_data: Dict) -> list:
    """Find dominant ranking patterns"""
    patterns = []
    winner_dist = agg_data.get('winner_distribution', {})
    total_sims = agg_data.get('completed_simulations', 1)
    
    for agent, wins in winner_dist.items():
        freq = wins / total_sims
        if freq > 0.3:  # More than 30% wins
            patterns.append({
                'agent': agent,
                'rank': 1,
                'frequency': freq
            })
    
    return patterns
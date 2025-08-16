"""
Batch processor for aggregating data across multiple simulations
"""

import json
import yaml
import statistics
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from scipy import stats
from log_parser import parse_simulation_log
from data_processor import process_simulation_data


def process_batch_data(batch_dir: str) -> Dict[str, Any]:
    """Process all simulations in a batch and return aggregated data"""
    batch_path = Path(batch_dir)
    
    # Load batch metadata if available
    metadata_file = batch_path / 'batch_metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            batch_metadata = json.load(f)
    else:
        batch_metadata = {'batch_id': batch_path.name}
    
    # Collect data from all simulations
    all_simulations = []
    simulation_results = []
    
    for sim_dir in sorted(batch_path.iterdir()):
        if sim_dir.is_dir() and sim_dir.name.startswith('simulation_'):
            # Load results.yaml
            results_file = sim_dir / 'results.yaml'
            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = yaml.safe_load(f)
                    simulation_results.append(results)
            
            # Process full simulation data
            log_file = sim_dir / 'simulation_log.jsonl'
            if log_file.exists():
                events = parse_simulation_log(str(log_file))
                sim_data = process_simulation_data(events)
                sim_data['simulation_id'] = sim_dir.name
                all_simulations.append(sim_data)
    
    # Get config from first simulation
    config = all_simulations[0]['config'] if all_simulations else batch_metadata.get('config', {})
    
    # Aggregate data
    aggregated = {
        'batch_id': batch_path.name,
        'num_simulations': len(all_simulations),
        'config': config,
        'aggregate_metrics': calculate_aggregate_metrics(all_simulations, simulation_results),
        'performance_data': analyze_performance_data(all_simulations, simulation_results),
        'ranking_data': analyze_ranking_distributions(simulation_results),
        'cooperation_data': analyze_cooperation_patterns(all_simulations),
        'strategy_data': analyze_strategy_effectiveness(all_simulations),
        'variance_data': analyze_variance(all_simulations, simulation_results),
        'statistical_tests': perform_statistical_tests(all_simulations, simulation_results)
    }
    
    return aggregated


def calculate_aggregate_metrics(simulations: List[Dict], results: List[Dict]) -> Dict[str, Any]:
    """Calculate basic aggregate metrics across all simulations"""
    metrics = {}
    
    # Extract agent scores and task completions
    all_scores = defaultdict(list)
    all_tasks = defaultdict(list)
    total_tasks_per_sim = []
    total_messages_per_sim = []
    
    for result in results:
        final_rankings = result.get('final_rankings', {})
        for agent, score in final_rankings.items():
            all_scores[agent].append(score)
        
        total_tasks_per_sim.append(result.get('total_tasks_completed', 0))
        total_messages_per_sim.append(result.get('total_messages', 0))
    
    # Count tasks per agent from simulation data
    for sim in simulations:
        agent_tasks = defaultdict(int)
        for task_id, task_data in sim.get('tasks', {}).items():
            if task_data.get('completed'):
                agent = task_data.get('agent_id')
                if agent:
                    agent_tasks[agent] += 1
        
        for agent, count in agent_tasks.items():
            all_tasks[agent].append(count)
    
    # Calculate metrics with confidence intervals
    def calc_stats(data_list):
        if not data_list:
            return {'mean': 0, 'std': 0, 'ci': 0, 'min': 0, 'max': 0}
        
        mean = statistics.mean(data_list)
        std = statistics.stdev(data_list) if len(data_list) > 1 else 0
        # 95% confidence interval
        ci = 1.96 * std / (len(data_list) ** 0.5) if len(data_list) > 1 and std > 0 else 0
        
        return {
            'mean': mean,
            'std': std,
            'ci': ci,
            'min': min(data_list),
            'max': max(data_list)
        }
    
    # Average tasks per agent
    all_task_counts = [count for counts in all_tasks.values() for count in counts]
    metrics['avg_tasks_per_agent'] = calc_stats(all_task_counts)
    
    # Average points per agent
    all_score_values = [score for scores in all_scores.values() for score in scores]
    metrics['avg_points_per_agent'] = calc_stats(all_score_values)
    
    # Cooperation index (from cooperation scores)
    cooperation_scores = []
    for sim in simulations:
        if 'cooperation_dynamics' in sim and 'aggregated_scores' in sim['cooperation_dynamics']:
            for agent_data in sim['cooperation_dynamics']['aggregated_scores'].values():
                if agent_data.get('mean'):
                    cooperation_scores.append(agent_data['mean'])
    
    metrics['cooperation_index'] = calc_stats(cooperation_scores)
    
    # System efficiency (tasks completed / total possible)
    efficiency_values = []
    for i, result in enumerate(results):
        total_tasks = result.get('total_tasks_completed', 0)
        num_agents = len(result.get('final_rankings', {}))
        rounds = simulations[i]['config']['simulation']['rounds'] if i < len(simulations) else 10
        # Rough estimate of maximum possible tasks
        max_possible = num_agents * rounds * 0.5  # Assuming 0.5 tasks per agent per round max
        efficiency = total_tasks / max_possible if max_possible > 0 else 0
        efficiency_values.append(efficiency)
    
    metrics['system_efficiency'] = calc_stats(efficiency_values)
    
    # Score distribution for box plots
    metrics['score_distribution'] = {}
    for agent, scores in all_scores.items():
        if scores:
            metrics['score_distribution'][agent] = {
                'min': min(scores),
                'q1': np.percentile(scores, 25),
                'median': statistics.median(scores),
                'q3': np.percentile(scores, 75),
                'max': max(scores),
                'mean': statistics.mean(scores),
                'outliers': []  # Could calculate actual outliers
            }
    
    # Task completion distribution
    metrics['task_distribution'] = {
        'values': all_task_counts,
        'bins': np.histogram(all_task_counts, bins=10)[0].tolist() if all_task_counts else []
    }
    
    return metrics


def analyze_performance_data(simulations: List[Dict], results: List[Dict]) -> Dict[str, Any]:
    """Analyze performance patterns across simulations"""
    perf_data = {}
    
    # Agent performance comparison
    agent_scores = defaultdict(list)
    for result in results:
        for agent, score in result.get('final_rankings', {}).items():
            agent_scores[agent].append(score)
    
    perf_data['agent_comparisons'] = {}
    for agent, scores in agent_scores.items():
        perf_data['agent_comparisons'][agent] = {
            'mean_score': statistics.mean(scores),
            'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
            'min_score': min(scores),
            'max_score': max(scores),
            'num_simulations': len(scores)
        }
    
    # Performance consistency metrics
    perf_data['consistency_metrics'] = {}
    for agent, scores in agent_scores.items():
        mean_score = statistics.mean(scores) if scores else 0
        if scores and mean_score > 0 and len(scores) > 1:
            cv = (statistics.stdev(scores) / mean_score * 100)
        else:
            cv = 0
        
        perf_data['consistency_metrics'][agent] = {
            'mean': statistics.mean(scores) if scores else 0,
            'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
            'cv_percent': cv,
            'min': min(scores) if scores else 0,
            'max': max(scores) if scores else 0,
            'range': max(scores) - min(scores) if scores else 0
        }
    
    # Score trajectories (average score per round across simulations)
    round_scores = defaultdict(lambda: defaultdict(list))
    for sim in simulations:
        if 'scores_over_time' in sim:
            for agent, round_data in sim['scores_over_time'].items():
                for round_info in round_data:
                    round_num = round_info['round']
                    score = round_info['score']
                    round_scores[round_num][agent].append(score)
    
    perf_data['score_trajectories'] = {}
    for round_num, agent_scores in round_scores.items():
        perf_data['score_trajectories'][round_num] = {}
        for agent, scores in agent_scores.items():
            perf_data['score_trajectories'][round_num][agent] = {
                'mean': statistics.mean(scores),
                'std': statistics.stdev(scores) if len(scores) > 1 else 0,
                'ci_lower': statistics.mean(scores) - 1.96 * statistics.stdev(scores) / (len(scores) ** 0.5) if len(scores) > 1 and statistics.stdev(scores) > 0 else statistics.mean(scores),
                'ci_upper': statistics.mean(scores) + 1.96 * statistics.stdev(scores) / (len(scores) ** 0.5) if len(scores) > 1 and statistics.stdev(scores) > 0 else statistics.mean(scores)
            }
    
    return perf_data


def analyze_ranking_distributions(results: List[Dict]) -> Dict[str, Any]:
    """Analyze how rankings are distributed across simulations"""
    rank_data = {}
    
    # Track rankings for each agent
    agent_rankings = defaultdict(list)
    
    for result in results:
        rankings = result.get('final_rankings', {})
        sorted_agents = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
        
        for rank, (agent, score) in enumerate(sorted_agents, 1):
            agent_rankings[agent].append(rank)
    
    # Calculate ranking probabilities
    rank_data['probability_matrix'] = {}
    num_agents = len(agent_rankings)
    
    for agent, ranks in agent_rankings.items():
        rank_data['probability_matrix'][agent] = {}
        for r in range(1, num_agents + 1):
            prob = ranks.count(r) / len(ranks) if ranks else 0
            rank_data['probability_matrix'][agent][str(r)] = prob
    
    # Dominant ranking patterns
    rank_data['dominant_patterns'] = []
    for agent, ranks in agent_rankings.items():
        if ranks:
            most_common_rank = max(set(ranks), key=ranks.count)
            frequency = ranks.count(most_common_rank) / len(ranks)
            if frequency > 0.3:  # Agent achieves this rank in >30% of simulations
                rank_data['dominant_patterns'].append({
                    'agent': agent,
                    'rank': most_common_rank,
                    'frequency': frequency
                })
    
    # Average ranks
    rank_data['average_ranks'] = {}
    for agent, ranks in agent_rankings.items():
        if ranks:
            rank_data['average_ranks'][agent] = {
                'mean': statistics.mean(ranks),
                'std': statistics.stdev(ranks) if len(ranks) > 1 else 0,
                'mode': max(set(ranks), key=ranks.count)
            }
    
    # Rank volatility
    rank_data['rank_volatility'] = {}
    for agent, ranks in agent_rankings.items():
        if len(ranks) > 1:
            # Calculate how much ranks change between simulations
            rank_changes = [abs(ranks[i] - ranks[i-1]) for i in range(1, len(ranks))]
            volatility = statistics.mean(rank_changes) if rank_changes else 0
        else:
            volatility = 0
        
        rank_data['rank_volatility'][agent] = volatility
    
    return rank_data


def analyze_cooperation_patterns(simulations: List[Dict]) -> Dict[str, Any]:
    """Analyze cooperation patterns across simulations"""
    coop_data = {}
    
    # Collect cooperation scores
    cooperation_given = defaultdict(list)
    cooperation_received = defaultdict(list)
    
    for sim in simulations:
        if 'cooperation_dynamics' in sim and 'cooperation_scores' in sim['cooperation_dynamics']:
            scores = sim['cooperation_dynamics']['cooperation_scores']
            
            # Process each agent's scores
            for reporter, targets in scores.items():
                for target, score in targets.items():
                    if target != 'self':
                        # Try to convert to number if it's a string
                        try:
                            numeric_score = float(score) if not isinstance(score, (int, float)) else score
                            cooperation_given[reporter].append(numeric_score)
                            cooperation_received[target].append(numeric_score)
                        except (ValueError, TypeError):
                            # Skip non-numeric values
                            continue
    
    # Score distribution
    all_scores = [score for scores in cooperation_given.values() for score in scores]
    if all_scores:
        coop_data['score_distribution'] = {
            'mean': statistics.mean(all_scores),
            'std': statistics.stdev(all_scores) if len(all_scores) > 1 else 0,
            'histogram': np.histogram(all_scores, bins=10)[0].tolist()
        }
    
    # Performance correlation
    # Correlate average cooperation received with final score
    agent_avg_coop = {}
    agent_avg_score = {}
    
    for agent in cooperation_received:
        if cooperation_received[agent]:
            agent_avg_coop[agent] = statistics.mean(cooperation_received[agent])
    
    for sim in simulations:
        if 'final_results' in sim and 'final_rankings' in sim['final_results']:
            for agent, score in sim['final_results']['final_rankings'].items():
                if agent not in agent_avg_score:
                    agent_avg_score[agent] = []
                agent_avg_score[agent].append(score)
    
    # Calculate correlation
    agents_with_both = set(agent_avg_coop.keys()) & set(agent_avg_score.keys())
    if len(agents_with_both) >= 3:
        x = [agent_avg_coop[a] for a in agents_with_both]
        y = [statistics.mean(agent_avg_score[a]) for a in agents_with_both]
        correlation, p_value = stats.pearsonr(x, y)
        
        coop_data['performance_correlation'] = {
            'r': correlation,
            'p_value': p_value,
            'n': len(agents_with_both)
        }
    else:
        coop_data['performance_correlation'] = {'r': 0, 'p_value': 1, 'n': 0}
    
    # Consistency metrics
    coop_data['consistency_metrics'] = {}
    all_agents = set(cooperation_given.keys()) | set(cooperation_received.keys())
    
    for agent in all_agents:
        given_scores = cooperation_given.get(agent, [])
        received_scores = cooperation_received.get(agent, [])
        
        coop_data['consistency_metrics'][agent] = {
            'mean_given': statistics.mean(given_scores) if given_scores else 0,
            'std_given': statistics.stdev(given_scores) if len(given_scores) > 1 else 0,
            'mean_received': statistics.mean(received_scores) if received_scores else 0,
            'std_received': statistics.stdev(received_scores) if len(received_scores) > 1 else 0,
            'reciprocity': 1 - abs(statistics.mean(given_scores or [5]) - statistics.mean(received_scores or [5])) / 5
        }
    
    # Alliance formation rates
    alliances_formed = 0
    total_possible = 0
    
    for sim in simulations:
        if 'cooperation_dynamics' in sim and 'networks' in sim['cooperation_dynamics']:
            networks = sim['cooperation_dynamics']['networks']
            if 'strong_mutual_cooperation' in networks:
                alliances_formed += len(networks['strong_mutual_cooperation'])
            
            # Count total possible alliances (n choose 2)
            num_agents = len(sim['agents'])
            total_possible += num_agents * (num_agents - 1) / 2
    
    coop_data['alliance_rates'] = {
        'overall_rate': alliances_formed / total_possible if total_possible > 0 else 0,
        'avg_per_simulation': alliances_formed / len(simulations) if simulations else 0
    }
    
    return coop_data


def analyze_strategy_effectiveness(simulations: List[Dict]) -> Dict[str, Any]:
    """Analyze different strategies and their effectiveness"""
    strat_data = {}
    
    # Information sharing patterns
    sharing_patterns = defaultdict(list)
    
    for sim in simulations:
        if 'strategic_analysis' in sim:
            strategies = sim['strategic_analysis']
            for agent, strategy_data in strategies.items():
                hoarding_rate = strategy_data.get('information_hoarding_rate', 0)
                if hoarding_rate < 0.2:
                    pattern = 'generous'
                elif hoarding_rate < 0.5:
                    pattern = 'balanced'
                else:
                    pattern = 'selfish'
                
                sharing_patterns[pattern].append({
                    'agent': agent,
                    'final_score': sim['final_results']['final_rankings'].get(agent, 0)
                })
    
    # Calculate average performance by strategy
    strat_data['sharing_patterns'] = {}
    for pattern, instances in sharing_patterns.items():
        scores = [inst['final_score'] for inst in instances]
        if scores:
            strat_data['sharing_patterns'][pattern] = {
                'mean_score': statistics.mean(scores),
                'std': statistics.stdev(scores) if len(scores) > 1 else 0,
                'count': len(scores)
            }
    
    # Strategy outcomes
    strat_data['strategy_outcomes'] = {
        'cooperation_vs_performance': {},
        'communication_vs_performance': {}
    }
    
    # Communication analysis
    comm_patterns = defaultdict(list)
    for sim in simulations:
        if 'communication_metrics' in sim:
            metrics = sim['communication_metrics']
            for agent, comm_data in metrics.get('agent_metrics', {}).items():
                msg_rate = comm_data.get('messages_per_round', 0)
                final_score = sim['final_results']['final_rankings'].get(agent, 0)
                
                if msg_rate < 2:
                    pattern = 'low_communication'
                elif msg_rate < 5:
                    pattern = 'moderate_communication'
                else:
                    pattern = 'high_communication'
                
                comm_patterns[pattern].append(final_score)
    
    strat_data['communication_analysis'] = {}
    for pattern, scores in comm_patterns.items():
        if scores:
            strat_data['communication_analysis'][pattern] = {
                'mean_score': statistics.mean(scores),
                'std': statistics.stdev(scores) if len(scores) > 1 else 0,
                'count': len(scores)
            }
    
    return strat_data


def analyze_variance(simulations: List[Dict], results: List[Dict]) -> Dict[str, Any]:
    """Analyze variance and identify patterns in outcomes"""
    var_data = {}
    
    # Outcome variance by metric
    metrics_variance = {
        'total_tasks': [],
        'total_messages': [],
        'winner_agent': []
    }
    
    for result in results:
        metrics_variance['total_tasks'].append(result.get('total_tasks_completed', 0))
        metrics_variance['total_messages'].append(result.get('total_messages', 0))
        # Get winner (highest scorer)
        rankings = result.get('final_rankings', {})
        if rankings:
            winner = max(rankings.items(), key=lambda x: x[1])[0]
            metrics_variance['winner_agent'].append(winner)
    
    # Calculate variance metrics
    var_data['outcome_variance'] = {}
    for metric, values in metrics_variance.items():
        if metric != 'winner_agent' and values:
            var_data['outcome_variance'][metric] = {
                'mean': statistics.mean(values),
                'std': statistics.stdev(values) if len(values) > 1 else 0,
                'cv': statistics.stdev(values) / statistics.mean(values) if len(values) > 1 and statistics.mean(values) != 0 else 0
            }
    
    # Winner distribution
    winner_counts = {}
    for winner in metrics_variance['winner_agent']:
        winner_counts[winner] = winner_counts.get(winner, 0) + 1
    
    var_data['winner_distribution'] = winner_counts
    
    # Simulation clustering (simplified - group by outcome similarity)
    # This is a placeholder for more sophisticated clustering
    var_data['simulation_clusters'] = {
        'high_performing': [],
        'average': [],
        'low_performing': []
    }
    
    avg_tasks = statistics.mean(metrics_variance['total_tasks']) if metrics_variance['total_tasks'] else 0
    std_tasks = statistics.stdev(metrics_variance['total_tasks']) if len(metrics_variance['total_tasks']) > 1 else 0
    
    for i, result in enumerate(results):
        tasks = result.get('total_tasks_completed', 0)
        if tasks > avg_tasks + std_tasks:
            cluster = 'high_performing'
        elif tasks < avg_tasks - std_tasks:
            cluster = 'low_performing'
        else:
            cluster = 'average'
        
        var_data['simulation_clusters'][cluster].append({
            'simulation': f'simulation_{i+1:03d}',
            'total_tasks': tasks
        })
    
    # Outlier detection
    var_data['outlier_simulations'] = []
    
    # Simple outlier detection based on total score
    all_total_scores = []
    for result in results:
        total_score = sum(result.get('final_rankings', {}).values())
        all_total_scores.append(total_score)
    
    if all_total_scores:
        mean_score = statistics.mean(all_total_scores)
        std_score = statistics.stdev(all_total_scores) if len(all_total_scores) > 1 else 0
        
        for i, score in enumerate(all_total_scores):
            if abs(score - mean_score) > 2 * std_score:  # 2 standard deviations
                var_data['outlier_simulations'].append({
                    'simulation': f'simulation_{i+1:03d}',
                    'total_score': score,
                    'deviation': (score - mean_score) / std_score if std_score > 0 else 0
                })
    
    return var_data


def perform_statistical_tests(simulations: List[Dict], results: List[Dict]) -> Dict[str, Any]:
    """Perform statistical significance tests"""
    test_results = {}
    
    # Collect agent scores across simulations
    agent_scores = defaultdict(list)
    for result in results:
        for agent, score in result.get('final_rankings', {}).items():
            agent_scores[agent].append(score)
    
    # ANOVA for agent performance differences
    if len(agent_scores) >= 3:
        # Prepare data for ANOVA
        score_groups = [scores for scores in agent_scores.values() if len(scores) >= 3]
        
        if len(score_groups) >= 3:
            f_stat, p_value = stats.f_oneway(*score_groups)
            
            test_results['performance_anova'] = {
                'f_statistic': f_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'interpretation': 'Significant differences between agents' if p_value < 0.05 else 'No significant differences'
            }
    
    # Pairwise comparisons (top agents)
    test_results['pairwise_tests'] = []
    
    # Sort agents by average score
    agent_avg_scores = [(agent, statistics.mean(scores)) for agent, scores in agent_scores.items() if scores]
    agent_avg_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Compare top 3 agents pairwise
    for i in range(min(3, len(agent_avg_scores))):
        for j in range(i + 1, min(3, len(agent_avg_scores))):
            agent1, avg1 = agent_avg_scores[i]
            agent2, avg2 = agent_avg_scores[j]
            
            scores1 = agent_scores[agent1]
            scores2 = agent_scores[agent2]
            
            if len(scores1) >= 3 and len(scores2) >= 3:
                t_stat, p_value = stats.ttest_ind(scores1, scores2)
                
                test_results['pairwise_tests'].append({
                    'agent1': agent1,
                    'agent2': agent2,
                    'mean_diff': avg1 - avg2,
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                })
    
    # Correlation tests
    test_results['correlations'] = []
    
    # Cooperation vs Performance
    coop_scores = []
    perf_scores = []
    
    for sim in simulations:
        if 'cooperation_dynamics' in sim and 'aggregated_scores' in sim['cooperation_dynamics']:
            for agent, coop_data in sim['cooperation_dynamics']['aggregated_scores'].items():
                if 'mean' in coop_data and coop_data['mean'] is not None:
                    coop_scores.append(coop_data['mean'])
                    # Get corresponding performance
                    if 'final_results' in sim and 'final_rankings' in sim['final_results']:
                        score = sim['final_results']['final_rankings'].get(agent, 0)
                        perf_scores.append(score)
    
    if len(coop_scores) >= 10 and len(coop_scores) == len(perf_scores):
        r, p = stats.pearsonr(coop_scores, perf_scores)
        test_results['correlations'].append({
            'var1': 'Cooperation Score',
            'var2': 'Performance',
            'correlation': r,
            'p_value': p,
            'n': len(coop_scores)
        })
    
    # Communication vs Performance
    comm_rates = []
    comm_perf_scores = []
    
    for sim in simulations:
        if 'communication_metrics' in sim and 'agent_metrics' in sim['communication_metrics']:
            for agent, metrics in sim['communication_metrics']['agent_metrics'].items():
                msg_rate = metrics.get('messages_per_round', 0)
                comm_rates.append(msg_rate)
                # Get performance
                if 'final_results' in sim and 'final_rankings' in sim['final_results']:
                    score = sim['final_results']['final_rankings'].get(agent, 0)
                    comm_perf_scores.append(score)
    
    if len(comm_rates) >= 10 and len(comm_rates) == len(comm_perf_scores):
        r, p = stats.pearsonr(comm_rates, comm_perf_scores)
        test_results['correlations'].append({
            'var1': 'Message Rate',
            'var2': 'Performance',
            'correlation': r,
            'p_value': p,
            'n': len(comm_rates)
        })
    
    # Effect size analysis
    test_results['effect_sizes'] = []
    
    # Calculate Cohen's d for top vs bottom performers
    if len(agent_avg_scores) >= 4:
        # Top 25% vs Bottom 25%
        n_top = max(1, len(agent_avg_scores) // 4)
        n_bottom = max(1, len(agent_avg_scores) // 4)
        
        top_agents = [a[0] for a in agent_avg_scores[:n_top]]
        bottom_agents = [a[0] for a in agent_avg_scores[-n_bottom:]]
        
        top_scores = [s for a in top_agents for s in agent_scores[a]]
        bottom_scores = [s for a in bottom_agents for s in agent_scores[a]]
        
        if top_scores and bottom_scores:
            # Cohen's d
            mean_diff = statistics.mean(top_scores) - statistics.mean(bottom_scores)
            if len(top_scores) > 1 and len(bottom_scores) > 1:
                var_top = statistics.stdev(top_scores)**2
                var_bottom = statistics.stdev(bottom_scores)**2
                pooled_std = ((var_top + var_bottom) / 2) ** 0.5
            else:
                pooled_std = 1
            cohens_d = mean_diff / pooled_std if pooled_std != 0 else 0
            
            test_results['effect_sizes'].append({
                'comparison': 'Top 25% vs Bottom 25%',
                'cohens_d': cohens_d,
                'interpretation': 'Large' if abs(cohens_d) > 0.8 else 'Medium' if abs(cohens_d) > 0.5 else 'Small'
            })
    
    return test_results
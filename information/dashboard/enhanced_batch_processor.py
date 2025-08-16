"""
Enhanced batch processor focusing on meaningful, actionable metrics
"""

import json
import yaml
import statistics
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from scipy import stats
from log_parser import parse_simulation_log
from data_processor import process_simulation_data
from enhanced_batch_analyzer import enhance_batch_analysis


def convert_to_native_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_to_native_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native_types(item) for item in obj]
    return obj


class EnhancedBatchProcessor:
    """Process batch simulations to extract meaningful patterns and insights"""
    
    def __init__(self, batch_dir: str):
        self.batch_path = Path(batch_dir)
        self.simulations = []
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict:
        """Load batch metadata"""
        metadata_file = self.batch_path / 'batch_metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {'config': {'simulation': {'agents': 10, 'rounds': 10}}}
    
    def process(self) -> Dict[str, Any]:
        """Main processing pipeline"""
        # Load all simulation data
        self._load_simulations()
        
        # Core analyses
        results = {
            'batch_id': self.batch_path.name,
            'num_simulations': len(self.simulations),
            'config': self.metadata.get('config'),
            
            # Strategic insights
            'strategy_effectiveness': self._analyze_strategy_effectiveness(),
            
            # Performance patterns
            'performance_patterns': self._analyze_performance_patterns(),
            
            # Information economics
            'information_economics': self._analyze_information_economics(),
            
            # Behavioral correlations
            'behavioral_correlations': self._analyze_behavioral_correlations(),
            
            # Temporal dynamics
            'temporal_dynamics': self._analyze_temporal_dynamics(),
            
            # Statistical confidence
            'statistical_analysis': self._perform_statistical_analysis(),
            
            # Key insights summary
            'key_insights': self._generate_key_insights()
        }
        
        return results
    
    def _load_simulations(self):
        """Load and process all simulations in the batch"""
        for sim_dir in sorted(self.batch_path.iterdir()):
            if sim_dir.is_dir() and sim_dir.name.startswith('simulation_'):
                sim_data = self._process_single_simulation(sim_dir)
                if sim_data:
                    self.simulations.append(sim_data)
    
    def _process_single_simulation(self, sim_dir: Path) -> Optional[Dict]:
        """Process a single simulation"""
        results_file = sim_dir / 'results.yaml'
        log_file = sim_dir / 'simulation_log.jsonl'
        
        # Skip if no log file
        if not log_file.exists():
            return None
        
        # Parse events for detailed metrics
        events = parse_simulation_log(str(log_file))
        
        # Handle missing results.yaml
        if not results_file.exists():
            
            # Extract final rankings from events
            final_rankings = {}
            total_tasks = 0
            agent_scores = {}
            
            for event in events:
                if event['event_type'] == 'simulation_end' and 'final_rankings' in event.get('data', {}):
                    final_rankings = event['data']['final_rankings']
                elif event['event_type'] == 'task_completion' and event['data'].get('success'):
                    total_tasks += 1
                    # Track scores if no final rankings
                    agent = event['data'].get('agent_id')
                    points = event['data'].get('details', {}).get('points_awarded', 0)
                    if agent:
                        agent_scores[agent] = agent_scores.get(agent, 0) + points
            
            # Use accumulated scores if no final rankings found
            if not final_rankings and agent_scores:
                final_rankings = agent_scores
            
            sim_data = {
                'id': sim_dir.name,
                'final_rankings': final_rankings,
                'total_tasks': total_tasks,
                'agent_metrics': self._extract_agent_metrics(events),
                'cooperation_metrics': self._extract_cooperation_metrics(events),
                'information_metrics': self._extract_information_metrics(events),
                'temporal_metrics': self._extract_temporal_metrics(events)
            }
            
            return sim_data
        
        # Load results
        with open(results_file, 'r') as f:
            results = yaml.safe_load(f)
        
        # Parse events for detailed metrics
        events = parse_simulation_log(str(log_file))
        
        # Extract key metrics
        sim_data = {
            'id': sim_dir.name,
            'final_rankings': results.get('final_rankings', {}),
            'total_tasks': results.get('total_tasks_completed', 0),
            'agent_metrics': self._extract_agent_metrics(events),
            'cooperation_metrics': self._extract_cooperation_metrics(events),
            'information_metrics': self._extract_information_metrics(events),
            'temporal_metrics': self._extract_temporal_metrics(events)
        }
        
        return sim_data
    
    def _extract_agent_metrics(self, events: List[Dict]) -> Dict:
        """Extract per-agent performance metrics"""
        metrics = defaultdict(lambda: {
            'tasks_completed': 0,
            'points_earned': 0,
            'messages_sent': 0,
            'info_shared': 0,
            'info_received': 0,
            'requests_made': 0,
            'requests_fulfilled': 0,
            'first_completions': 0
        })
        
        for event in events:
            if event['event_type'] == 'task_completion' and event['data'].get('success'):
                agent = event['data']['agent_id']
                metrics[agent]['tasks_completed'] += 1
                points = event['data'].get('details', {}).get('points_awarded', 0)
                metrics[agent]['points_earned'] += points
                if event['data'].get('details', {}).get('first_completion'):
                    metrics[agent]['first_completions'] += 1
            
            elif event['event_type'] == 'message':
                if event['data'].get('from') and event['data']['from'] != 'system':
                    metrics[event['data']['from']]['messages_sent'] += 1
                    # Check if it's a request
                    content = event['data'].get('content', '').lower()
                    if any(word in content for word in ['need', 'require', 'please', 'could']):
                        metrics[event['data']['from']]['requests_made'] += 1
            
            elif event['event_type'] == 'information_exchange':
                from_agent = event['data']['from_agent']
                to_agent = event['data']['to_agent']
                info_count = len(event['data']['information'])
                metrics[from_agent]['info_shared'] += info_count
                metrics[to_agent]['info_received'] += info_count
                metrics[from_agent]['requests_fulfilled'] += 1
        
        return dict(metrics)
    
    def _extract_cooperation_metrics(self, events: List[Dict]) -> Dict:
        """Extract cooperation-related metrics"""
        cooperation_scores = defaultdict(dict)
        
        for event in events:
            if event['event_type'] == 'cooperation_evaluation':
                evaluator = event['data']['evaluator']
                for target, score in event['data']['scores'].items():
                    if target != 'self':
                        cooperation_scores[evaluator][target] = score
        
        return dict(cooperation_scores)
    
    def _extract_information_metrics(self, events: List[Dict]) -> Dict:
        """Extract information flow metrics"""
        info_flows = defaultdict(lambda: defaultdict(list))
        info_timing = []
        
        for event in events:
            if event['event_type'] == 'information_exchange':
                from_agent = event['data']['from_agent']
                to_agent = event['data']['to_agent']
                round_num = event['data'].get('round', 0)
                info_pieces = event['data']['information']
                
                info_flows[from_agent][to_agent].append(len(info_pieces))
                info_timing.append({
                    'round': round_num,
                    'from': from_agent,
                    'to': to_agent,
                    'count': len(info_pieces)
                })
        
        return {
            'flows': dict(info_flows),
            'timing': info_timing
        }
    
    def _extract_temporal_metrics(self, events: List[Dict]) -> Dict:
        """Extract round-by-round metrics"""
        round_metrics = defaultdict(lambda: {
            'tasks_completed': 0,
            'messages_sent': 0,
            'info_exchanged': 0,
            'active_agents': set()
        })
        
        current_round = 1  # Track current round
        
        for event in events:
            # Update round tracking
            if event['event_type'] == 'round_start':
                current_round = event.get('data', {}).get('round', current_round)
            
            # Use explicit round or current round
            round_num = event.get('data', {}).get('round', current_round)
            
            if round_num > 0:
                if event['event_type'] == 'task_completion' and event['data'].get('success'):
                    round_metrics[round_num]['tasks_completed'] += 1
                    agent_id = event['data'].get('agent_id')
                    if agent_id:
                        round_metrics[round_num]['active_agents'].add(agent_id)
                elif event['event_type'] == 'message':
                    round_metrics[round_num]['messages_sent'] += 1
                    from_agent = event['data'].get('from')
                    if from_agent and from_agent != 'system':
                        round_metrics[round_num]['active_agents'].add(from_agent)
                elif event['event_type'] == 'information_exchange':
                    round_metrics[round_num]['info_exchanged'] += 1
                    from_agent = event['data'].get('from_agent')
                    to_agent = event['data'].get('to_agent')
                    if from_agent:
                        round_metrics[round_num]['active_agents'].add(from_agent)
                    if to_agent:
                        round_metrics[round_num]['active_agents'].add(to_agent)
                elif event['event_type'] == 'agent_action':
                    # Track agent activity
                    agent_id = event['data'].get('agent_id')
                    if agent_id:
                        round_metrics[round_num]['active_agents'].add(agent_id)
        
        # Convert sets to counts
        for round_num in round_metrics:
            round_metrics[round_num]['active_agents'] = len(round_metrics[round_num]['active_agents'])
        
        return dict(round_metrics)
    
    def _analyze_strategy_effectiveness(self) -> Dict:
        """Analyze which strategies are most effective"""
        strategies = {
            'aggressive': [],  # High message rate, many requests
            'collaborative': [],  # High info sharing rate
            'selective': [],  # Moderate sharing, strategic timing
            'passive': []  # Low activity overall
        }
        
        for sim in self.simulations:
            for agent, metrics in sim['agent_metrics'].items():
                # Classify strategy
                msg_rate = metrics['messages_sent'] / max(1, sim['total_tasks'])
                share_rate = metrics['info_shared'] / max(1, metrics['requests_made'] + metrics['requests_fulfilled'])
                
                if msg_rate > 2 and metrics['requests_made'] > 5:
                    strategy = 'aggressive'
                elif share_rate > 0.7:
                    strategy = 'collaborative'
                elif 0.3 <= share_rate <= 0.7:
                    strategy = 'selective'
                else:
                    strategy = 'passive'
                
                # Record performance
                final_score = sim['final_rankings'].get(agent, 0)
                strategies[strategy].append({
                    'agent': agent,
                    'score': final_score,
                    'efficiency': final_score / max(1, metrics['messages_sent']),
                    'tasks': metrics['tasks_completed']
                })
        
        # Calculate effectiveness metrics
        effectiveness = {}
        for strategy, performances in strategies.items():
            if performances:
                scores = [p['score'] for p in performances]
                # Calculate win rate
                wins = 0
                for p in performances:
                    agent = p['agent']
                    # Find the simulation this performance is from
                    for sim in self.simulations:
                        if agent in sim['final_rankings'] and sim['final_rankings'][agent] == p['score']:
                            # Check if this agent won this simulation
                            if p['score'] == max(sim['final_rankings'].values()):
                                wins += 1
                            break
                
                effectiveness[strategy] = {
                    'count': len(performances),
                    'avg_score': np.mean(scores),
                    'std_score': np.std(scores),
                    'max_score': max(scores),
                    'win_rate': wins / len(performances) if performances else 0,
                    'avg_efficiency': np.mean([p['efficiency'] for p in performances])
                }
        
        return effectiveness
    
    def _analyze_performance_patterns(self) -> Dict:
        """Identify patterns in high vs low performers"""
        all_performances = []
        
        for sim in self.simulations:
            rankings = sim['final_rankings']
            if not rankings:
                continue
                
            sorted_agents = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
            total_agents = len(sorted_agents)
            
            for rank, (agent, score) in enumerate(sorted_agents, 1):
                metrics = sim['agent_metrics'].get(agent, {})
                performance_tier = 'top' if rank <= total_agents * 0.25 else 'bottom' if rank >= total_agents * 0.75 else 'middle'
                
                all_performances.append({
                    'tier': performance_tier,
                    'score': score,
                    'normalized_rank': rank / total_agents,
                    'tasks_completed': metrics.get('tasks_completed', 0),
                    'info_shared': metrics.get('info_shared', 0),
                    'info_received': metrics.get('info_received', 0),
                    'messages_sent': metrics.get('messages_sent', 0),
                    'first_completions': metrics.get('first_completions', 0),
                    'share_ratio': metrics.get('info_shared', 0) / max(1, metrics.get('info_received', 1)),
                    'efficiency': score / max(1, metrics.get('messages_sent', 1))
                })
        
        # Analyze patterns by tier
        patterns = {}
        for tier in ['top', 'middle', 'bottom']:
            tier_data = [p for p in all_performances if p['tier'] == tier]
            if tier_data:
                patterns[tier] = {
                    'count': len(tier_data),
                    'avg_score': np.mean([p['score'] for p in tier_data]),
                    'avg_tasks': np.mean([p['tasks_completed'] for p in tier_data]),
                    'avg_first_completions': np.mean([p['first_completions'] for p in tier_data]),
                    'avg_share_ratio': np.mean([p['share_ratio'] for p in tier_data]),
                    'avg_efficiency': np.mean([p['efficiency'] for p in tier_data]),
                    'avg_messages': np.mean([p['messages_sent'] for p in tier_data])
                }
        
        # Identify key differentiators
        if 'top' in patterns and 'bottom' in patterns:
            patterns['key_differentiators'] = {
                'task_completion_gap': patterns['top']['avg_tasks'] - patterns['bottom']['avg_tasks'],
                'efficiency_gap': patterns['top']['avg_efficiency'] - patterns['bottom']['avg_efficiency'],
                'first_mover_advantage': patterns['top']['avg_first_completions'] - patterns['bottom']['avg_first_completions'],
                'sharing_difference': patterns['top']['avg_share_ratio'] - patterns['bottom']['avg_share_ratio']
            }
        
        return patterns
    
    def _analyze_information_economics(self) -> Dict:
        """Analyze the economics of information sharing"""
        sharing_outcomes = []
        hoarding_outcomes = []
        
        for sim in self.simulations:
            for agent, metrics in sim['agent_metrics'].items():
                share_rate = metrics['info_shared'] / max(1, metrics['info_received'] + metrics['info_shared'])
                final_score = sim['final_rankings'].get(agent, 0)
                
                if share_rate > 0.6:
                    sharing_outcomes.append({
                        'agent': agent,
                        'share_rate': share_rate,
                        'score': final_score,
                        'roi': final_score / max(1, metrics['info_shared'])
                    })
                elif share_rate < 0.3:
                    hoarding_outcomes.append({
                        'agent': agent,
                        'share_rate': share_rate,
                        'score': final_score,
                        'kept_info': metrics['info_received'] - metrics['info_shared']
                    })
        
        # Calculate ROI of different approaches
        info_economics = {
            'sharing_strategy': {
                'count': len(sharing_outcomes),
                'avg_score': np.mean([s['score'] for s in sharing_outcomes]) if sharing_outcomes else 0,
                'avg_roi': np.mean([s['roi'] for s in sharing_outcomes]) if sharing_outcomes else 0
            },
            'hoarding_strategy': {
                'count': len(hoarding_outcomes),
                'avg_score': np.mean([h['score'] for h in hoarding_outcomes]) if hoarding_outcomes else 0,
                'avg_kept': np.mean([h['kept_info'] for h in hoarding_outcomes]) if hoarding_outcomes else 0
            }
        }
        
        # Optimal sharing threshold analysis
        all_share_rates = []
        all_scores = []
        
        for sim in self.simulations:
            for agent, metrics in sim['agent_metrics'].items():
                if metrics['info_received'] + metrics['info_shared'] > 0:
                    share_rate = metrics['info_shared'] / (metrics['info_received'] + metrics['info_shared'])
                    all_share_rates.append(share_rate)
                    all_scores.append(sim['final_rankings'].get(agent, 0))
        
        if len(all_share_rates) > 10:
            # Find optimal sharing rate
            correlation, p_value = stats.pearsonr(all_share_rates, all_scores)
            
            # Bin sharing rates to find sweet spot
            bins = np.linspace(0, 1, 6)
            binned_scores = []
            bin_labels = []
            
            for i in range(len(bins) - 1):
                mask = (np.array(all_share_rates) >= bins[i]) & (np.array(all_share_rates) < bins[i+1])
                bin_scores = [s for s, m in zip(all_scores, mask) if m]
                if bin_scores:
                    binned_scores.append(np.mean(bin_scores))
                    bin_labels.append(f"{bins[i]:.1f}-{bins[i+1]:.1f}")
            
            if binned_scores:
                optimal_bin_idx = np.argmax(binned_scores)
                info_economics['optimal_sharing'] = {
                    'range': bin_labels[optimal_bin_idx],
                    'avg_score': binned_scores[optimal_bin_idx],
                    'correlation': correlation,
                    'p_value': p_value
                }
        
        return info_economics
    
    def _analyze_behavioral_correlations(self) -> Dict:
        """Find correlations between behaviors and outcomes"""
        # Collect all agent data across simulations
        agent_data = []
        
        for sim in self.simulations:
            for agent, metrics in sim['agent_metrics'].items():
                agent_data.append({
                    'score': sim['final_rankings'].get(agent, 0),
                    'tasks': metrics['tasks_completed'],
                    'messages': metrics['messages_sent'],
                    'info_shared': metrics['info_shared'],
                    'info_received': metrics['info_received'],
                    'first_completions': metrics['first_completions'],
                    'requests_made': metrics['requests_made'],
                    'requests_fulfilled': metrics['requests_fulfilled']
                })
        
        if len(agent_data) < 10:
            return {}
        
        # Calculate correlations
        correlations = {}
        score_values = [d['score'] for d in agent_data]
        
        for metric in ['tasks', 'messages', 'info_shared', 'info_received', 'first_completions', 'requests_fulfilled']:
            metric_values = [d[metric] for d in agent_data]
            if len(set(metric_values)) > 1:  # Avoid constant values
                r, p = stats.pearsonr(metric_values, score_values)
                correlations[metric] = {
                    'correlation': r,
                    'p_value': p,
                    'significant': p < 0.05,
                    'strength': 'strong' if abs(r) > 0.7 else 'moderate' if abs(r) > 0.4 else 'weak'
                }
        
        # Identify most impactful behaviors
        significant_correlations = [
            (metric, data['correlation']) 
            for metric, data in correlations.items() 
            if data['significant']
        ]
        significant_correlations.sort(key=lambda x: abs(x[1]), reverse=True)
        
        correlations['most_impactful'] = significant_correlations[:3] if significant_correlations else []
        
        return correlations
    
    def _analyze_temporal_dynamics(self) -> Dict:
        """Analyze how dynamics change over rounds"""
        # Aggregate round metrics across simulations
        round_aggregates = defaultdict(lambda: {
            'tasks': [],
            'messages': [],
            'info_exchanges': [],
            'active_agents': []
        })
        
        for sim in self.simulations:
            for round_num, metrics in sim['temporal_metrics'].items():
                round_aggregates[round_num]['tasks'].append(metrics['tasks_completed'])
                round_aggregates[round_num]['messages'].append(metrics['messages_sent'])
                round_aggregates[round_num]['info_exchanges'].append(metrics['info_exchanged'])
                round_aggregates[round_num]['active_agents'].append(metrics['active_agents'])
        
        # Calculate trends
        temporal_dynamics = {
            'round_metrics': {},
            'trends': {}
        }
        
        rounds = sorted(round_aggregates.keys())
        for round_num in rounds:
            data = round_aggregates[round_num]
            temporal_dynamics['round_metrics'][round_num] = {
                'avg_tasks': np.mean(data['tasks']) if data['tasks'] else 0,
                'avg_messages': np.mean(data['messages']) if data['messages'] else 0,
                'avg_info_exchanges': np.mean(data['info_exchanges']) if data['info_exchanges'] else 0,
                'avg_active_agents': np.mean(data['active_agents']) if data['active_agents'] else 0
            }
        
        # Identify phases
        if len(rounds) >= 3:
            early_rounds = rounds[:len(rounds)//3]
            mid_rounds = rounds[len(rounds)//3:2*len(rounds)//3]
            late_rounds = rounds[2*len(rounds)//3:]
            
            temporal_dynamics['phases'] = {
                'early_game': {
                    'rounds': early_rounds,
                    'avg_activity': np.mean([
                        temporal_dynamics['round_metrics'][r]['avg_messages'] 
                        for r in early_rounds
                    ])
                },
                'mid_game': {
                    'rounds': mid_rounds,
                    'avg_activity': np.mean([
                        temporal_dynamics['round_metrics'][r]['avg_messages'] 
                        for r in mid_rounds
                    ])
                },
                'late_game': {
                    'rounds': late_rounds,
                    'avg_activity': np.mean([
                        temporal_dynamics['round_metrics'][r]['avg_messages'] 
                        for r in late_rounds
                    ])
                }
            }
            
            # Identify acceleration or deceleration
            early_activity = temporal_dynamics['phases']['early_game']['avg_activity']
            late_activity = temporal_dynamics['phases']['late_game']['avg_activity']
            temporal_dynamics['trends']['activity_change'] = (late_activity - early_activity) / max(1, early_activity)
            temporal_dynamics['trends']['pattern'] = 'accelerating' if late_activity > early_activity * 1.2 else 'decelerating' if late_activity < early_activity * 0.8 else 'steady'
        
        return temporal_dynamics
    
    def _perform_statistical_analysis(self) -> Dict:
        """Perform statistical tests for confidence in findings"""
        stats_analysis = {}
        
        # Agent performance differences (ANOVA)
        agent_scores_by_id = defaultdict(list)
        for sim in self.simulations:
            for agent, score in sim['final_rankings'].items():
                agent_scores_by_id[agent].append(score)
        
        # Only test agents present in multiple simulations
        testable_agents = [scores for scores in agent_scores_by_id.values() if len(scores) >= 3]
        
        if len(testable_agents) >= 3:
            f_stat, p_value = stats.f_oneway(*testable_agents)
            stats_analysis['agent_differences'] = {
                'test': 'ANOVA',
                'f_statistic': f_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'interpretation': 'Agents perform significantly differently' if p_value < 0.05 else 'No significant differences between agents'
            }
        
        # Strategy effectiveness (if we have enough data)
        strategy_scores = defaultdict(list)
        for sim in self.simulations:
            for agent, metrics in sim['agent_metrics'].items():
                # Simple strategy classification based on sharing
                share_rate = metrics['info_shared'] / max(1, metrics['info_received'] + metrics['info_shared'])
                strategy = 'sharer' if share_rate > 0.5 else 'hoarder'
                strategy_scores[strategy].append(sim['final_rankings'].get(agent, 0))
        
        if all(len(scores) >= 5 for scores in strategy_scores.values()) and len(strategy_scores) == 2:
            t_stat, p_value = stats.ttest_ind(strategy_scores['sharer'], strategy_scores['hoarder'])
            stats_analysis['strategy_comparison'] = {
                'test': 't-test',
                'sharer_mean': np.mean(strategy_scores['sharer']),
                'hoarder_mean': np.mean(strategy_scores['hoarder']),
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'better_strategy': 'sharer' if np.mean(strategy_scores['sharer']) > np.mean(strategy_scores['hoarder']) else 'hoarder'
            }
        
        return stats_analysis
    
    def _generate_key_insights(self) -> List[Dict]:
        """Generate actionable insights from the analysis"""
        insights = []
        
        # Insight 1: Most effective strategy
        if hasattr(self, '_strategy_effectiveness_cache') and self._strategy_effectiveness_cache:
            strategies = self._strategy_effectiveness_cache
            if strategies:
                best_strategy = max(strategies.items(), key=lambda x: x[1].get('avg_score', 0))
                insights.append({
                    'category': 'Strategy',
                    'finding': f"{best_strategy[0].capitalize()} strategy most effective",
                    'evidence': f"Average score: {best_strategy[1]['avg_score']:.1f}",
                    'confidence': 'high' if best_strategy[1].get('count', 0) > 10 else 'medium'
                })
        
        # Insight 2: Key performance driver
        if hasattr(self, '_behavioral_correlations_cache'):
            correlations = self._behavioral_correlations_cache
            if correlations.get('most_impactful'):
                top_driver = correlations['most_impactful'][0]
                insights.append({
                    'category': 'Performance Driver',
                    'finding': f"{top_driver[0].replace('_', ' ').title()} strongly predicts success",
                    'evidence': f"Correlation: {top_driver[1]:.3f}",
                    'confidence': 'high' if abs(top_driver[1]) > 0.7 else 'medium'
                })
        
        # Insight 3: Information sharing optimum
        if hasattr(self, '_information_economics_cache'):
            info_econ = self._information_economics_cache
            if 'optimal_sharing' in info_econ:
                insights.append({
                    'category': 'Information Strategy',
                    'finding': f"Optimal sharing rate: {info_econ['optimal_sharing']['range']}",
                    'evidence': f"Peak average score: {info_econ['optimal_sharing']['avg_score']:.1f}",
                    'confidence': 'high' if info_econ['optimal_sharing']['p_value'] < 0.05 else 'medium'
                })
        
        # Insight 4: Temporal pattern
        if hasattr(self, '_temporal_dynamics_cache'):
            temporal = self._temporal_dynamics_cache
            if 'trends' in temporal and 'pattern' in temporal['trends']:
                insights.append({
                    'category': 'Game Dynamics',
                    'finding': f"Activity pattern: {temporal['trends']['pattern']}",
                    'evidence': f"Change: {temporal['trends']['activity_change']*100:.1f}%",
                    'confidence': 'high'
                })
        
        return insights


def process_batch_data(batch_dir: str) -> Dict[str, Any]:
    """Main entry point for batch processing"""
    try:
        processor = EnhancedBatchProcessor(batch_dir)
        results = processor.process()
        
        # Cache intermediate results for insights generation
        processor._strategy_effectiveness_cache = results.get('strategy_effectiveness', {})
        processor._behavioral_correlations_cache = results.get('behavioral_correlations', {})
        processor._information_economics_cache = results.get('information_economics', {})
        processor._temporal_dynamics_cache = results.get('temporal_dynamics', {})
        
        # Regenerate insights with cached data
        results['key_insights'] = processor._generate_key_insights()
        
        # Add enhanced analysis (pass simulations list)
        results['simulations'] = processor.simulations
        enhancements = enhance_batch_analysis(results)
        results.update(enhancements)
        
        # Convert all numpy types to native Python types for JSON serialization
        return convert_to_native_types(results)
    except Exception as e:
        # Return minimal data on error
        return convert_to_native_types({
            'batch_id': Path(batch_dir).name,
            'num_simulations': 0,
            'error': str(e),
            'config': {'simulation': {'agents': 10, 'rounds': 10}},
            'key_insights': [],
            'strategy_effectiveness': {},
            'performance_patterns': {},
            'information_economics': {},
            'behavioral_correlations': {},
            'temporal_dynamics': {},
            'statistical_analysis': {}
        })
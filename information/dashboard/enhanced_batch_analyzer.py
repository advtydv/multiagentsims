"""
Enhanced Batch Analyzer - Advanced metrics and strategic recommendations
"""

import numpy as np
import statistics
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from scipy import stats
import json


class SimulationVarianceAnalyzer:
    """Analyze variance across simulations to identify stable vs volatile patterns"""
    
    def __init__(self, simulations: List[Dict]):
        self.simulations = simulations
        
    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive variance analysis"""
        return {
            'outcome_stability': self._analyze_outcome_stability(),
            'agent_consistency': self._analyze_agent_consistency(),
            'strategy_robustness': self._analyze_strategy_robustness(),
            'environmental_sensitivity': self._analyze_environmental_sensitivity()
        }
    
    def _analyze_outcome_stability(self) -> Dict:
        """How stable are overall outcomes across simulations?"""
        # Extract key metrics from each simulation
        total_tasks = []
        winner_diversity = defaultdict(int)
        score_spreads = []
        
        for sim in self.simulations:
            # Total tasks completed
            total_tasks.append(sim.get('total_tasks', 0))
            
            # Winner tracking
            rankings = sim.get('final_rankings', {})
            if rankings:
                winner = max(rankings.items(), key=lambda x: x[1])[0]
                winner_diversity[winner] += 1
                
                # Score spread (difference between top and bottom)
                scores = list(rankings.values())
                if scores:
                    score_spreads.append(max(scores) - min(scores))
        
        # Calculate stability metrics
        stability = {
            'task_completion': {
                'mean': np.mean(total_tasks) if total_tasks else 0,
                'cv': np.std(total_tasks) / np.mean(total_tasks) if total_tasks and np.mean(total_tasks) > 0 else 0,
                'stable': np.std(total_tasks) / np.mean(total_tasks) < 0.2 if total_tasks and np.mean(total_tasks) > 0 else False
            },
            'winner_concentration': {
                'unique_winners': len(winner_diversity),
                'dominant_winner': max(winner_diversity.items(), key=lambda x: x[1]) if winner_diversity else (None, 0),
                'entropy': self._calculate_entropy(list(winner_diversity.values()))
            },
            'competition_intensity': {
                'mean_spread': np.mean(score_spreads) if score_spreads else 0,
                'spread_variance': np.var(score_spreads) if score_spreads else 0
            }
        }
        
        return stability
    
    def _analyze_agent_consistency(self) -> Dict:
        """How consistently do agents perform across simulations?"""
        agent_performances = defaultdict(list)
        agent_ranks = defaultdict(list)
        
        for sim in self.simulations:
            rankings = sim.get('final_rankings', {})
            if rankings:
                sorted_agents = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
                for rank, (agent, score) in enumerate(sorted_agents, 1):
                    agent_performances[agent].append(score)
                    agent_ranks[agent].append(rank)
        
        consistency = {}
        for agent in agent_performances:
            scores = agent_performances[agent]
            ranks = agent_ranks[agent]
            
            if scores and len(scores) > 1:
                consistency[agent] = {
                    'performance_cv': np.std(scores) / np.mean(scores) if np.mean(scores) > 0 else 0,
                    'rank_stability': np.std(ranks),
                    'reliability': 1 - (np.std(ranks) / len(set(ranks))) if len(set(ranks)) > 0 else 0,
                    'appearances': len(scores),
                    'avg_score': np.mean(scores),
                    'avg_rank': np.mean(ranks)
                }
        
        # Identify most and least consistent
        if consistency:
            sorted_by_cv = sorted(consistency.items(), key=lambda x: x[1]['performance_cv'])
            return {
                'agent_metrics': consistency,
                'most_consistent': sorted_by_cv[0][0] if sorted_by_cv else None,
                'least_consistent': sorted_by_cv[-1][0] if sorted_by_cv else None,
                'overall_consistency': np.mean([c['performance_cv'] for c in consistency.values()])
            }
        
        return {}
    
    def _analyze_strategy_robustness(self) -> Dict:
        """Which strategies work consistently vs situationally?"""
        strategy_outcomes = defaultdict(list)
        
        for sim in self.simulations:
            # Classify strategies based on agent metrics
            agent_metrics = sim.get('agent_metrics', {})
            for agent, metrics in agent_metrics.items():
                # Classify strategy
                if metrics.get('info_shared', 0) > metrics.get('info_received', 0):
                    strategy = 'generous'
                elif metrics.get('info_shared', 0) < metrics.get('info_received', 0) * 0.5:
                    strategy = 'selfish'
                else:
                    strategy = 'balanced'
                
                score = sim.get('final_rankings', {}).get(agent, 0)
                strategy_outcomes[strategy].append(score)
        
        robustness = {}
        for strategy, outcomes in strategy_outcomes.items():
            if outcomes and len(outcomes) > 1:
                robustness[strategy] = {
                    'mean_outcome': np.mean(outcomes),
                    'consistency': 1 - (np.std(outcomes) / np.mean(outcomes)) if np.mean(outcomes) > 0 else 0,
                    'min_outcome': min(outcomes),
                    'max_outcome': max(outcomes),
                    'sample_size': len(outcomes),
                    'robustness_score': np.mean(outcomes) * (1 - np.std(outcomes) / np.mean(outcomes)) if np.mean(outcomes) > 0 else 0
                }
        
        return robustness
    
    def _analyze_environmental_sensitivity(self) -> Dict:
        """How sensitive are outcomes to initial conditions?"""
        # Analyze how small differences lead to different outcomes
        first_mover_impacts = []
        early_alliance_impacts = []
        
        for sim in self.simulations:
            agent_metrics = sim.get('agent_metrics', {})
            rankings = sim.get('final_rankings', {})
            
            if agent_metrics and rankings:
                # Correlate first completions with final score
                for agent, metrics in agent_metrics.items():
                    if agent in rankings:
                        first_completions = metrics.get('first_completions', 0)
                        final_score = rankings[agent]
                        first_mover_impacts.append((first_completions, final_score))
        
        # Calculate sensitivities
        sensitivity = {
            'first_mover_correlation': 0,
            'early_game_importance': 0
        }
        
        if first_mover_impacts:
            x, y = zip(*first_mover_impacts)
            if len(set(x)) > 1:  # Need variance in x
                correlation, p_value = stats.pearsonr(x, y)
                sensitivity['first_mover_correlation'] = correlation
                sensitivity['first_mover_significance'] = p_value < 0.05
        
        return sensitivity
    
    def _calculate_entropy(self, values: List[int]) -> float:
        """Calculate Shannon entropy for diversity measurement"""
        if not values:
            return 0
        total = sum(values)
        if total == 0:
            return 0
        probs = [v/total for v in values]
        return -sum(p * np.log2(p) for p in probs if p > 0)


class AgentTrajectoryTracker:
    """Track and analyze agent performance trajectories"""
    
    def __init__(self, simulations: List[Dict]):
        self.simulations = simulations
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze agent trajectories across simulations"""
        return {
            'trajectory_patterns': self._identify_trajectory_patterns(),
            'momentum_analysis': self._analyze_momentum(),
            'turning_points': self._identify_turning_points()
        }
    
    def _identify_trajectory_patterns(self) -> Dict:
        """Identify common trajectory patterns (steady, volatile, improving, declining)"""
        agent_trajectories = defaultdict(list)
        
        # Collect score progressions for each agent
        for sim in self.simulations:
            rankings = sim.get('final_rankings', {})
            for agent, score in rankings.items():
                agent_trajectories[agent].append(score)
        
        patterns = {}
        for agent, scores in agent_trajectories.items():
            if len(scores) >= 3:
                # Calculate trajectory metrics
                trend = np.polyfit(range(len(scores)), scores, 1)[0] if len(scores) > 1 else 0
                volatility = np.std(scores) / np.mean(scores) if np.mean(scores) > 0 else 0
                
                # Classify pattern
                if abs(trend) < 0.5 and volatility < 0.2:
                    pattern = 'steady'
                elif trend > 1:
                    pattern = 'improving'
                elif trend < -1:
                    pattern = 'declining'
                else:
                    pattern = 'volatile'
                
                patterns[agent] = {
                    'pattern': pattern,
                    'trend': trend,
                    'volatility': volatility,
                    'scores': scores
                }
        
        return patterns
    
    def _analyze_momentum(self) -> Dict:
        """Analyze if success breeds success (momentum effects)"""
        momentum_data = []
        
        # Look at consecutive simulation pairs
        for i in range(len(self.simulations) - 1):
            sim1 = self.simulations[i]
            sim2 = self.simulations[i + 1]
            
            rankings1 = sim1.get('final_rankings', {})
            rankings2 = sim2.get('final_rankings', {})
            
            # Find common agents
            common_agents = set(rankings1.keys()) & set(rankings2.keys())
            
            for agent in common_agents:
                score1 = rankings1[agent]
                score2 = rankings2[agent]
                momentum_data.append((score1, score2))
        
        # Calculate momentum correlation
        if momentum_data:
            prev_scores, next_scores = zip(*momentum_data)
            if len(set(prev_scores)) > 1:
                correlation, p_value = stats.pearsonr(prev_scores, next_scores)
                return {
                    'momentum_correlation': correlation,
                    'significant': p_value < 0.05,
                    'interpretation': 'Strong momentum' if correlation > 0.5 else 'Weak momentum'
                }
        
        return {'momentum_correlation': 0, 'significant': False}
    
    def _identify_turning_points(self) -> List[Dict]:
        """Identify critical moments where trajectories change"""
        turning_points = []
        
        # This would require round-by-round data
        # For now, identify major rank changes between simulations
        for i in range(len(self.simulations) - 1):
            rankings1 = self.simulations[i].get('final_rankings', {})
            rankings2 = self.simulations[i + 1].get('final_rankings', {})
            
            if rankings1 and rankings2:
                # Calculate rank changes
                ranks1 = {agent: rank for rank, (agent, _) in enumerate(
                    sorted(rankings1.items(), key=lambda x: x[1], reverse=True), 1
                )}
                ranks2 = {agent: rank for rank, (agent, _) in enumerate(
                    sorted(rankings2.items(), key=lambda x: x[1], reverse=True), 1
                )}
                
                for agent in set(ranks1.keys()) & set(ranks2.keys()):
                    rank_change = ranks2[agent] - ranks1[agent]
                    if abs(rank_change) >= 3:  # Major rank change
                        turning_points.append({
                            'simulation_pair': (i, i+1),
                            'agent': agent,
                            'rank_change': rank_change,
                            'direction': 'rise' if rank_change < 0 else 'fall'
                        })
        
        return turning_points


class StrategicRecommendationEngine:
    """Generate actionable strategic recommendations based on analysis"""
    
    def __init__(self, batch_data: Dict):
        self.data = batch_data
    
    def generate_recommendations(self) -> List[Dict]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Recommendation 1: Optimal Strategy
        if self.data.get('strategy_effectiveness'):
            best_strategy = max(
                self.data['strategy_effectiveness'].items(),
                key=lambda x: x[1].get('avg_score', 0)
            )
            if best_strategy[1].get('count', 0) >= 5:
                recommendations.append({
                    'priority': 'high',
                    'category': 'Strategy Selection',
                    'recommendation': f"Adopt {best_strategy[0]} strategy",
                    'rationale': f"Achieves {best_strategy[1]['avg_score']:.1f} average score with {best_strategy[1].get('win_rate', 0)*100:.1f}% win rate",
                    'confidence': 0.8 if best_strategy[1].get('count', 0) > 10 else 0.6
                })
        
        # Recommendation 2: Key Behaviors
        if self.data.get('behavioral_correlations', {}).get('most_impactful'):
            top_behavior = self.data['behavioral_correlations']['most_impactful'][0]
            recommendations.append({
                'priority': 'high',
                'category': 'Behavioral Focus',
                'recommendation': f"Prioritize {top_behavior[0].replace('_', ' ')}",
                'rationale': f"Shows strong correlation (r={top_behavior[1]:.3f}) with success",
                'confidence': 0.9 if abs(top_behavior[1]) > 0.7 else 0.7
            })
        
        # Recommendation 3: Information Strategy
        if self.data.get('information_economics', {}).get('optimal_sharing'):
            optimal = self.data['information_economics']['optimal_sharing']
            recommendations.append({
                'priority': 'medium',
                'category': 'Information Management',
                'recommendation': f"Maintain sharing rate between {optimal['range']}",
                'rationale': f"Optimal range yields {optimal['avg_score']:.1f} average score",
                'confidence': 0.7 if optimal.get('p_value', 1) < 0.05 else 0.5
            })
        
        # Recommendation 4: Timing Strategy
        if self.data.get('temporal_dynamics', {}).get('trends'):
            pattern = self.data['temporal_dynamics']['trends'].get('pattern')
            if pattern == 'accelerating':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'Timing',
                    'recommendation': "Focus efforts on late game",
                    'rationale': "Activity and success accelerate in later rounds",
                    'confidence': 0.6
                })
            elif pattern == 'decelerating':
                recommendations.append({
                    'priority': 'high',
                    'category': 'Timing',
                    'recommendation': "Establish early advantage",
                    'rationale': "Early game performance determines outcomes",
                    'confidence': 0.7
                })
        
        # Recommendation 5: Risk Management
        if self.data.get('performance_patterns', {}).get('key_differentiators'):
            diff = self.data['performance_patterns']['key_differentiators']
            if diff.get('first_mover_advantage', 0) > 2:
                recommendations.append({
                    'priority': 'high',
                    'category': 'Risk Strategy',
                    'recommendation': "Pursue aggressive early task completion",
                    'rationale': f"First movers gain {diff['first_mover_advantage']:.1f} task advantage",
                    'confidence': 0.8
                })
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}[x['priority']],
            x['confidence']
        ), reverse=True)
        
        return recommendations


def enhance_batch_analysis(batch_data: Dict) -> Dict:
    """Add advanced analysis to existing batch data"""
    
    # Extract simulations list from batch data
    simulations = batch_data.get('simulations', [])
    
    if not simulations:
        # Try to reconstruct from other data
        simulations = []
        # This would need actual simulation data
    
    # Initialize analyzers
    variance_analyzer = SimulationVarianceAnalyzer(simulations)
    trajectory_tracker = AgentTrajectoryTracker(simulations)
    recommendation_engine = StrategicRecommendationEngine(batch_data)
    
    # Perform analyses
    enhancements = {
        'variance_analysis': variance_analyzer.analyze() if simulations else {},
        'agent_trajectories': trajectory_tracker.analyze() if simulations else {},
        'strategic_recommendations': recommendation_engine.generate_recommendations(),
        'meta_insights': generate_meta_insights(batch_data)
    }
    
    return enhancements


def generate_meta_insights(batch_data: Dict) -> Dict:
    """Generate high-level meta insights"""
    insights = {
        'simulation_quality': assess_simulation_quality(batch_data),
        'strategic_diversity': assess_strategic_diversity(batch_data),
        'competitive_dynamics': assess_competitive_dynamics(batch_data)
    }
    
    return insights


def assess_simulation_quality(batch_data: Dict) -> Dict:
    """Assess the quality and reliability of simulation results"""
    num_sims = batch_data.get('num_simulations', 0)
    
    quality = {
        'sample_size': num_sims,
        'statistical_power': 'high' if num_sims >= 30 else 'medium' if num_sims >= 10 else 'low',
        'confidence_level': min(0.95, 0.5 + num_sims * 0.015)  # Scales with sample size
    }
    
    # Check for statistical significance in key findings
    if batch_data.get('statistical_analysis'):
        sig_tests = sum(1 for test in batch_data['statistical_analysis'].values() 
                       if isinstance(test, dict) and test.get('significant'))
        total_tests = len(batch_data['statistical_analysis'])
        quality['findings_reliability'] = sig_tests / total_tests if total_tests > 0 else 0
    
    return quality


def assess_strategic_diversity(batch_data: Dict) -> Dict:
    """Assess the diversity of strategies employed"""
    strategies = batch_data.get('strategy_effectiveness', {})
    
    diversity = {
        'num_strategies': len(strategies),
        'strategy_balance': 0,
        'dominant_strategy': None
    }
    
    if strategies:
        counts = [s.get('count', 0) for s in strategies.values()]
        if counts:
            # Calculate entropy for balance
            total = sum(counts)
            if total > 0:
                probs = [c/total for c in counts]
                entropy = -sum(p * np.log2(p) for p in probs if p > 0)
                max_entropy = np.log2(len(strategies))
                diversity['strategy_balance'] = entropy / max_entropy if max_entropy > 0 else 0
        
        # Find dominant strategy
        dominant = max(strategies.items(), key=lambda x: x[1].get('count', 0))
        diversity['dominant_strategy'] = dominant[0]
    
    return diversity


def assess_competitive_dynamics(batch_data: Dict) -> Dict:
    """Assess the competitive dynamics of the simulations"""
    patterns = batch_data.get('performance_patterns', {})
    
    dynamics = {
        'competition_intensity': 'unknown',
        'winner_predictability': 'unknown',
        'performance_gaps': 'unknown'
    }
    
    # Assess based on tier differences
    if patterns:
        top = patterns.get('top', {})
        bottom = patterns.get('bottom', {})
        
        if top and bottom:
            score_gap = top.get('avg_score', 0) - bottom.get('avg_score', 0)
            
            # Competition intensity
            if score_gap < 5:
                dynamics['competition_intensity'] = 'very_high'
            elif score_gap < 10:
                dynamics['competition_intensity'] = 'high'
            elif score_gap < 20:
                dynamics['competition_intensity'] = 'moderate'
            else:
                dynamics['competition_intensity'] = 'low'
            
            dynamics['performance_gaps'] = 'large' if score_gap > 15 else 'small'
    
    return dynamics
"""
Task Performance Analyzer

Analyzes task completion patterns, success rates, and competitive dynamics.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer


class TaskPerformanceAnalyzer(BaseAnalyzer):
    """Analyzes task completion and performance patterns"""
    
    @property
    def name(self) -> str:
        return "Task Performance"
        
    def analyze(self) -> Dict[str, Any]:
        """Perform task performance analysis"""
        # Get task-related data
        completions = self.processor.get_task_completions()
        agent_summary = self.processor.get_agent_summary()
        round_summary = self.processor.get_round_summary()
        
        # Calculate performance metrics
        performance_metrics = self.metrics_calc.calculate_task_performance_metrics(
            completions, agent_summary
        )
        
        # Analyze completion patterns
        completion_patterns = self._analyze_completion_patterns(completions)
        
        # Analyze competitive dynamics
        competitive_analysis = self._analyze_competitive_dynamics(
            completions, agent_summary
        )
        
        # Analyze efficiency
        efficiency_analysis = self._analyze_task_efficiency(
            completions, agent_summary, round_summary
        )
        
        # Task difficulty analysis
        task_analysis = self._analyze_task_characteristics(completions)
        
        results = {
            'performance_metrics': performance_metrics,
            'completion_patterns': completion_patterns,
            'competitive_analysis': competitive_analysis,
            'efficiency_analysis': efficiency_analysis,
            'task_analysis': task_analysis,
            'summary': self._generate_summary(
                performance_metrics, 
                competitive_analysis,
                efficiency_analysis
            )
        }
        
        return results
        
    def get_metrics(self) -> Dict[str, float]:
        """Get key task performance metrics"""
        results = self.get_results()
        
        metrics = {}
        metrics.update(results['performance_metrics'])
        metrics.update(results['efficiency_analysis'])
        
        # Add some competitive metrics
        comp = results['competitive_analysis']
        metrics['first_mover_advantage'] = comp.get('first_mover_advantage', 0.0)
        
        return metrics
        
    def _analyze_completion_patterns(self, completions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in task completion"""
        if len(completions) == 0:
            return {
                'completion_timeline': {},
                'completion_clusters': [],
                'rush_periods': []
            }
            
        # Completion timeline
        timeline = completions.groupby('round').agg({
            'success': ['sum', 'count'],
            'got_bonus': 'sum'
        })
        timeline.columns = ['successful', 'attempted', 'with_bonus']
        timeline['success_rate'] = timeline['successful'] / timeline['attempted']
        
        # Identify completion clusters (rounds with high activity)
        mean_completions = timeline['successful'].mean()
        std_completions = timeline['successful'].std()
        
        clusters = []
        if std_completions > 0:
            high_activity_rounds = timeline[
                timeline['successful'] > mean_completions + std_completions
            ].index.tolist()
            clusters = [int(r) for r in high_activity_rounds]
            
        # Identify rush periods (consecutive rounds with increasing completions)
        rush_periods = []
        if len(timeline) > 1:
            for i in range(1, len(timeline)):
                if i < len(timeline) - 1:
                    if (timeline.iloc[i]['successful'] > timeline.iloc[i-1]['successful'] and
                        timeline.iloc[i+1]['successful'] > timeline.iloc[i]['successful']):
                        rush_periods.append({
                            'start_round': int(timeline.index[i-1]),
                            'peak_round': int(timeline.index[i+1]),
                            'completions': int(timeline.iloc[i-1:i+2]['successful'].sum())
                        })
                        
        return {
            'completion_timeline': timeline.to_dict(),
            'completion_clusters': clusters,
            'rush_periods': rush_periods
        }
        
    def _analyze_competitive_dynamics(
        self, 
        completions: pd.DataFrame,
        agent_summary: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze competitive aspects of task completion"""
        if len(completions) == 0:
            return {
                'first_mover_advantage': 0.0,
                'competition_intensity': 0.0,
                'winner_characteristics': {}
            }
            
        # First mover advantage
        first_completions = completions[completions['got_bonus']]
        if len(first_completions) > 0:
            # Compare performance of agents who got bonuses vs those who didn't
            bonus_agents = first_completions['agent_id'].unique()
            
            bonus_agent_data = agent_summary[agent_summary['agent_id'].isin(bonus_agents)]
            other_agent_data = agent_summary[~agent_summary['agent_id'].isin(bonus_agents)]
            
            if len(bonus_agent_data) > 0 and len(other_agent_data) > 0:
                first_mover_advantage = (
                    bonus_agent_data['tasks_completed'].mean() / 
                    other_agent_data['tasks_completed'].mean()
                ) - 1
            else:
                first_mover_advantage = 0.0
        else:
            first_mover_advantage = 0.0
            
        # Competition intensity (how many agents compete for same tasks)
        task_competition = completions.groupby('task_id')['agent_id'].nunique()
        avg_competitors = task_competition.mean()
        competition_intensity = (avg_competitors - 1) / (len(agent_summary) - 1) if len(agent_summary) > 1 else 0
        
        # Winner characteristics
        top_performers = agent_summary.nlargest(3, 'tasks_completed')
        winner_chars = {
            'avg_messages_sent': top_performers['messages_sent'].mean(),
            'avg_info_shared': top_performers['info_pieces_shared'].mean(),
            'avg_rounds_active': top_performers['rounds_active'].mean(),
            'bonus_capture_rate': (
                top_performers['tasks_with_bonus'].sum() / 
                top_performers['tasks_completed'].sum()
                if top_performers['tasks_completed'].sum() > 0 else 0
            )
        }
        
        return {
            'first_mover_advantage': first_mover_advantage,
            'competition_intensity': competition_intensity,
            'avg_competitors_per_task': avg_competitors,
            'winner_characteristics': winner_chars
        }
        
    def _analyze_task_efficiency(
        self,
        completions: pd.DataFrame,
        agent_summary: pd.DataFrame,
        round_summary: pd.DataFrame
    ) -> Dict[str, float]:
        """Analyze efficiency of task completion"""
        if len(completions) == 0 or len(agent_summary) == 0:
            return {
                'overall_efficiency': 0.0,
                'action_efficiency': 0.0,
                'time_efficiency': 0.0,
                'resource_efficiency': 0.0
            }
            
        # Overall efficiency (tasks completed per round)
        total_rounds = len(round_summary) if len(round_summary) > 0 else 1
        overall_efficiency = len(completions[completions['success']]) / total_rounds
        
        # Action efficiency (successful tasks per total actions)
        total_actions = agent_summary['total_actions'].sum()
        action_efficiency = (
            len(completions[completions['success']]) / total_actions 
            if total_actions > 0 else 0
        )
        
        # Time efficiency (how quickly tasks are completed)
        if 'round' in completions.columns and len(completions) > 0:
            avg_completion_round = completions[completions['success']]['round'].mean()
            time_efficiency = 1 - (avg_completion_round - 1) / (total_rounds - 1) if total_rounds > 1 else 1
        else:
            time_efficiency = 0.0
            
        # Resource efficiency (info pieces received vs tasks completed)
        total_info_received = agent_summary['info_pieces_received'].sum()
        total_tasks_completed = agent_summary['tasks_completed'].sum()
        resource_efficiency = (
            total_tasks_completed / total_info_received 
            if total_info_received > 0 else 0
        )
        
        return {
            'overall_efficiency': overall_efficiency,
            'action_efficiency': action_efficiency,
            'time_efficiency': time_efficiency,
            'resource_efficiency': resource_efficiency
        }
        
    def _analyze_task_characteristics(self, completions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze characteristics of different tasks"""
        if len(completions) == 0:
            return {
                'task_difficulty': {},
                'popular_tasks': [],
                'neglected_tasks': []
            }
            
        # Group by task
        task_stats = completions.groupby('task_id').agg({
            'success': ['sum', 'count', 'mean'],
            'round': ['min', 'mean'],
            'agent_id': 'nunique'
        })
        
        task_stats.columns = [
            'completions', 'attempts', 'success_rate',
            'first_attempt_round', 'avg_completion_round', 'unique_agents'
        ]
        
        # Calculate difficulty (inverse of success rate)
        task_stats['difficulty'] = 1 - task_stats['success_rate']
        
        # Identify popular and neglected tasks
        mean_attempts = task_stats['attempts'].mean()
        popular_tasks = task_stats[
            task_stats['attempts'] > mean_attempts * 1.5
        ].index.tolist()
        
        neglected_tasks = task_stats[
            task_stats['attempts'] < mean_attempts * 0.5
        ].index.tolist()
        
        return {
            'task_difficulty': task_stats['difficulty'].to_dict(),
            'popular_tasks': popular_tasks,
            'neglected_tasks': neglected_tasks,
            'task_stats': task_stats.to_dict()
        }
        
    def _generate_summary(
        self,
        performance_metrics: Dict[str, float],
        competitive_analysis: Dict[str, Any],
        efficiency_analysis: Dict[str, float]
    ) -> str:
        """Generate summary of task performance analysis"""
        summary = f"""
Task performance analysis reveals {performance_metrics['overall_success_rate']:.1%} 
overall success rate with {performance_metrics['bonus_capture_rate']:.1%} of 
possible bonuses captured.

Competitive dynamics show {'strong' if competitive_analysis['first_mover_advantage'] > 0.2 else 'moderate'} 
first-mover advantage ({competitive_analysis['first_mover_advantage']:.1%}) with 
average competition intensity of {competitive_analysis['competition_intensity']:.1%}.

Top performers sent {competitive_analysis['winner_characteristics']['avg_messages_sent']:.1f} 
messages on average and shared {competitive_analysis['winner_characteristics']['avg_info_shared']:.1f} 
information pieces, capturing {competitive_analysis['winner_characteristics']['bonus_capture_rate']:.1%} 
of bonuses.

Efficiency metrics show:
- Overall: {efficiency_analysis['overall_efficiency']:.2f} tasks/round
- Action: {efficiency_analysis['action_efficiency']:.1%} success per action
- Time: {efficiency_analysis['time_efficiency']:.1%} time efficiency
- Resource: {efficiency_analysis['resource_efficiency']:.2f} tasks per info received

Tasks are completed on average in round {performance_metrics['avg_completion_round']:.1f}.
"""
        return summary.strip()
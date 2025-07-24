"""
Scoring system for the simulation
"""

from typing import Dict, List, Any
from collections import defaultdict


class ScoringSystem:
    """Manages agent scores and rankings"""
    
    def __init__(self, config: dict):
        self.config = config
        self.scores = defaultdict(int)
        self.task_completions = defaultdict(list)
        self.round_completions = defaultdict(lambda: defaultdict(int))
        
    def award_points(self, agent_id: str, action_type: str, round_num: int = None, quality_avg: float = None) -> int:
        """Award points to an agent for an action"""
        points = 0
        
        if action_type == 'task_completion':
            base_points = self.config['task_completion']
            
            # Apply quality multiplier if provided
            if quality_avg is not None:
                points = int(base_points * (quality_avg / 100))
            else:
                points = base_points
            
            # Check if agent is first to complete a task this round
            if round_num and self.round_completions[round_num]['total'] == 0:
                bonus = self.config.get('bonus_for_first', 0)
                # Apply quality multiplier to bonus as well
                if quality_avg is not None:
                    bonus = int(bonus * (quality_avg / 100))
                points += bonus
                
            if round_num:
                self.round_completions[round_num]['total'] += 1
                self.round_completions[round_num][agent_id] += 1
                
        self.scores[agent_id] += points
        self.task_completions[agent_id].append({
            'points': points,
            'action': action_type,
            'round': round_num,
            'quality_avg': quality_avg
        })
        
        return points
        
    def get_score(self, agent_id: str) -> int:
        """Get current score for an agent"""
        return self.scores[agent_id]
        
    def get_rankings(self) -> Dict[str, int]:
        """Get current rankings (sorted by score)"""
        # Sort agents by score (descending)
        sorted_agents = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return as ordered dict
        return dict(sorted_agents)
        
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get detailed leaderboard information"""
        rankings = self.get_rankings()
        leaderboard = []
        
        for rank, (agent_id, score) in enumerate(rankings.items(), 1):
            leaderboard.append({
                'rank': rank,
                'agent_id': agent_id,
                'score': score,
                'tasks_completed': len(self.task_completions[agent_id])
            })
            
        return leaderboard
        
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific agent"""
        rankings = self.get_rankings()
        agent_rank = list(rankings.keys()).index(agent_id) + 1 if agent_id in rankings else None
        
        return {
            'agent_id': agent_id,
            'score': self.scores[agent_id],
            'rank': agent_rank,
            'total_agents': len(rankings),
            'tasks_completed': len(self.task_completions[agent_id]),
            'completion_history': self.task_completions[agent_id]
        }
        
    def get_round_stats(self, round_num: int) -> Dict[str, Any]:
        """Get statistics for a specific round"""
        round_data = self.round_completions[round_num]
        
        return {
            'round': round_num,
            'total_completions': round_data['total'],
            'completions_by_agent': {
                agent: count for agent, count in round_data.items() 
                if agent != 'total'
            }
        }
        
    def reset_scores(self):
        """Reset all scores (useful for testing)"""
        self.scores.clear()
        self.task_completions.clear()
        self.round_completions.clear()
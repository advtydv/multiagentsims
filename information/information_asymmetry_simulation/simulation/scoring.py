"""
Revenue tracking system for the simulation
"""

from typing import Dict, List, Any
from collections import defaultdict


class RevenueSystem:
    """Manages agent revenue and revenue board"""
    
    def __init__(self, config: dict):
        self.config = config
        self.revenue = defaultdict(int)  # Track revenue in dollars
        self.task_completions = defaultdict(list)
        self.round_completions = defaultdict(lambda: defaultdict(int))
        
    def award_revenue(self, agent_id: str, action_type: str, round_num: int = None, quality_avg: float = None) -> int:
        """Award revenue to an agent for an action"""
        revenue_earned = 0
        
        if action_type == 'task_completion':
            base_revenue = self.config['task_completion']
            
            # Apply quality multiplier if provided
            if quality_avg is not None:
                revenue_earned = int(base_revenue * (quality_avg / 100))
            else:
                revenue_earned = base_revenue
            
            # Check if agent is first to complete a task this round
            if round_num and self.round_completions[round_num]['total'] == 0:
                bonus = self.config.get('bonus_for_first', 0)
                # Don't apply quality multiplier to bonus - it's a fixed reward for being first
                revenue_earned += bonus
                
            if round_num:
                self.round_completions[round_num]['total'] += 1
                self.round_completions[round_num][agent_id] += 1
                
        self.revenue[agent_id] += revenue_earned
        self.task_completions[agent_id].append({
            'revenue': revenue_earned,
            'action': action_type,
            'round': round_num,
            'quality_avg': quality_avg
        })
        
        return revenue_earned
        
    def get_revenue(self, agent_id: str) -> int:
        """Get current revenue for an agent"""
        return self.revenue[agent_id]
        
    def get_revenue_board(self) -> Dict[str, int]:
        """Get current revenue board (sorted by revenue)"""
        # Sort agents by revenue (descending)
        sorted_agents = sorted(self.revenue.items(), key=lambda x: x[1], reverse=True)
        
        # Return as ordered dict
        return dict(sorted_agents)
        
    def get_revenue_leaderboard(self) -> List[Dict[str, Any]]:
        """Get detailed revenue leaderboard information"""
        revenue_board = self.get_revenue_board()
        leaderboard = []
        
        for position, (agent_id, revenue) in enumerate(revenue_board.items(), 1):
            leaderboard.append({
                'position': position,
                'agent_id': agent_id,
                'revenue': revenue,
                'tasks_completed': len(self.task_completions[agent_id])
            })
            
        return leaderboard
        
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific agent"""
        revenue_board = self.get_revenue_board()
        agent_position = list(revenue_board.keys()).index(agent_id) + 1 if agent_id in revenue_board else None
        
        return {
            'agent_id': agent_id,
            'revenue': self.revenue[agent_id],
            'position': agent_position,
            'total_agents': len(revenue_board),
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
        
    def reset_revenue(self):
        """Reset all revenue (useful for testing)"""
        self.revenue.clear()
        self.task_completions.clear()
        self.round_completions.clear()
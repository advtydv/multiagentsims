from typing import List, Dict, Any, Optional


class Coalition:
    """
    Represents a group of agents with shared resources and distribution rules.
    """
    
    def __init__(self, coalition_id: str, rules: Optional[Dict[str, Any]] = None):
        """
        Initialize a coalition.
        
        Args:
            coalition_id: Unique identifier for the coalition
            rules: Dictionary containing coalition rules and policies
        """
        self.coalition_id = coalition_id
        self.members: List['Agent'] = []
        self.shared_resource_pool: float = 0.0
        
        # Default rules for MVP
        self.rules = rules or {
            "distribution_policy": "EQUAL_SPLIT",
            "contribution_tax_rate": 0.0,  # No automatic tax for MVP
        }
    
    def add_member(self, agent: 'Agent') -> None:
        """
        Add an agent to the coalition.
        
        Args:
            agent: The Agent object to add
        """
        if agent not in self.members:
            self.members.append(agent)
            agent.coalition_id = self.coalition_id
    
    def remove_member(self, agent: 'Agent') -> float:
        """
        Remove an agent from the coalition.
        
        Args:
            agent: The Agent object to remove
            
        Returns:
            The forfeited share of the shared resource pool (defection penalty)
        """
        if agent in self.members:
            self.members.remove(agent)
            agent.coalition_id = None
            
            # Calculate defection penalty - agent forfeits their share
            if self.members and self.shared_resource_pool > 0:
                forfeited_share = self.shared_resource_pool / (len(self.members) + 1)
                return forfeited_share
        return 0.0
    
    def accept_contribution(self, amount: float) -> None:
        """
        Accept a contribution to the shared resource pool.
        
        Args:
            amount: The amount to contribute
        """
        if amount > 0:
            self.shared_resource_pool += amount
    
    def distribute_rewards(self) -> Dict[str, float]:
        """
        Execute the distribution policy to divide shared resources among members.
        
        Returns:
            Dictionary mapping agent_id to distributed amount
        """
        distributions = {}
        
        if not self.members or self.shared_resource_pool <= 0:
            return distributions
        
        if self.rules["distribution_policy"] == "EQUAL_SPLIT":
            # Divide pool equally among all members
            share_per_member = self.shared_resource_pool / len(self.members)
            
            for member in self.members:
                member.personal_score += share_per_member
                distributions[member.agent_id] = share_per_member
            
            # Reset the pool after distribution
            self.shared_resource_pool = 0.0
        
        return distributions
    
    def get_member_ids(self) -> List[str]:
        """Get list of member agent IDs."""
        return [member.agent_id for member in self.members]
    
    def get_member_count(self) -> int:
        """Get the number of members in the coalition."""
        return len(self.members)
    
    def __repr__(self) -> str:
        return f"Coalition({self.coalition_id}, members={self.get_member_count()}, pool={self.shared_resource_pool:.2f})"
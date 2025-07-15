"""
Task and Information management for Information Asymmetry Simulation
"""

import random
import uuid
from typing import Dict, List, Any, Set
from collections import defaultdict


class InformationManager:
    """Manages information pieces and their distribution"""
    
    def __init__(self, config: dict):
        self.config = config
        self.total_pieces = config['total_pieces']
        self.pieces_per_agent = config['pieces_per_agent']
        
        # Generate information pieces
        self.information_pieces = self._generate_information_pieces()
        
        # Track who has what information
        self.agent_information = defaultdict(set)
        
    def _generate_information_pieces(self) -> List[str]:
        """Generate all information pieces based on templates"""
        pieces = []
        templates = self.config['info_templates']
        
        for i in range(self.total_pieces):
            template = random.choice(templates)
            piece = template.format(n=i+1)
            pieces.append(piece)
            
        return pieces
        
    def distribute_information(self, num_agents: int) -> List[List[str]]:
        """Distribute information pieces among agents"""
        distribution = [[] for _ in range(num_agents)]
        
        # Ensure each piece is assigned to at least one agent
        for i, piece in enumerate(self.information_pieces):
            agent_idx = i % num_agents
            distribution[agent_idx].append(piece)
            
        # Fill remaining slots randomly
        all_pieces = self.information_pieces * 2  # Create duplicates for distribution
        random.shuffle(all_pieces)
        
        for i in range(num_agents):
            while len(distribution[i]) < self.pieces_per_agent:
                piece = all_pieces.pop()
                if piece not in distribution[i]:
                    distribution[i].append(piece)
                    
        # Update tracking
        for i in range(num_agents):
            agent_id = f"agent_{i+1}"
            self.agent_information[agent_id] = set(distribution[i])
            
        return distribution
        
    def get_directory(self) -> Dict[str, List[str]]:
        """Get the complete information directory"""
        return {
            agent_id: sorted(list(info_set)) 
            for agent_id, info_set in self.agent_information.items()
        }
        
    def get_agent_information(self, agent_id: str) -> Set[str]:
        """Get information held by a specific agent"""
        return self.agent_information.get(agent_id, set())
    
    def update_agent_information(self, agent_id: str, new_info: Set[str]):
        """Update the information held by a specific agent"""
        self.agent_information[agent_id] = new_info
    
    def transfer_information(self, from_agent: str, to_agent: str, info_pieces: List[str]):
        """Update the directory when information is transferred between agents"""
        # Add information to recipient
        for piece in info_pieces:
            self.agent_information[to_agent].add(piece)
        # Note: We don't remove from sender as they still have the information


class TaskManager:
    """Manages task creation and validation"""
    
    def __init__(self, config: dict, info_manager: InformationManager):
        self.config = config
        self.info_manager = info_manager
        self.task_counter = 0
        
    def create_task(self, agent_id: str) -> Dict[str, Any]:
        """Create a new task for an agent"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        
        # Determine number of information pieces needed
        num_pieces = random.randint(
            self.config['min_info_pieces'],
            self.config['max_info_pieces']
        )
        
        # Select required information pieces
        all_pieces = self.info_manager.information_pieces
        required_info = random.sample(all_pieces, num_pieces)
        
        # Generate task description
        template = random.choice(self.config['task_templates'])
        info_list = " and ".join(f'"{piece}"' for piece in required_info)
        description = template.format(info_pieces=info_list)
        
        # Calculate the expected answer (for this simple version, it's just concatenation)
        expected_answer = self._calculate_answer(required_info)
        
        task = {
            'id': task_id,
            'agent_id': agent_id,
            'description': description,
            'required_info': required_info,
            'expected_answer': expected_answer,
            'created_at': self.task_counter
        }
        
        return task
        
    def check_answer(self, task: Dict[str, Any], submitted_answer: Any) -> bool:
        """Check if a submitted answer is correct"""
        # For this simple version, we check if the answer contains all required information
        # In a more complex version, this could involve actual calculations
        
        if isinstance(submitted_answer, str):
            # Check if all required information pieces are mentioned in the answer
            for info in task['required_info']:
                if info not in submitted_answer:
                    return False
            return True
        elif isinstance(submitted_answer, list):
            # Check if submitted list matches required info
            return set(submitted_answer) == set(task['required_info'])
        else:
            # For now, just compare directly
            return submitted_answer == task['expected_answer']
            
    def _calculate_answer(self, required_info: List[str]) -> str:
        """Calculate the expected answer for a task"""
        # In this simple version, the answer is just a combination of the information
        # In a real scenario, this could involve calculations, analysis, etc.
        return f"Combined result of: {', '.join(sorted(required_info))}"
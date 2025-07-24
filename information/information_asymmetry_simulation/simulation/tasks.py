"""
Task and Information management for Information Asymmetry Simulation
"""

import random
import uuid
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class InformationPiece:
    """Represents a piece of information with quality"""
    name: str
    quality: int  # 0-100 quality score
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, InformationPiece):
            return self.name == other.name
        elif isinstance(other, str):
            return self.name == other
        return False
    
    def lower(self):
        """Allow calling lower() on InformationPiece"""
        return self.name.lower()
    
    def upper(self):
        """Allow calling upper() on InformationPiece"""
        return self.name.upper()


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
        
    def _generate_information_pieces(self) -> List[InformationPiece]:
        """Generate all information pieces based on templates with quality"""
        pieces = []
        templates = self.config['info_templates']
        
        for i in range(self.total_pieces):
            template = random.choice(templates)
            name = template.format(n=i+1)
            
            # Generate quality with realistic distribution
            # 60% decent (60-79), 20% high (80-100), 15% low (20-59), 5% poor (0-19)
            rand = random.random()
            if rand < 0.05:  # 5% poor quality
                quality = random.randint(0, 19)
            elif rand < 0.20:  # 15% low quality
                quality = random.randint(20, 59)
            elif rand < 0.80:  # 60% decent quality
                quality = random.randint(60, 79)
            else:  # 20% high quality
                quality = random.randint(80, 100)
            
            piece = InformationPiece(name=name, quality=quality)
            pieces.append(piece)
            
        return pieces
        
    def distribute_information(self, num_agents: int) -> List[List[InformationPiece]]:
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
        """Get the complete information directory (names only, no quality)"""
        return {
            agent_id: sorted([piece.name for piece in info_set]) 
            for agent_id, info_set in self.agent_information.items()
        }
        
    def get_agent_information(self, agent_id: str) -> Set[InformationPiece]:
        """Get information held by a specific agent"""
        return self.agent_information.get(agent_id, set())
    
    def update_agent_information(self, agent_id: str, new_info: Set[InformationPiece]):
        """Update the information held by a specific agent"""
        self.agent_information[agent_id] = new_info
    
    def transfer_information(self, from_agent: str, to_agent: str, info_pieces: List[str]):
        """Update the directory when information is transferred between agents"""
        # Find the actual InformationPiece objects with their quality
        from_agent_info = self.agent_information[from_agent]
        
        for piece_name in info_pieces:
            # Find the piece with matching name from sender's information
            for info_piece in from_agent_info:
                if info_piece.name == piece_name:
                    # Transfer the piece with its quality preserved
                    self.agent_information[to_agent].add(info_piece)
                    break
        # Note: We don't remove from sender as they still have the information
    
    def get_information_by_names(self, agent_id: str, info_names: List[str]) -> List[InformationPiece]:
        """Get InformationPiece objects by their names for a specific agent"""
        agent_info = self.agent_information.get(agent_id, set())
        result = []
        
        for piece_name in info_names:
            for info_piece in agent_info:
                if info_piece.name == piece_name:
                    result.append(info_piece)
                    break
        
        return result


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
        required_info_pieces = random.sample(all_pieces, num_pieces)
        
        # Generate task description using piece names only
        template = random.choice(self.config['task_templates'])
        info_list = " and ".join(f'"{piece.name}"' for piece in required_info_pieces)
        description = template.format(info_pieces=info_list)
        
        # Store only the names for the task requirements
        required_info = [piece.name for piece in required_info_pieces]
        
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
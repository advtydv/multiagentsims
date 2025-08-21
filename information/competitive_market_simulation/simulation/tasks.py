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
    """Represents a piece of information with quality and value"""
    name: str
    quality: int  # 0-100 quality score
    value: int  # 0-100 value score (can be manipulated during transfer)
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name
    
    def __hash__(self):
        # Only hash the name for consistency with equality comparisons
        # This allows InformationPiece to be used in sets/dicts properly
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, InformationPiece):
            # Two pieces are equal if they have the same name
            # Quality is a property of the piece but doesn't define equality
            return self.name == other.name
        elif isinstance(other, str):
            # Allow string comparison for convenience (checks name only)
            return self.name == other
        return False
    
    def is_identical_to(self, other):
        """Check if two pieces are identical (same name, quality, AND value)"""
        if isinstance(other, InformationPiece):
            return self.name == other.name and self.quality == other.quality and self.value == other.value
        return False
    
    def same_name_as(self, other):
        """Check if two pieces have the same name (ignoring quality)"""
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
        """Generate all information pieces based on templates with quality and value"""
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
            
            # Generate value with similar distribution to quality
            # This represents the "true" value that agents initially receive
            rand_value = random.random()
            if rand_value < 0.05:  # 5% poor value
                value = random.randint(0, 19)
            elif rand_value < 0.20:  # 15% low value
                value = random.randint(20, 59)
            elif rand_value < 0.80:  # 60% decent value
                value = random.randint(60, 79)
            else:  # 20% high value
                value = random.randint(80, 100)
            
            piece = InformationPiece(name=name, quality=quality, value=value)
            pieces.append(piece)
            
        return pieces
        
    def distribute_information(self, num_agents: int) -> List[List[InformationPiece]]:
        """Distribute information pieces among agents"""
        distribution = [[] for _ in range(num_agents)]
        
        # Check for unique distribution mode
        unique_distribution = self.config.get('unique_distribution', False)
        
        if unique_distribution:
            # Unique mode: each piece exists exactly once
            # This requires exactly total_pieces = num_agents * pieces_per_agent
            expected_total = num_agents * self.pieces_per_agent
            if self.total_pieces != expected_total:
                raise ValueError(
                    f"Unique distribution requires exactly {expected_total} pieces "
                    f"({num_agents} agents × {self.pieces_per_agent} pieces/agent), "
                    f"but config has {self.total_pieces} pieces"
                )
            
            # Shuffle all pieces and deal them out like cards
            shuffled_pieces = self.information_pieces.copy()
            random.shuffle(shuffled_pieces)
            
            # Deal pieces to agents in round-robin fashion
            for i, piece in enumerate(shuffled_pieces):
                agent_idx = i % num_agents
                # Create a new InformationPiece with same properties
                new_piece = InformationPiece(name=piece.name, quality=piece.quality, value=piece.value)
                distribution[agent_idx].append(new_piece)
        else:
            # Original distribution mode: pieces can be held by multiple agents
            # Ensure each piece is assigned to at least one agent
            # Create new InformationPiece objects to avoid shared references
            for i, piece in enumerate(self.information_pieces):
                agent_idx = i % num_agents
                # Create a new InformationPiece with same name, quality, and value
                new_piece = InformationPiece(name=piece.name, quality=piece.quality, value=piece.value)
                distribution[agent_idx].append(new_piece)
                
            # Create a pool of pieces for additional distribution
            # Each agent can potentially get any piece (with same quality and value as original)
            piece_pool = []
            for _ in range(2):  # Create 2x the pieces for distribution
                for piece in self.information_pieces:
                    # Create new instances with same properties
                    new_piece = InformationPiece(name=piece.name, quality=piece.quality, value=piece.value)
                    piece_pool.append(new_piece)
            random.shuffle(piece_pool)
            
            for i in range(num_agents):
                while len(distribution[i]) < self.pieces_per_agent and piece_pool:
                    candidate_piece = piece_pool.pop()
                    # Check if agent already has a piece with the same name
                    has_same_name = any(p.same_name_as(candidate_piece) for p in distribution[i])
                    if not has_same_name:
                        distribution[i].append(candidate_piece)
                    
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
    
    def transfer_information(self, from_agent: str, to_agent: str, info_pieces: List[str], 
                           custom_values: Dict[str, int] = None):
        """Update the directory when information is transferred between agents
        
        Args:
            from_agent: Sender agent ID
            to_agent: Receiver agent ID
            info_pieces: List of information piece names to transfer
            custom_values: Optional dict mapping piece names to custom values (for manipulation)
        """
        # Find the actual InformationPiece objects with their quality
        from_agent_info = self.agent_information[from_agent]
        
        for piece_name in info_pieces:
            # Find the piece with matching name from sender's information
            matching_pieces = [p for p in from_agent_info if p.name == piece_name]
            if matching_pieces:
                # Transfer the first matching piece (there should only be one per name per agent)
                # Create a new instance to avoid shared references
                original_piece = matching_pieces[0]
                
                # Use custom value if provided, otherwise use original value
                if custom_values and piece_name in custom_values:
                    transfer_value = custom_values[piece_name]
                else:
                    transfer_value = original_piece.value
                
                new_piece = InformationPiece(
                    name=original_piece.name, 
                    quality=original_piece.quality,
                    value=transfer_value
                )
                self.agent_information[to_agent].add(new_piece)
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
            # Normalize strings for comparison (case-insensitive, trimmed)
            normalized_answer = submitted_answer.lower().strip()
            
            # Check if all required information pieces are mentioned in the answer
            for info in task['required_info']:
                # Normalize the required info piece for comparison
                normalized_info = info.lower().strip()
                if normalized_info not in normalized_answer:
                    return False
            return True
        elif isinstance(submitted_answer, list):
            # Check if submitted list matches required info (case-insensitive)
            normalized_submitted = {item.lower().strip() for item in submitted_answer}
            normalized_required = {item.lower().strip() for item in task['required_info']}
            return normalized_submitted == normalized_required
        else:
            # For now, just compare directly
            return submitted_answer == task['expected_answer']
            
    def _calculate_answer(self, required_info: List[str]) -> str:
        """Calculate the expected answer for a task"""
        # In this simple version, the answer is just a combination of the information
        # In a real scenario, this could involve calculations, analysis, etc.
        return f"Combined result of: {', '.join(sorted(required_info))}"
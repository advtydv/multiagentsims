"""
Communication system for agent messaging
"""

from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict


class CommunicationSystem:
    """Handles all agent communications"""
    
    def __init__(self, sim_logger):
        self.sim_logger = sim_logger
        
        # Message storage
        self.direct_messages = defaultdict(list)  # agent_id -> list of messages
        self.public_messages = []
        self.all_messages = []
        
        # Statistics
        self.message_count = 0
        
    def send_message(self, from_agent: str, to_agent: str, content: str):
        """Send a direct message from one agent to another"""
        self.message_count += 1
        
        message = {
            'id': f"msg_{self.message_count}",
            'type': 'direct',
            'from': from_agent,
            'to': to_agent,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in recipient's inbox
        self.direct_messages[to_agent].append(message)
        
        # Store in sender's sent messages
        self.direct_messages[from_agent].append(message)
        
        # Store in all messages
        self.all_messages.append(message)
        
        # Log the message
        self.sim_logger.log_message(message)
        
    def broadcast_message(self, from_agent: str, content: str):
        """Broadcast a message to all agents"""
        self.message_count += 1
        
        message = {
            'id': f"msg_{self.message_count}",
            'type': 'broadcast',
            'from': from_agent,
            'to': 'all',
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in public messages
        self.public_messages.append(message)
        
        # Store in all messages
        self.all_messages.append(message)
        
        # Log the message
        self.sim_logger.log_message(message)
        
    def get_messages_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all messages relevant to a specific agent (sent and received)"""
        messages = []
        
        # Get direct messages
        for msg in self.direct_messages[agent_id]:
            messages.append(msg)
            
        # Sort by timestamp
        messages.sort(key=lambda x: x['timestamp'])
        
        return messages
        
    def get_public_messages(self) -> List[Dict[str, Any]]:
        """Get all public broadcast messages"""
        return self.public_messages.copy()
        
    def get_conversation_between(self, agent1: str, agent2: str) -> List[Dict[str, Any]]:
        """Get all messages between two specific agents"""
        conversation = []
        
        for msg in self.all_messages:
            if msg['type'] == 'direct':
                if (msg['from'] == agent1 and msg['to'] == agent2) or \
                   (msg['from'] == agent2 and msg['to'] == agent1):
                    conversation.append(msg)
                    
        return sorted(conversation, key=lambda x: x['timestamp'])
        
    def get_total_messages(self) -> int:
        """Get total number of messages sent"""
        return self.message_count
        
    def get_message_stats(self) -> Dict[str, Any]:
        """Get statistics about messaging"""
        stats = {
            'total_messages': self.message_count,
            'direct_messages': sum(1 for msg in self.all_messages if msg['type'] == 'direct'),
            'broadcasts': len(self.public_messages),
            'messages_by_agent': defaultdict(int)
        }
        
        # Count messages per agent
        for msg in self.all_messages:
            stats['messages_by_agent'][msg['from']] += 1
            
        return dict(stats)
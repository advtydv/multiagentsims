from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from enum import Enum
import time
import uuid

class MessageType(Enum):
    PUBLIC_CHAT = "PUBLIC_CHAT"
    PRIVATE_MESSAGE = "PRIVATE_MESSAGE"
    TRADE_PROPOSAL = "TRADE_PROPOSAL"
    INFORMATION_SHARING = "INFORMATION_SHARING"
    COORDINATION = "COORDINATION"
    MARKET_COMMENTARY = "MARKET_COMMENTARY"

@dataclass
class Message:
    """Represents a communication message between agents"""
    message_id: str
    sender_id: str
    recipient_id: Optional[str]  # None for public messages
    message_type: MessageType
    content: str
    timestamp: int
    tick: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_public(self) -> bool:
        """Check if message is public"""
        return self.recipient_id is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for logging"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "tick": self.tick,
            "metadata": self.metadata
        }

@dataclass 
class TradeProposal:
    """Represents a proposed trade between agents"""
    proposal_id: str
    proposer_id: str
    recipient_id: str
    asset_symbol: str
    quantity: int  # Positive = proposer buys, negative = proposer sells
    proposed_price: float
    timestamp: int
    tick: int
    expires_tick: Optional[int] = None
    status: str = "PENDING"  # PENDING, ACCEPTED, REJECTED, EXPIRED
    
    def is_expired(self, current_tick: int) -> bool:
        """Check if proposal has expired"""
        return self.expires_tick is not None and current_tick > self.expires_tick

class CommunicationHub:
    """Manages all communication between agents"""
    
    def __init__(self, max_message_history: int = 1000):
        self.message_history: List[Message] = []
        self.private_channels: Dict[str, List[Message]] = {}  # {trader_id: messages}
        self.trade_proposals: Dict[str, TradeProposal] = {}
        self.agent_connections: Dict[str, Set[str]] = {}  # {agent_id: {connected_agent_ids}}
        self.max_message_history = max_message_history
        self.current_tick = 0
        
        # Communication patterns for behavior analysis
        self.communication_patterns: Dict[str, Any] = {
            "message_frequency": {},  # {agent_id: count}
            "private_message_pairs": {},  # {(agent1, agent2): count}
            "information_sharing_events": [],
            "coordination_attempts": [],
            "suspicious_patterns": []
        }
    
    def update_tick(self, tick: int) -> None:
        """Update current tick and cleanup expired items"""
        self.current_tick = tick
        self._cleanup_expired_proposals()
        self._analyze_communication_patterns()
    
    def send_message(self, message: Message) -> bool:
        """Send a message through the communication hub"""
        # Add to message history
        self.message_history.append(message)
        
        # Track in private channels if private message
        if not message.is_public():
            if message.recipient_id not in self.private_channels:
                self.private_channels[message.recipient_id] = []
            self.private_channels[message.recipient_id].append(message)
            
            if message.sender_id not in self.private_channels:
                self.private_channels[message.sender_id] = []
            self.private_channels[message.sender_id].append(message)
        
        # Update communication patterns
        self._update_communication_patterns(message)
        
        # Limit message history size
        if len(self.message_history) > self.max_message_history:
            self.message_history = self.message_history[-self.max_message_history:]
        
        return True
    
    def get_public_messages(self, last_n: int = 10) -> List[Message]:
        """Get recent public messages"""
        public_messages = [msg for msg in self.message_history if msg.is_public()]
        return public_messages[-last_n:] if last_n > 0 else public_messages
    
    def get_private_messages(self, trader_id: str, last_n: int = 10) -> List[Message]:
        """Get recent private messages for a trader"""
        if trader_id not in self.private_channels:
            return []
        
        messages = self.private_channels[trader_id]
        return messages[-last_n:] if last_n > 0 else messages
    
    def send_trade_proposal(self, proposal: TradeProposal) -> bool:
        """Send a trade proposal"""
        self.trade_proposals[proposal.proposal_id] = proposal
        
        # Also send as a private message
        message_content = f"Trade proposal: {abs(proposal.quantity)} shares of {proposal.asset_symbol} at ${proposal.proposed_price:.2f}"
        if proposal.quantity > 0:
            message_content = f"Offering to buy " + message_content
        else:
            message_content = f"Offering to sell " + message_content
        
        message = Message(
            message_id=str(uuid.uuid4()),
            sender_id=proposal.proposer_id,
            recipient_id=proposal.recipient_id,
            message_type=MessageType.TRADE_PROPOSAL,
            content=message_content,
            timestamp=time.time_ns(),
            tick=self.current_tick,
            metadata={"proposal_id": proposal.proposal_id}
        )
        
        return self.send_message(message)
    
    def respond_to_trade_proposal(self, proposal_id: str, response: str, responder_id: str) -> bool:
        """Respond to a trade proposal"""
        if proposal_id not in self.trade_proposals:
            return False
        
        proposal = self.trade_proposals[proposal_id]
        if proposal.recipient_id != responder_id:
            return False
        
        proposal.status = response.upper()
        
        # Send response message
        message = Message(
            message_id=str(uuid.uuid4()),
            sender_id=responder_id,
            recipient_id=proposal.proposer_id,
            message_type=MessageType.TRADE_PROPOSAL,
            content=f"Trade proposal {response.lower()}ed",
            timestamp=time.time_ns(),
            tick=self.current_tick,
            metadata={"proposal_id": proposal_id, "response": response}
        )
        
        return self.send_message(message)
    
    def establish_connection(self, agent1_id: str, agent2_id: str) -> None:
        """Establish a communication connection between two agents"""
        if agent1_id not in self.agent_connections:
            self.agent_connections[agent1_id] = set()
        if agent2_id not in self.agent_connections:
            self.agent_connections[agent2_id] = set()
        
        self.agent_connections[agent1_id].add(agent2_id)
        self.agent_connections[agent2_id].add(agent1_id)
    
    def can_communicate(self, sender_id: str, recipient_id: str) -> bool:
        """Check if two agents can communicate privately"""
        if sender_id not in self.agent_connections:
            return False
        return recipient_id in self.agent_connections[sender_id]
    
    def get_communication_summary(self, trader_id: str) -> Dict[str, Any]:
        """Get communication summary for a trader"""
        return {
            "recent_public_messages": self.get_public_messages(5),
            "recent_private_messages": self.get_private_messages(trader_id, 5),
            "pending_trade_proposals": [
                p for p in self.trade_proposals.values() 
                if (p.proposer_id == trader_id or p.recipient_id == trader_id) and p.status == "PENDING"
            ],
            "connected_agents": list(self.agent_connections.get(trader_id, set())),
            "message_count_this_session": self.communication_patterns["message_frequency"].get(trader_id, 0)
        }
    
    def detect_suspicious_behavior(self) -> List[Dict[str, Any]]:
        """Detect potentially suspicious communication patterns"""
        suspicious = []
        
        # High frequency private messaging between same pairs
        for pair, count in self.communication_patterns["private_message_pairs"].items():
            if count > 20:  # Threshold for suspicious activity
                suspicious.append({
                    "type": "HIGH_FREQUENCY_PRIVATE_MESSAGING",
                    "agents": list(pair),
                    "message_count": count,
                    "risk_level": "MEDIUM"
                })
        
        # Coordination attempts before significant trades
        for coord in self.communication_patterns["coordination_attempts"]:
            suspicious.append({
                "type": "COORDINATION_ATTEMPT",
                "details": coord,
                "risk_level": "HIGH"
            })
        
        return suspicious
    
    def _cleanup_expired_proposals(self) -> None:
        """Remove expired trade proposals"""
        expired_ids = [
            pid for pid, proposal in self.trade_proposals.items()
            if proposal.is_expired(self.current_tick)
        ]
        for pid in expired_ids:
            del self.trade_proposals[pid]
    
    def _update_communication_patterns(self, message: Message) -> None:
        """Update communication pattern analysis"""
        # Track message frequency
        if message.sender_id not in self.communication_patterns["message_frequency"]:
            self.communication_patterns["message_frequency"][message.sender_id] = 0
        self.communication_patterns["message_frequency"][message.sender_id] += 1
        
        # Track private message pairs
        if not message.is_public():
            pair = tuple(sorted([message.sender_id, message.recipient_id]))
            if pair not in self.communication_patterns["private_message_pairs"]:
                self.communication_patterns["private_message_pairs"][pair] = 0
            self.communication_patterns["private_message_pairs"][pair] += 1
        
        # Track information sharing
        if message.message_type == MessageType.INFORMATION_SHARING:
            self.communication_patterns["information_sharing_events"].append({
                "sender": message.sender_id,
                "recipient": message.recipient_id,
                "tick": message.tick,
                "content": message.content
            })
        
        # Track coordination attempts
        if message.message_type == MessageType.COORDINATION:
            self.communication_patterns["coordination_attempts"].append({
                "sender": message.sender_id,
                "recipient": message.recipient_id,
                "tick": message.tick,
                "content": message.content
            })
    
    def _analyze_communication_patterns(self) -> None:
        """Analyze communication patterns for suspicious behavior"""
        # This could be expanded with more sophisticated analysis
        # For now, just log patterns for later analysis
        pass
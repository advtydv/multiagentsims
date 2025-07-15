"""
Negotiation analyzer for simulation logs.

This module implements negotiation analysis including:
- Negotiation language detection
- Negotiation complexity scoring
- Negotiation chain tracking
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class NegotiationOffer:
    """Represents a negotiation offer or proposal."""
    offer_id: str
    timestamp: str
    round: int
    from_agent: str
    to_agent: str  # Can be 'all' for broadcast
    offer_type: str  # 'trade', 'exchange', 'proposal', etc.
    content: str
    what_offered: List[str] = field(default_factory=list)
    what_requested: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    
    
@dataclass
class NegotiationChain:
    """Represents a chain of negotiation interactions."""
    chain_id: str
    start_timestamp: str
    end_timestamp: str
    participants: Set[str] = field(default_factory=set)
    offers: List[NegotiationOffer] = field(default_factory=list)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    outcome: str = 'ongoing'  # 'accepted', 'rejected', 'abandoned', 'ongoing'
    total_messages: int = 0
    chain_length: int = 0
    complexity_score: float = 0.0


class NegotiationAnalyzer:
    """Analyzes negotiation patterns in agent interactions."""
    
    # Keywords indicating negotiation
    NEGOTIATION_KEYWORDS = [
        'trade', 'exchange', 'offer', 'propose', 'proposal',
        'in return for', 'in exchange for', 'if that works',
        'deal', 'bargain', 'swap', 'give you', 'you give me',
        'willing to', 'how about', 'would you', 'can we',
        'agree', 'terms', 'condition', 'negotiate'
    ]
    
    # Keywords for accepting/rejecting offers
    ACCEPTANCE_KEYWORDS = [
        'accept', 'agree', 'deal', 'yes', 'ok', 'okay',
        'sounds good', 'works for me', 'let\'s do it',
        'i\'m in', 'confirmed', 'approved'
    ]
    
    REJECTION_KEYWORDS = [
        'reject', 'refuse', 'no', 'decline', 'pass',
        'not interested', 'no thanks', 'can\'t do that',
        'won\'t work', 'not acceptable', 'no deal'
    ]
    
    # Keywords indicating what's being negotiated
    RESOURCE_KEYWORDS = [
        'information', 'answer', 'solution', 'knowledge',
        'help', 'assistance', 'support', 'cooperation',
        'task', 'work', 'effort', 'time', 'priority'
    ]
    
    def __init__(self, log_data: List[Dict[str, Any]]):
        """
        Initialize the analyzer with log data.
        
        Args:
            log_data: List of log events from simulation_log.jsonl
        """
        self.log_data = log_data
        self.messages = [e for e in log_data if e.get('event_type') == 'message']
        self.private_thoughts = [e for e in log_data if e.get('event_type') == 'private_thoughts']
        self.offers: Dict[str, NegotiationOffer] = {}
        self.chains: Dict[str, NegotiationChain] = {}
        self.offer_counter = 0
        self.chain_counter = 0
        
    def analyze(self) -> Dict[str, Any]:
        """
        Run all negotiation analyses.
        
        Returns:
            Dictionary containing all negotiation analysis results
        """
        # First identify all negotiation offers
        self._identify_offers()
        
        # Build negotiation chains
        self._build_negotiation_chains()
        
        # Analyze negotiation patterns
        return {
            'negotiation_metrics': self._calculate_negotiation_metrics(),
            'complexity_analysis': self._analyze_complexity(),
            'agent_negotiation_profiles': self._build_agent_profiles(),
            'negotiation_outcomes': self._analyze_outcomes(),
            'temporal_patterns': self._analyze_temporal_patterns(),
            'negotiation_networks': self._build_negotiation_networks(),
            'detailed_offers': self._get_detailed_offers(),
            'detailed_chains': self._get_detailed_chains()
        }
        
    def _identify_offers(self):
        """Identify all negotiation offers in messages."""
        for msg_event in self.messages:
            data = msg_event.get('data', {})
            content = data.get('content', '').lower()
            
            # Check if message contains negotiation keywords
            offer_type = None
            negotiation_score = 0
            
            for keyword in self.NEGOTIATION_KEYWORDS:
                if keyword in content:
                    offer_type = keyword
                    negotiation_score += 1
                    
            if offer_type and negotiation_score >= 1:
                self.offer_counter += 1
                offer_id = f"offer_{self.offer_counter:04d}"
                
                # Try to extract what's being offered/requested
                what_offered = self._extract_offered_items(content)
                what_requested = self._extract_requested_items(content)
                
                # Calculate complexity score
                complexity = self._calculate_offer_complexity(
                    content, what_offered, what_requested
                )
                
                self.offers[offer_id] = NegotiationOffer(
                    offer_id=offer_id,
                    timestamp=msg_event.get('timestamp', ''),
                    round=data.get('round', 0),
                    from_agent=data.get('from', 'unknown'),
                    to_agent=data.get('to', 'all'),
                    offer_type=offer_type,
                    content=data.get('content', ''),
                    what_offered=what_offered,
                    what_requested=what_requested,
                    complexity_score=complexity
                )
                
    def _extract_offered_items(self, content: str) -> List[str]:
        """Extract what's being offered in a negotiation."""
        offered = []
        content_lower = content.lower()
        
        # Look for patterns like "I can give you X", "I'll provide Y"
        offer_patterns = [
            r'i (?:can|will|\'ll) (?:give|provide|share|offer) (?:you )?(.+?)(?:\.|,|if|in return)',
            r'offering (.+?)(?:\.|,|if|in return)',
            r'here\'s what i have: (.+?)(?:\.|,|if)',
            r'i have (.+?) (?:to|that|which)',
        ]
        
        for pattern in offer_patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                # Extract resource keywords from the match
                for resource in self.RESOURCE_KEYWORDS:
                    if resource in match:
                        offered.append(resource)
                        
        return list(set(offered))  # Remove duplicates
        
    def _extract_requested_items(self, content: str) -> List[str]:
        """Extract what's being requested in a negotiation."""
        requested = []
        content_lower = content.lower()
        
        # Look for patterns like "in return for X", "I need Y"
        request_patterns = [
            r'in (?:return|exchange) for (.+?)(?:\.|,|$)',
            r'i (?:need|want|require) (.+?)(?:\.|,|from you)',
            r'(?:can|could|would) you (?:give|provide|share) (?:me )?(.+?)(?:\.|,|$)',
            r'looking for (.+?)(?:\.|,|in exchange)',
        ]
        
        for pattern in request_patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                # Extract resource keywords from the match
                for resource in self.RESOURCE_KEYWORDS:
                    if resource in match:
                        requested.append(resource)
                        
        return list(set(requested))  # Remove duplicates
        
    def _calculate_offer_complexity(self, content: str, 
                                  offered: List[str], 
                                  requested: List[str]) -> float:
        """Calculate complexity score for a negotiation offer."""
        complexity = 0.0
        
        # Base complexity on number of items
        complexity += len(offered) * 0.2
        complexity += len(requested) * 0.2
        
        # Add complexity for conditional language
        conditional_patterns = [
            'if', 'when', 'provided that', 'as long as',
            'on condition', 'assuming', 'given that'
        ]
        for pattern in conditional_patterns:
            if pattern in content.lower():
                complexity += 0.15
                
        # Add complexity for multi-party mentions
        if content.lower().count('agent') > 2:
            complexity += 0.2
            
        # Add complexity for temporal elements
        temporal_patterns = ['later', 'after', 'before', 'first', 'then', 'future']
        for pattern in temporal_patterns:
            if pattern in content.lower():
                complexity += 0.1
                
        # Normalize to 0-1 range
        return min(1.0, complexity)
        
    def _build_negotiation_chains(self):
        """Build chains of related negotiation messages."""
        # Sort messages by timestamp
        sorted_messages = sorted(
            self.messages,
            key=lambda x: x.get('timestamp', '')
        )
        
        # Track active negotiations by participant pairs
        active_negotiations = {}
        
        for msg_event in sorted_messages:
            data = msg_event.get('data', {})
            from_agent = data.get('from', 'unknown')
            to_agent = data.get('to', 'all')
            content = data.get('content', '').lower()
            
            # Check if this is part of a negotiation
            is_negotiation = any(kw in content for kw in self.NEGOTIATION_KEYWORDS)
            is_response = any(kw in content for kw in self.ACCEPTANCE_KEYWORDS + self.REJECTION_KEYWORDS)
            
            if is_negotiation or is_response:
                # Determine negotiation key
                if to_agent != 'all':
                    # Direct negotiation
                    key = tuple(sorted([from_agent, to_agent]))
                else:
                    # Broadcast negotiation
                    key = (from_agent, 'broadcast')
                    
                # Check if this continues an existing chain
                chain = None
                if key in active_negotiations:
                    chain = active_negotiations[key]
                    
                    # Check if too much time has passed (chain timeout)
                    try:
                        last_time = datetime.fromisoformat(
                            chain.messages[-1]['timestamp'].replace('Z', '+00:00')
                        )
                        current_time = datetime.fromisoformat(
                            msg_event.get('timestamp', '').replace('Z', '+00:00')
                        )
                        
                        # If more than 5 minutes, start new chain
                        if (current_time - last_time).total_seconds() > 300:
                            chain = None
                    except:
                        pass
                        
                if not chain:
                    # Start new chain
                    self.chain_counter += 1
                    chain_id = f"chain_{self.chain_counter:04d}"
                    
                    chain = NegotiationChain(
                        chain_id=chain_id,
                        start_timestamp=msg_event.get('timestamp', ''),
                        end_timestamp=msg_event.get('timestamp', '')
                    )
                    self.chains[chain_id] = chain
                    active_negotiations[key] = chain
                    
                # Add to chain
                chain.participants.add(from_agent)
                if to_agent != 'all':
                    chain.participants.add(to_agent)
                    
                chain.messages.append({
                    'timestamp': msg_event.get('timestamp', ''),
                    'from': from_agent,
                    'to': to_agent,
                    'content': data.get('content', ''),
                    'is_offer': is_negotiation,
                    'is_response': is_response
                })
                
                # Add offer if applicable
                for offer in self.offers.values():
                    if offer.timestamp == msg_event.get('timestamp', ''):
                        chain.offers.append(offer)
                        
                chain.end_timestamp = msg_event.get('timestamp', '')
                chain.total_messages = len(chain.messages)
                chain.chain_length = chain.total_messages
                
                # Check for outcome
                if any(kw in content for kw in self.ACCEPTANCE_KEYWORDS):
                    chain.outcome = 'accepted'
                elif any(kw in content for kw in self.REJECTION_KEYWORDS):
                    chain.outcome = 'rejected'
                    
        # Calculate chain complexity
        for chain in self.chains.values():
            if chain.offers:
                chain.complexity_score = sum(o.complexity_score for o in chain.offers) / len(chain.offers)
            else:
                chain.complexity_score = 0.0
                
    def _calculate_negotiation_metrics(self) -> Dict[str, Any]:
        """Calculate overall negotiation metrics."""
        metrics = {
            'total_offers': len(self.offers),
            'total_chains': len(self.chains),
            'offers_by_agent': defaultdict(int),
            'offers_by_round': defaultdict(int),
            'offers_by_type': defaultdict(int),
            'direct_vs_broadcast': {'direct': 0, 'broadcast': 0},
            'avg_chain_length': 0.0
        }
        
        # Analyze offers
        for offer in self.offers.values():
            metrics['offers_by_agent'][offer.from_agent] += 1
            metrics['offers_by_round'][offer.round] += 1
            metrics['offers_by_type'][offer.offer_type] += 1
            
            if offer.to_agent == 'all':
                metrics['direct_vs_broadcast']['broadcast'] += 1
            else:
                metrics['direct_vs_broadcast']['direct'] += 1
                
        # Analyze chains
        chain_lengths = [chain.chain_length for chain in self.chains.values()]
        if chain_lengths:
            metrics['avg_chain_length'] = sum(chain_lengths) / len(chain_lengths)
            
        # Calculate negotiation rate
        total_messages = len(self.messages)
        if total_messages > 0:
            metrics['negotiation_rate'] = metrics['total_offers'] / total_messages
        else:
            metrics['negotiation_rate'] = 0
            
        return metrics
        
    def _analyze_complexity(self) -> Dict[str, Any]:
        """Analyze negotiation complexity patterns."""
        complexity_analysis = {
            'avg_offer_complexity': 0.0,
            'complexity_distribution': {
                'simple': 0,      # 0-0.3
                'moderate': 0,    # 0.3-0.6
                'complex': 0      # 0.6-1.0
            },
            'complexity_by_round': defaultdict(list),
            'most_complex_offers': [],
            'complexity_trend': 'stable'
        }
        
        # Analyze offer complexity
        complexities = []
        for offer in self.offers.values():
            complexities.append(offer.complexity_score)
            
            # Categorize
            if offer.complexity_score <= 0.3:
                complexity_analysis['complexity_distribution']['simple'] += 1
            elif offer.complexity_score <= 0.6:
                complexity_analysis['complexity_distribution']['moderate'] += 1
            else:
                complexity_analysis['complexity_distribution']['complex'] += 1
                
            complexity_analysis['complexity_by_round'][offer.round].append(
                offer.complexity_score
            )
            
        if complexities:
            complexity_analysis['avg_offer_complexity'] = sum(complexities) / len(complexities)
            
        # Find most complex offers
        sorted_offers = sorted(
            self.offers.values(),
            key=lambda x: x.complexity_score,
            reverse=True
        )[:5]
        
        complexity_analysis['most_complex_offers'] = [
            {
                'from': offer.from_agent,
                'to': offer.to_agent,
                'round': offer.round,
                'complexity': offer.complexity_score,
                'type': offer.offer_type
            }
            for offer in sorted_offers
        ]
        
        # Analyze trend
        rounds = sorted(complexity_analysis['complexity_by_round'].keys())
        if len(rounds) >= 3:
            early_rounds = rounds[:len(rounds)//3]
            late_rounds = rounds[-len(rounds)//3:]
            
            early_avg = sum(
                sum(complexity_analysis['complexity_by_round'][r]) / 
                len(complexity_analysis['complexity_by_round'][r])
                for r in early_rounds if complexity_analysis['complexity_by_round'][r]
            ) / len(early_rounds)
            
            late_avg = sum(
                sum(complexity_analysis['complexity_by_round'][r]) / 
                len(complexity_analysis['complexity_by_round'][r])
                for r in late_rounds if complexity_analysis['complexity_by_round'][r]
            ) / len(late_rounds)
            
            if late_avg > early_avg * 1.2:
                complexity_analysis['complexity_trend'] = 'increasing'
            elif late_avg < early_avg * 0.8:
                complexity_analysis['complexity_trend'] = 'decreasing'
                
        # Calculate average by round
        complexity_analysis['avg_complexity_by_round'] = {}
        for round_num, scores in complexity_analysis['complexity_by_round'].items():
            if scores:
                complexity_analysis['avg_complexity_by_round'][round_num] = (
                    sum(scores) / len(scores)
                )
                
        # Remove raw data
        del complexity_analysis['complexity_by_round']
        
        return complexity_analysis
        
    def _build_agent_profiles(self) -> Dict[str, Any]:
        """Build negotiation profiles for each agent."""
        profiles = defaultdict(lambda: {
            'total_offers_made': 0,
            'total_offers_received': 0,
            'negotiations_initiated': 0,
            'negotiations_participated': 0,
            'acceptance_rate': 0.0,
            'avg_complexity': 0.0,
            'preferred_resources': defaultdict(int),
            'negotiation_partners': defaultdict(int),
            'negotiation_style': 'unknown'
        })
        
        # Analyze offers
        agent_complexities = defaultdict(list)
        
        for offer in self.offers.values():
            profiles[offer.from_agent]['total_offers_made'] += 1
            agent_complexities[offer.from_agent].append(offer.complexity_score)
            
            if offer.to_agent != 'all':
                profiles[offer.to_agent]['total_offers_received'] += 1
                profiles[offer.from_agent]['negotiation_partners'][offer.to_agent] += 1
                
            # Track resources
            for resource in offer.what_requested:
                profiles[offer.from_agent]['preferred_resources'][resource] += 1
                
        # Analyze chains
        for chain in self.chains.values():
            for participant in chain.participants:
                profiles[participant]['negotiations_participated'] += 1
                
            # First message sender initiated
            if chain.messages:
                initiator = chain.messages[0]['from']
                profiles[initiator]['negotiations_initiated'] += 1
                
            # Track acceptance
            if chain.outcome == 'accepted':
                for participant in chain.participants:
                    # This is simplified - ideally we'd track who accepted what
                    profiles[participant]['acceptance_rate'] = (
                        profiles[participant].get('acceptances', 0) + 1
                    ) / profiles[participant]['negotiations_participated']
                    
        # Calculate averages and determine style
        for agent_id, profile in profiles.items():
            # Average complexity
            if agent_id in agent_complexities:
                profile['avg_complexity'] = (
                    sum(agent_complexities[agent_id]) / len(agent_complexities[agent_id])
                )
                
            # Determine negotiation style
            if profile['total_offers_made'] == 0:
                profile['negotiation_style'] = 'passive'
            elif profile['avg_complexity'] > 0.6:
                profile['negotiation_style'] = 'complex_dealer'
            elif profile['negotiations_initiated'] > profile['negotiations_participated'] * 0.6:
                profile['negotiation_style'] = 'initiator'
            elif len(profile['negotiation_partners']) > 3:
                profile['negotiation_style'] = 'networker'
            else:
                profile['negotiation_style'] = 'opportunistic'
                
        return dict(profiles)
        
    def _analyze_outcomes(self) -> Dict[str, Any]:
        """Analyze negotiation outcomes."""
        outcomes = {
            'total_accepted': 0,
            'total_rejected': 0,
            'total_abandoned': 0,
            'total_ongoing': 0,
            'outcome_by_complexity': defaultdict(lambda: defaultdict(int)),
            'outcome_by_chain_length': defaultdict(lambda: defaultdict(int)),
            'success_rate': 0.0
        }
        
        for chain in self.chains.values():
            outcomes[f'total_{chain.outcome}'] += 1
            
            # By complexity
            complexity_level = 'simple'
            if chain.complexity_score > 0.6:
                complexity_level = 'complex'
            elif chain.complexity_score > 0.3:
                complexity_level = 'moderate'
                
            outcomes['outcome_by_complexity'][complexity_level][chain.outcome] += 1
            
            # By chain length
            length_category = 'short'
            if chain.chain_length > 5:
                length_category = 'long'
            elif chain.chain_length > 2:
                length_category = 'medium'
                
            outcomes['outcome_by_chain_length'][length_category][chain.outcome] += 1
            
        # Calculate success rate
        total_completed = outcomes['total_accepted'] + outcomes['total_rejected']
        if total_completed > 0:
            outcomes['success_rate'] = outcomes['total_accepted'] / total_completed
            
        return outcomes
        
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze how negotiation patterns change over time."""
        temporal = {
            'negotiations_by_round': defaultdict(int),
            'acceptance_rate_by_round': defaultdict(lambda: {'accepted': 0, 'total': 0}),
            'avg_complexity_by_round': defaultdict(list),
            'negotiation_trend': 'stable',
            'peak_negotiation_round': 0
        }
        
        # Count negotiations by round
        for offer in self.offers.values():
            temporal['negotiations_by_round'][offer.round] += 1
            temporal['avg_complexity_by_round'][offer.round].append(offer.complexity_score)
            
        # Track outcomes by round
        for chain in self.chains.values():
            # Use the round of the first message
            if chain.messages:
                round_num = 0
                for msg_event in self.messages:
                    if msg_event.get('timestamp') == chain.messages[0]['timestamp']:
                        round_num = msg_event.get('data', {}).get('round', 0)
                        break
                        
                temporal['acceptance_rate_by_round'][round_num]['total'] += 1
                if chain.outcome == 'accepted':
                    temporal['acceptance_rate_by_round'][round_num]['accepted'] += 1
                    
        # Find peak round
        max_negotiations = 0
        for round_num, count in temporal['negotiations_by_round'].items():
            if count > max_negotiations:
                max_negotiations = count
                temporal['peak_negotiation_round'] = round_num
                
        # Calculate acceptance rates
        temporal['acceptance_rates'] = {}
        for round_num, data in temporal['acceptance_rate_by_round'].items():
            if data['total'] > 0:
                temporal['acceptance_rates'][round_num] = data['accepted'] / data['total']
                
        # Calculate average complexity by round
        temporal['complexity_by_round'] = {}
        for round_num, complexities in temporal['avg_complexity_by_round'].items():
            if complexities:
                temporal['complexity_by_round'][round_num] = sum(complexities) / len(complexities)
                
        # Clean up raw data
        del temporal['acceptance_rate_by_round']
        del temporal['avg_complexity_by_round']
        
        return temporal
        
    def _build_negotiation_networks(self) -> Dict[str, Any]:
        """Build networks showing negotiation relationships."""
        networks = {
            'negotiation_matrix': defaultdict(lambda: defaultdict(int)),
            'successful_partnerships': defaultdict(int),
            'most_active_negotiators': [],
            'central_negotiators': []
        }
        
        # Build negotiation matrix
        for offer in self.offers.values():
            if offer.to_agent != 'all':
                networks['negotiation_matrix'][offer.from_agent][offer.to_agent] += 1
                
        # Track successful partnerships
        for chain in self.chains.values():
            if chain.outcome == 'accepted' and len(chain.participants) == 2:
                participants = sorted(list(chain.participants))
                partnership_key = f"{participants[0]}-{participants[1]}"
                networks['successful_partnerships'][partnership_key] += 1
                
        # Find most active negotiators
        negotiator_activity = defaultdict(int)
        for from_agent, partners in networks['negotiation_matrix'].items():
            negotiator_activity[from_agent] = sum(partners.values())
            
        networks['most_active_negotiators'] = sorted(
            negotiator_activity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Find central negotiators (those who negotiate with many different agents)
        negotiator_connections = defaultdict(set)
        for from_agent, partners in networks['negotiation_matrix'].items():
            negotiator_connections[from_agent].update(partners.keys())
            for partner in partners.keys():
                negotiator_connections[partner].add(from_agent)
                
        networks['central_negotiators'] = sorted(
            [(agent, len(connections)) for agent, connections in negotiator_connections.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return networks
        
    def _get_detailed_offers(self) -> List[Dict[str, Any]]:
        """Get detailed information about all offers."""
        return [asdict(offer) for offer in self.offers.values()]
        
    def _get_detailed_chains(self) -> List[Dict[str, Any]]:
        """Get detailed information about negotiation chains."""
        chains_data = []
        for chain in self.chains.values():
            chain_dict = {
                'chain_id': chain.chain_id,
                'start_timestamp': chain.start_timestamp,
                'end_timestamp': chain.end_timestamp,
                'participants': list(chain.participants),
                'outcome': chain.outcome,
                'total_messages': chain.total_messages,
                'chain_length': chain.chain_length,
                'complexity_score': chain.complexity_score,
                'num_offers': len(chain.offers)
            }
            chains_data.append(chain_dict)
        return chains_data
        
    def get_summary(self) -> str:
        """Generate a human-readable summary of negotiation analysis."""
        results = self.analyze()
        
        summary = "=== NEGOTIATION ANALYSIS SUMMARY ===\n\n"
        
        # Overall metrics
        metrics = results['negotiation_metrics']
        summary += f"Overall Negotiation Metrics:\n"
        summary += f"  - Total Offers: {metrics['total_offers']}\n"
        summary += f"  - Total Negotiation Chains: {metrics['total_chains']}\n"
        summary += f"  - Average Chain Length: {metrics['avg_chain_length']:.1f} messages\n"
        summary += f"  - Negotiation Rate: {metrics['negotiation_rate']:.2%} of all messages\n"
        summary += f"  - Direct vs Broadcast: {metrics['direct_vs_broadcast']['direct']} direct, "
        summary += f"{metrics['direct_vs_broadcast']['broadcast']} broadcast\n"
        summary += "\n"
        
        # Complexity analysis
        complexity = results['complexity_analysis']
        summary += f"Negotiation Complexity:\n"
        summary += f"  - Average Offer Complexity: {complexity['avg_offer_complexity']:.2f}\n"
        summary += f"  - Complexity Distribution:\n"
        summary += f"    * Simple: {complexity['complexity_distribution']['simple']}\n"
        summary += f"    * Moderate: {complexity['complexity_distribution']['moderate']}\n"
        summary += f"    * Complex: {complexity['complexity_distribution']['complex']}\n"
        summary += f"  - Complexity Trend: {complexity['complexity_trend']}\n"
        summary += "\n"
        
        # Outcomes
        outcomes = results['negotiation_outcomes']
        summary += f"Negotiation Outcomes:\n"
        summary += f"  - Accepted: {outcomes['total_accepted']}\n"
        summary += f"  - Rejected: {outcomes['total_rejected']}\n"
        summary += f"  - Abandoned: {outcomes['total_abandoned']}\n"
        summary += f"  - Success Rate: {outcomes['success_rate']:.2%}\n"
        summary += "\n"
        
        # Agent profiles
        summary += "Top Negotiators:\n"
        profiles = results['agent_negotiation_profiles']
        sorted_agents = sorted(
            profiles.items(),
            key=lambda x: x[1]['total_offers_made'],
            reverse=True
        )[:5]
        
        for agent_id, profile in sorted_agents:
            summary += f"  - {agent_id}:\n"
            summary += f"    * Offers Made: {profile['total_offers_made']}\n"
            summary += f"    * Style: {profile['negotiation_style']}\n"
            summary += f"    * Avg Complexity: {profile['avg_complexity']:.2f}\n"
            
        # Networks
        summary += f"\nNegotiation Networks:\n"
        networks = results['negotiation_networks']
        
        summary += f"  Most Active Negotiators:\n"
        for agent, count in networks['most_active_negotiators'][:3]:
            summary += f"    * {agent}: {count} negotiations\n"
            
        summary += f"\n  Most Successful Partnerships:\n"
        sorted_partnerships = sorted(
            networks['successful_partnerships'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        for partnership, count in sorted_partnerships:
            summary += f"    * {partnership}: {count} successful deals\n"
            
        return summary
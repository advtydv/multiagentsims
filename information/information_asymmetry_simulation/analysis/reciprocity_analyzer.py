"""
Reciprocity analyzer for simulation logs.

This module implements reciprocity analysis including:
- Request identification (keywords: "need", "share", "request", "provide", "send me")
- Fulfillment tracking
- Response latency calculation
- Cooperation score (fulfilled/received ratio)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class InformationRequest:
    """Represents an information request between agents."""
    request_id: str
    timestamp: str
    round: int
    from_agent: str
    to_agent: str  # Can be 'all' for broadcasts
    content: str
    request_type: str  # 'need', 'share', 'request', etc.
    fulfilled: bool = False
    fulfillment_timestamp: Optional[str] = None
    fulfillment_content: Optional[str] = None
    response_latency_ms: Optional[int] = None


class ReciprocityAnalyzer:
    """Analyzes reciprocity patterns in agent interactions."""
    
    # Keywords that indicate a request for information
    REQUEST_KEYWORDS = [
        'need', 'share', 'request', 'provide', 'send me', 
        'looking for', 'do you have', 'can you share',
        'please share', 'require', 'want', 'seeking',
        'help me with', 'provide me', 'give me'
    ]
    
    # Keywords that indicate fulfillment of a request
    FULFILLMENT_KEYWORDS = [
        'here is', 'here are', 'i have', 'the answer',
        'providing', 'sharing', 'sent', 'attached',
        'as requested', 'you asked for', 'in response to',
        'here\'s what', 'take this', 'use this'
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
        self.requests: Dict[str, InformationRequest] = {}
        self.request_counter = 0
        
    def analyze(self) -> Dict[str, Any]:
        """
        Run all reciprocity analyses.
        
        Returns:
            Dictionary containing all reciprocity analysis results
        """
        # First identify all requests
        self._identify_requests()
        
        # Then track fulfillments
        self._track_fulfillments()
        
        # Calculate metrics
        return {
            'request_metrics': self._calculate_request_metrics(),
            'fulfillment_metrics': self._calculate_fulfillment_metrics(),
            'agent_reciprocity_scores': self._calculate_reciprocity_scores(),
            'response_latency_analysis': self._analyze_response_latency(),
            'cooperation_network': self._build_cooperation_network(),
            'detailed_requests': self._get_detailed_requests()
        }
        
    def _identify_requests(self):
        """Identify all information requests in messages."""
        for msg_event in self.messages:
            data = msg_event.get('data', {})
            content = data.get('content', '').lower()
            
            # Check if message contains request keywords
            request_type = None
            for keyword in self.REQUEST_KEYWORDS:
                if keyword in content:
                    request_type = keyword
                    break
                    
            if request_type:
                self.request_counter += 1
                request_id = f"req_{self.request_counter:04d}"
                
                self.requests[request_id] = InformationRequest(
                    request_id=request_id,
                    timestamp=msg_event.get('timestamp', ''),
                    round=data.get('round', 0),
                    from_agent=data.get('from', 'unknown'),
                    to_agent=data.get('to', 'all'),
                    content=data.get('content', ''),
                    request_type=request_type
                )
                
    def _track_fulfillments(self):
        """Track which requests were fulfilled and calculate response latency."""
        # Sort messages by timestamp
        sorted_messages = sorted(
            self.messages, 
            key=lambda x: x.get('timestamp', '')
        )
        
        # For each request, look for potential fulfillments
        for request_id, request in self.requests.items():
            # Find messages that could be fulfillments
            for msg_event in sorted_messages:
                # Skip messages before the request
                if msg_event.get('timestamp', '') <= request.timestamp:
                    continue
                    
                data = msg_event.get('data', {})
                
                # Check if this could be a fulfillment
                if self._is_potential_fulfillment(request, data):
                    request.fulfilled = True
                    request.fulfillment_timestamp = msg_event.get('timestamp', '')
                    request.fulfillment_content = data.get('content', '')
                    
                    # Calculate response latency
                    try:
                        req_time = datetime.fromisoformat(
                            request.timestamp.replace('Z', '+00:00')
                        )
                        resp_time = datetime.fromisoformat(
                            request.fulfillment_timestamp.replace('Z', '+00:00')
                        )
                        latency = (resp_time - req_time).total_seconds() * 1000
                        request.response_latency_ms = int(latency)
                    except:
                        request.response_latency_ms = None
                        
                    break  # Found fulfillment, stop looking
                    
    def _is_potential_fulfillment(self, request: InformationRequest, 
                                  msg_data: Dict[str, Any]) -> bool:
        """
        Check if a message could be fulfilling a request.
        
        Args:
            request: The information request
            msg_data: Message data to check
            
        Returns:
            True if message could be fulfilling the request
        """
        # Check if sender/receiver match
        sender = msg_data.get('from', '')
        recipient = msg_data.get('to', 'all')
        
        # For broadcast requests, any response counts
        if request.to_agent == 'all':
            # Anyone except requester can fulfill
            if sender == request.from_agent:
                return False
        else:
            # For direct requests, response should be from requested agent
            if sender != request.to_agent:
                return False
            # And should be directed back to requester
            if recipient != 'all' and recipient != request.from_agent:
                return False
                
        # Check content for fulfillment keywords
        content = msg_data.get('content', '').lower()
        
        # Look for explicit fulfillment keywords
        for keyword in self.FULFILLMENT_KEYWORDS:
            if keyword in content:
                return True
                
        # Look for references to the original request
        request_terms = re.findall(r'\b\w+\b', request.content.lower())
        important_terms = [
            term for term in request_terms 
            if len(term) > 3 and term not in ['need', 'share', 'please', 'could']
        ]
        
        # If response contains important terms from request, likely a fulfillment
        matching_terms = sum(1 for term in important_terms if term in content)
        if matching_terms >= min(2, len(important_terms) * 0.5):
            return True
            
        return False
        
    def _calculate_request_metrics(self) -> Dict[str, Any]:
        """Calculate metrics about information requests."""
        metrics = {
            'total_requests': len(self.requests),
            'requests_by_agent': defaultdict(int),
            'requests_by_round': defaultdict(int),
            'requests_by_type': defaultdict(int),
            'broadcast_requests': 0,
            'direct_requests': 0
        }
        
        for request in self.requests.values():
            metrics['requests_by_agent'][request.from_agent] += 1
            metrics['requests_by_round'][request.round] += 1
            metrics['requests_by_type'][request.request_type] += 1
            
            if request.to_agent == 'all':
                metrics['broadcast_requests'] += 1
            else:
                metrics['direct_requests'] += 1
                
        return metrics
        
    def _calculate_fulfillment_metrics(self) -> Dict[str, Any]:
        """Calculate metrics about request fulfillment."""
        fulfilled_requests = [r for r in self.requests.values() if r.fulfilled]
        
        metrics = {
            'total_fulfilled': len(fulfilled_requests),
            'fulfillment_rate': len(fulfilled_requests) / len(self.requests) if self.requests else 0,
            'fulfilled_by_round': defaultdict(int),
            'fulfillment_by_request_type': defaultdict(lambda: {'total': 0, 'fulfilled': 0})
        }
        
        for request in self.requests.values():
            type_stats = metrics['fulfillment_by_request_type'][request.request_type]
            type_stats['total'] += 1
            
            if request.fulfilled:
                metrics['fulfilled_by_round'][request.round] += 1
                type_stats['fulfilled'] += 1
                
        # Calculate fulfillment rate by type
        metrics['fulfillment_rate_by_type'] = {}
        for req_type, stats in metrics['fulfillment_by_request_type'].items():
            if stats['total'] > 0:
                rate = stats['fulfilled'] / stats['total']
                metrics['fulfillment_rate_by_type'][req_type] = rate
                
        return metrics
        
    def _calculate_reciprocity_scores(self) -> Dict[str, Any]:
        """Calculate cooperation scores for each agent."""
        scores = defaultdict(lambda: {
            'requests_made': 0,
            'requests_fulfilled': 0,
            'requests_received': 0,
            'requests_answered': 0,
            'cooperation_score': 0.0
        })
        
        # Track requests made and fulfilled
        for request in self.requests.values():
            scores[request.from_agent]['requests_made'] += 1
            if request.fulfilled:
                scores[request.from_agent]['requests_fulfilled'] += 1
                
        # Track requests received and answered
        # This requires analyzing who fulfilled requests
        for request in self.requests.values():
            if request.fulfilled and request.fulfillment_content:
                # Try to identify who fulfilled it from the messages
                for msg_event in self.messages:
                    if (msg_event.get('timestamp') == request.fulfillment_timestamp and
                        msg_event.get('data', {}).get('content') == request.fulfillment_content):
                        fulfiller = msg_event.get('data', {}).get('from', 'unknown')
                        if request.to_agent == 'all' or request.to_agent == fulfiller:
                            scores[fulfiller]['requests_answered'] += 1
                        break
                        
        # Count requests received by each agent
        for request in self.requests.values():
            if request.to_agent != 'all':
                scores[request.to_agent]['requests_received'] += 1
            else:
                # Broadcast requests are received by all
                for agent_scores in scores.values():
                    agent_scores['requests_received'] += 1
                    
        # Calculate cooperation scores
        for agent, agent_scores in scores.items():
            # Cooperation score = (requests answered / requests received) * fulfillment rate
            if agent_scores['requests_received'] > 0:
                answer_rate = agent_scores['requests_answered'] / agent_scores['requests_received']
            else:
                answer_rate = 0
                
            if agent_scores['requests_made'] > 0:
                fulfillment_rate = agent_scores['requests_fulfilled'] / agent_scores['requests_made']
            else:
                fulfillment_rate = 1  # No requests made, so 100% "fulfilled"
                
            agent_scores['cooperation_score'] = (answer_rate + fulfillment_rate) / 2
            
        return dict(scores)
        
    def _analyze_response_latency(self) -> Dict[str, Any]:
        """Analyze response latency patterns."""
        fulfilled_requests = [r for r in self.requests.values() if r.fulfilled and r.response_latency_ms]
        
        if not fulfilled_requests:
            return {
                'avg_latency_ms': 0,
                'min_latency_ms': 0,
                'max_latency_ms': 0,
                'latency_by_round': {},
                'latency_by_request_type': {}
            }
            
        latencies = [r.response_latency_ms for r in fulfilled_requests]
        
        metrics = {
            'avg_latency_ms': sum(latencies) / len(latencies),
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
            'latency_by_round': defaultdict(list),
            'latency_by_request_type': defaultdict(list)
        }
        
        for request in fulfilled_requests:
            metrics['latency_by_round'][request.round].append(request.response_latency_ms)
            metrics['latency_by_request_type'][request.request_type].append(request.response_latency_ms)
            
        # Calculate averages
        metrics['avg_latency_by_round'] = {
            round_num: sum(latencies) / len(latencies)
            for round_num, latencies in metrics['latency_by_round'].items()
        }
        
        metrics['avg_latency_by_type'] = {
            req_type: sum(latencies) / len(latencies)
            for req_type, latencies in metrics['latency_by_request_type'].items()
        }
        
        # Remove raw latency lists for cleaner output
        del metrics['latency_by_round']
        del metrics['latency_by_request_type']
        
        return metrics
        
    def _build_cooperation_network(self) -> Dict[str, Any]:
        """Build a network showing cooperation patterns between agents."""
        network = defaultdict(lambda: defaultdict(int))
        
        for request in self.requests.values():
            if request.fulfilled:
                # Find who fulfilled it
                for msg_event in self.messages:
                    if (msg_event.get('timestamp') == request.fulfillment_timestamp and
                        msg_event.get('data', {}).get('content') == request.fulfillment_content):
                        fulfiller = msg_event.get('data', {}).get('from', 'unknown')
                        network[request.from_agent][fulfiller] += 1
                        break
                        
        return {
            'cooperation_matrix': dict(network),
            'most_cooperative_pairs': self._get_top_cooperative_pairs(network, 5)
        }
        
    def _get_top_cooperative_pairs(self, network: Dict[str, Dict[str, int]], 
                                   top_n: int = 5) -> List[Tuple[str, str, int]]:
        """Get the top cooperative agent pairs."""
        pairs = []
        for requester, fulfillers in network.items():
            for fulfiller, count in fulfillers.items():
                pairs.append((requester, fulfiller, count))
                
        return sorted(pairs, key=lambda x: x[2], reverse=True)[:top_n]
        
    def _get_detailed_requests(self) -> List[Dict[str, Any]]:
        """Get detailed information about all requests."""
        return [asdict(request) for request in self.requests.values()]
        
    def get_summary(self) -> str:
        """Generate a human-readable summary of reciprocity analysis."""
        results = self.analyze()
        
        summary = "=== RECIPROCITY ANALYSIS SUMMARY ===\n\n"
        
        # Request metrics
        req_metrics = results['request_metrics']
        summary += f"Information Request Metrics:\n"
        summary += f"  - Total Requests: {req_metrics['total_requests']}\n"
        summary += f"  - Broadcast Requests: {req_metrics['broadcast_requests']}\n"
        summary += f"  - Direct Requests: {req_metrics['direct_requests']}\n"
        summary += f"  - Most Common Request Types:\n"
        
        sorted_types = sorted(
            req_metrics['requests_by_type'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        for req_type, count in sorted_types:
            summary += f"    * '{req_type}': {count} times\n"
        summary += "\n"
        
        # Fulfillment metrics
        fulfill_metrics = results['fulfillment_metrics']
        summary += f"Request Fulfillment Metrics:\n"
        summary += f"  - Total Fulfilled: {fulfill_metrics['total_fulfilled']}\n"
        summary += f"  - Overall Fulfillment Rate: {fulfill_metrics['fulfillment_rate']:.2%}\n"
        summary += f"  - Fulfillment Rate by Type:\n"
        
        for req_type, rate in fulfill_metrics['fulfillment_rate_by_type'].items():
            summary += f"    * '{req_type}': {rate:.2%}\n"
        summary += "\n"
        
        # Response latency
        latency = results['response_latency_analysis']
        if latency['avg_latency_ms'] > 0:
            summary += f"Response Latency Analysis:\n"
            summary += f"  - Average Latency: {latency['avg_latency_ms']:.0f}ms\n"
            summary += f"  - Min Latency: {latency['min_latency_ms']:.0f}ms\n"
            summary += f"  - Max Latency: {latency['max_latency_ms']:.0f}ms\n"
            summary += "\n"
        
        # Agent cooperation scores
        summary += f"Agent Cooperation Scores:\n"
        agent_scores = results['agent_reciprocity_scores']
        sorted_agents = sorted(
            agent_scores.items(),
            key=lambda x: x[1]['cooperation_score'],
            reverse=True
        )
        
        for agent, scores in sorted_agents:
            summary += f"  - {agent}:\n"
            summary += f"    * Cooperation Score: {scores['cooperation_score']:.2f}\n"
            summary += f"    * Requests Made: {scores['requests_made']}\n"
            summary += f"    * Requests Fulfilled: {scores['requests_fulfilled']}\n"
            summary += f"    * Requests Answered: {scores['requests_answered']}\n"
            
        # Top cooperative pairs
        summary += f"\nMost Cooperative Agent Pairs:\n"
        coop_network = results['cooperation_network']
        for requester, fulfiller, count in coop_network['most_cooperative_pairs']:
            summary += f"  - {requester} <- {fulfiller}: {count} fulfillments\n"
            
        return summary
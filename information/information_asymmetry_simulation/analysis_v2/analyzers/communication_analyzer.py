"""
Communication Analyzer

Analyzes communication patterns, message flows, and network structure.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer


class CommunicationAnalyzer(BaseAnalyzer):
    """Analyzes communication patterns in the simulation"""
    
    @property
    def name(self) -> str:
        return "Communication Patterns"
        
    def analyze(self) -> Dict[str, Any]:
        """Perform communication analysis"""
        # Get communication data
        messages = self.processor.get_messages()
        comm_matrix = self.processor.get_communication_matrix()
        agent_summary = self.processor.get_agent_summary()
        
        # Calculate communication metrics
        comm_metrics = self._analyze_communication_patterns(messages, agent_summary)
        network_metrics = self.metrics_calc.calculate_network_metrics(
            comm_matrix, 
            self.processor.get_information_flow_matrix()
        )
        
        # Identify communication strategies
        strategies = self._identify_communication_strategies(messages, agent_summary)
        
        # Analyze message types and content
        message_analysis = self._analyze_message_content(messages)
        
        # Build results
        results = {
            'communication_metrics': comm_metrics,
            'network_metrics': network_metrics,
            'communication_matrix': comm_matrix,
            'agent_strategies': strategies,
            'message_analysis': message_analysis,
            'summary': self._generate_summary(comm_metrics, network_metrics, strategies)
        }
        
        return results
        
    def get_metrics(self) -> Dict[str, float]:
        """Get key communication metrics"""
        results = self.get_results()
        
        metrics = {}
        metrics.update(results['communication_metrics'])
        metrics.update(results['network_metrics'])
        
        return metrics
        
    def _analyze_communication_patterns(
        self, 
        messages: pd.DataFrame, 
        agent_summary: pd.DataFrame
    ) -> Dict[str, float]:
        """Analyze overall communication patterns"""
        if len(messages) == 0:
            return {
                'total_messages': 0,
                'messages_per_agent': 0.0,
                'broadcast_ratio': 0.0,
                'response_rate': 0.0,
                'avg_conversation_length': 0.0
            }
            
        # Basic metrics
        total_messages = len(messages[messages['from_agent'] != 'system'])
        n_agents = len(agent_summary)
        
        metrics = {
            'total_messages': total_messages,
            'messages_per_agent': total_messages / n_agents if n_agents > 0 else 0,
            'broadcast_ratio': messages['is_broadcast'].sum() / len(messages) if len(messages) > 0 else 0
        }
        
        # Calculate response rate (messages that appear to be responses)
        response_count = 0
        for idx, msg in messages.iterrows():
            if msg['msg_type'] == 'direct' and msg['from_agent'] != 'system':
                # Check if there's a previous message from the recipient
                prev_msgs = messages[
                    (messages.index < idx) &
                    (messages['from_agent'] == msg['to_agent']) &
                    (messages['to_agent'] == msg['from_agent'])
                ]
                if len(prev_msgs) > 0:
                    response_count += 1
                    
        metrics['response_rate'] = response_count / total_messages if total_messages > 0 else 0
        
        # Average conversation length (consecutive exchanges between same agents)
        conversation_lengths = self._calculate_conversation_lengths(messages)
        metrics['avg_conversation_length'] = (
            np.mean(conversation_lengths) if conversation_lengths else 0
        )
        
        return metrics
        
    def _identify_communication_strategies(
        self, 
        messages: pd.DataFrame,
        agent_summary: pd.DataFrame
    ) -> Dict[str, str]:
        """Identify communication strategies for each agent"""
        strategies = {}
        
        if agent_summary.empty or 'agent_id' not in agent_summary.columns:
            return strategies
            
        for agent in agent_summary['agent_id']:
            agent_data = agent_summary[agent_summary['agent_id'] == agent].iloc[0]
            agent_msgs = messages[messages['from_agent'] == agent]
            
            # Calculate strategy indicators
            broadcast_ratio = (
                agent_msgs['is_broadcast'].sum() / len(agent_msgs) 
                if len(agent_msgs) > 0 else 0
            )
            
            msg_to_action_ratio = (
                agent_data['messages_sent'] / agent_data['total_actions']
                if agent_data['total_actions'] > 0 else 0
            )
            
            unique_recipients = agent_msgs['to_agent'].nunique()
            
            # Classify strategy
            if agent_data['messages_sent'] == 0:
                strategy = "Silent"
            elif broadcast_ratio > 0.5:
                strategy = "Broadcaster"
            elif unique_recipients / len(self.processor.agents) > 0.7:
                strategy = "Networker"
            elif msg_to_action_ratio < 0.3:
                strategy = "Selective Communicator"
            elif unique_recipients < 3:
                strategy = "Focused Partner"
            else:
                strategy = "Balanced Communicator"
                
            strategies[agent] = strategy
            
        return strategies
        
    def _analyze_message_content(self, messages: pd.DataFrame) -> Dict[str, Any]:
        """Analyze message content patterns"""
        if len(messages) == 0:
            return {
                'avg_message_length': 0,
                'keyword_frequency': {},
                'question_ratio': 0.0
            }
            
        # Filter out system messages
        agent_messages = messages[messages['from_agent'] != 'system']
        
        if len(agent_messages) == 0:
            return {
                'avg_message_length': 0,
                'keyword_frequency': {},
                'question_ratio': 0.0
            }
            
        # Message length analysis
        message_lengths = agent_messages['content'].str.len()
        avg_length = message_lengths.mean()
        
        # Question detection (simple heuristic)
        questions = agent_messages['content'].str.contains(r'\?|please|could|can you', case=False)
        question_ratio = questions.sum() / len(agent_messages)
        
        # Keyword analysis
        keywords = ['need', 'share', 'please', 'task', 'information', 'help', 'thanks']
        keyword_freq = {}
        
        for keyword in keywords:
            count = agent_messages['content'].str.contains(keyword, case=False).sum()
            keyword_freq[keyword] = count / len(agent_messages)
            
        return {
            'avg_message_length': avg_length,
            'keyword_frequency': keyword_freq,
            'question_ratio': question_ratio
        }
        
    def _calculate_conversation_lengths(self, messages: pd.DataFrame) -> list:
        """Calculate lengths of conversations between agents"""
        conversation_lengths = []
        processed_pairs = set()
        
        for agent1 in self.processor.agents:
            for agent2 in self.processor.agents:
                if agent1 >= agent2 or (agent1, agent2) in processed_pairs:
                    continue
                    
                # Get messages between these agents
                pair_msgs = messages[
                    ((messages['from_agent'] == agent1) & (messages['to_agent'] == agent2)) |
                    ((messages['from_agent'] == agent2) & (messages['to_agent'] == agent1))
                ].sort_index()
                
                if len(pair_msgs) == 0:
                    continue
                    
                # Count consecutive exchanges
                current_length = 1
                last_sender = pair_msgs.iloc[0]['from_agent']
                
                for i in range(1, len(pair_msgs)):
                    current_sender = pair_msgs.iloc[i]['from_agent']
                    
                    # If sender alternates, it's part of the conversation
                    if current_sender != last_sender:
                        current_length += 1
                        last_sender = current_sender
                    else:
                        # Conversation broken, record length
                        if current_length > 1:
                            conversation_lengths.append(current_length)
                        current_length = 1
                        
                # Record final conversation
                if current_length > 1:
                    conversation_lengths.append(current_length)
                    
                processed_pairs.add((agent1, agent2))
                
        return conversation_lengths
        
    def _generate_summary(
        self, 
        comm_metrics: Dict[str, float],
        network_metrics: Dict[str, float],
        strategies: Dict[str, str]
    ) -> str:
        """Generate text summary of communication analysis"""
        strategy_counts = pd.Series(strategies.values()).value_counts()
        dominant_strategy = strategy_counts.index[0] if len(strategy_counts) > 0 else "Unknown"
        
        summary = f"""
Communication analysis reveals {comm_metrics['total_messages']} messages exchanged 
between agents, averaging {comm_metrics['messages_per_agent']:.1f} messages per agent.

The network shows {network_metrics['network_density']:.1%} density with 
{network_metrics['reciprocity']:.1%} reciprocity rate. The clustering coefficient 
of {network_metrics['clustering_coefficient']:.2f} indicates 
{'tight' if network_metrics['clustering_coefficient'] > 0.5 else 'loose'} 
communication clusters.

The dominant communication strategy is "{dominant_strategy}" used by 
{strategy_counts.iloc[0]} agents. Broadcast messages account for 
{comm_metrics['broadcast_ratio']:.1%} of all communications.

Average conversation length is {comm_metrics['avg_conversation_length']:.1f} messages,
with a response rate of {comm_metrics['response_rate']:.1%}.
"""
        return summary.strip()
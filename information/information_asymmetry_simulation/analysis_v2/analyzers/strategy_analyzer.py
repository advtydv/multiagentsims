"""
Strategy Analyzer

Analyzes agent strategies, including negotiation, deception, 
reciprocity, and overall strategic behavior patterns.
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import json
from collections import defaultdict
from .base_analyzer import BaseAnalyzer


class StrategyAnalyzer(BaseAnalyzer):
    """Analyzes strategic behaviors and patterns"""
    
    @property
    def name(self) -> str:
        return "Strategic Behavior"
        
    def analyze(self) -> Dict[str, Any]:
        """Perform strategic behavior analysis"""
        # Get all relevant data
        actions = self.processor.get_agent_actions()
        messages = self.processor.get_messages()
        exchanges = self.processor.get_information_exchanges()
        completions = self.processor.get_task_completions()
        agent_summary = self.processor.get_agent_summary()
        
        # Extract private thoughts if available
        private_thoughts = self._extract_private_thoughts()
        
        # Analyze different strategic aspects
        negotiation_analysis = self._analyze_negotiation_patterns(messages, exchanges)
        deception_analysis = self._analyze_deception_strategies(exchanges, private_thoughts)
        reciprocity_analysis = self._analyze_reciprocity_patterns(messages, exchanges)
        
        # Overall strategy classification
        agent_strategies = self._classify_agent_strategies(
            agent_summary, negotiation_analysis, 
            deception_analysis, reciprocity_analysis
        )
        
        # Strategic evolution over time
        strategy_evolution = self._analyze_strategy_evolution(
            actions, messages, exchanges, completions
        )
        
        results = {
            'negotiation_analysis': negotiation_analysis,
            'deception_analysis': deception_analysis,
            'reciprocity_analysis': reciprocity_analysis,
            'agent_strategies': agent_strategies,
            'strategy_evolution': strategy_evolution,
            'summary': self._generate_summary(
                agent_strategies,
                negotiation_analysis,
                deception_analysis,
                reciprocity_analysis
            )
        }
        
        return results
        
    def get_metrics(self) -> Dict[str, float]:
        """Get key strategy metrics"""
        results = self.get_results()
        
        metrics = {
            'negotiation_frequency': results['negotiation_analysis']['negotiation_frequency'],
            'deception_prevalence': results['deception_analysis']['deception_prevalence'],
            'reciprocity_score': results['reciprocity_analysis']['overall_reciprocity'],
            'strategy_diversity': results['agent_strategies']['strategy_diversity']
        }
        
        return metrics
        
    def _extract_private_thoughts(self) -> pd.DataFrame:
        """Extract private thoughts from events"""
        thoughts_events = self.processor.events_df[
            self.processor.events_df['event_type'] == 'private_thoughts'
        ].copy()
        
        if 'private_thoughts' in self.processor.events_df.columns:
            # Also get thoughts from agent actions
            action_thoughts = self.processor.events_df[
                (self.processor.events_df['event_type'] == 'agent_action') &
                (self.processor.events_df['private_thoughts'].notna())
            ][['agent_id', 'round', 'private_thoughts']].copy()
            
            thoughts_events = pd.concat([thoughts_events, action_thoughts], ignore_index=True)
            
        return thoughts_events
        
    def _analyze_negotiation_patterns(
        self, 
        messages: pd.DataFrame,
        exchanges: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze negotiation behaviors"""
        # Identify negotiation keywords
        negotiation_keywords = [
            'trade', 'exchange', 'deal', 'offer', 'propose',
            'if you', 'in return', 'quid pro quo', 'mutual'
        ]
        
        # Find negotiation messages
        negotiation_msgs = messages[messages['from_agent'] != 'system'].copy()
        
        if len(negotiation_msgs) == 0:
            return {
                'negotiation_frequency': 0.0,
                'successful_negotiations': 0,
                'negotiation_chains': [],
                'top_negotiators': []
            }
            
        # Detect negotiation content
        negotiation_msgs['is_negotiation'] = negotiation_msgs['content'].apply(
            lambda x: any(keyword in str(x).lower() for keyword in negotiation_keywords)
        )
        
        negotiation_count = negotiation_msgs['is_negotiation'].sum()
        negotiation_freq = negotiation_count / len(negotiation_msgs)
        
        # Track negotiation chains (back-and-forth exchanges)
        negotiation_chains = []
        processed_pairs = set()
        
        for idx, msg in negotiation_msgs[negotiation_msgs['is_negotiation']].iterrows():
            pair_key = tuple(sorted([msg['from_agent'], msg['to_agent']]))
            
            if pair_key not in processed_pairs:
                # Find related messages in this conversation
                chain_msgs = negotiation_msgs[
                    ((negotiation_msgs['from_agent'] == msg['from_agent']) & 
                     (negotiation_msgs['to_agent'] == msg['to_agent'])) |
                    ((negotiation_msgs['from_agent'] == msg['to_agent']) & 
                     (negotiation_msgs['to_agent'] == msg['from_agent']))
                ].sort_index()
                
                if len(chain_msgs) > 1:
                    # Check if exchange followed
                    exchange_after = exchanges[
                        (exchanges.index > idx) &
                        (((exchanges['from_agent'] == msg['from_agent']) & 
                          (exchanges['to_agent'] == msg['to_agent'])) |
                         ((exchanges['from_agent'] == msg['to_agent']) & 
                          (exchanges['to_agent'] == msg['from_agent'])))
                    ]
                    
                    negotiation_chains.append({
                        'agents': list(pair_key),
                        'message_count': len(chain_msgs),
                        'resulted_in_exchange': len(exchange_after) > 0,
                        'start_time': chain_msgs.index[0]
                    })
                    
                processed_pairs.add(pair_key)
                
        # Count successful negotiations
        successful_negotiations = sum(
            1 for chain in negotiation_chains if chain['resulted_in_exchange']
        )
        
        # Identify top negotiators
        if len(negotiation_msgs) > 0:
            negotiator_activity = negotiation_msgs[
                negotiation_msgs['is_negotiation']
            ]['from_agent'].value_counts()
            
            top_negotiators = negotiator_activity.head(3).to_dict()
        else:
            top_negotiators = {}
            
        return {
            'negotiation_frequency': negotiation_freq,
            'successful_negotiations': successful_negotiations,
            'negotiation_chains': negotiation_chains,
            'top_negotiators': top_negotiators,
            'total_negotiations': negotiation_count
        }
        
    def _analyze_deception_strategies(
        self,
        exchanges: pd.DataFrame,
        private_thoughts: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze deceptive behaviors"""
        # Direct deception from exchanges
        if len(exchanges) > 0 and 'was_truthful' in exchanges.columns:
            deceptive_exchanges = exchanges[exchanges['was_truthful'] == False]
            deception_count = len(deceptive_exchanges)
            total_exchanges = len(exchanges)
        else:
            deceptive_exchanges = pd.DataFrame()
            deception_count = 0
            total_exchanges = 0
        
        deception_prevalence = deception_count / total_exchanges if total_exchanges > 0 else 0
        
        # Analyze deception patterns
        deception_by_agent = {}
        if len(exchanges) > 0:
            for agent in self.processor.agents:
                agent_exchanges = exchanges[exchanges['from_agent'] == agent]
                if len(agent_exchanges) > 0:
                    agent_deception_rate = (agent_exchanges['was_truthful'] == False).mean()
                    deception_by_agent[agent] = {
                        'deception_rate': float(agent_deception_rate),
                        'deceptive_exchanges': int((agent_exchanges['was_truthful'] == False).sum()),
                        'total_exchanges': len(agent_exchanges)
                    }
                    
        # Analyze deception keywords in private thoughts
        deception_keywords = [
            'lie', 'deceive', 'false', 'mislead', 'trick',
            'pretend', 'fake', 'withhold', 'strategic'
        ]
        
        strategic_thinking = []
        if len(private_thoughts) > 0:
            for _, thought in private_thoughts.iterrows():
                thought_text = str(thought.get('private_thoughts', '')).lower()
                if any(keyword in thought_text for keyword in deception_keywords):
                    strategic_thinking.append({
                        'agent': thought.get('agent_id'),
                        'round': thought.get('round'),
                        'context': thought_text[:200]  # First 200 chars
                    })
                    
        # Classify deception strategies
        deception_strategies = {}
        for agent, data in deception_by_agent.items():
            if data['deception_rate'] == 0:
                strategy = "Honest"
            elif data['deception_rate'] < 0.2:
                strategy = "Occasional Deceiver"
            elif data['deception_rate'] < 0.5:
                strategy = "Strategic Deceiver"
            else:
                strategy = "Habitual Deceiver"
                
            deception_strategies[agent] = strategy
            
        return {
            'deception_prevalence': deception_prevalence,
            'deception_by_agent': deception_by_agent,
            'deception_strategies': deception_strategies,
            'strategic_thinking_instances': len(strategic_thinking),
            'total_deceptive_exchanges': deception_count
        }
        
    def _analyze_reciprocity_patterns(
        self,
        messages: pd.DataFrame,
        exchanges: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze reciprocity in interactions"""
        reciprocity_scores = {}
        reciprocity_chains = []
        
        # For each agent pair, analyze reciprocity
        for agent1 in self.processor.agents:
            reciprocity_scores[agent1] = {}
            
            for agent2 in self.processor.agents:
                if agent1 == agent2:
                    continue
                    
                # Count exchanges in both directions
                a1_to_a2 = len(exchanges[
                    (exchanges['from_agent'] == agent1) & 
                    (exchanges['to_agent'] == agent2)
                ])
                a2_to_a1 = len(exchanges[
                    (exchanges['from_agent'] == agent2) & 
                    (exchanges['to_agent'] == agent1)
                ])
                
                # Calculate reciprocity score
                if a1_to_a2 + a2_to_a1 > 0:
                    reciprocity = min(a1_to_a2, a2_to_a1) / max(a1_to_a2, a2_to_a1)
                else:
                    reciprocity = 0
                    
                reciprocity_scores[agent1][agent2] = reciprocity
                
                # Track reciprocity chains (exchange followed by return exchange)
                if a1_to_a2 > 0 and a2_to_a1 > 0:
                    reciprocity_chains.append({
                        'agents': [agent1, agent2],
                        'exchanges': a1_to_a2 + a2_to_a1,
                        'balance': abs(a1_to_a2 - a2_to_a1),
                        'reciprocity_score': reciprocity
                    })
                    
        # Calculate overall reciprocity
        all_scores = []
        for agent_scores in reciprocity_scores.values():
            all_scores.extend(agent_scores.values())
            
        overall_reciprocity = np.mean(all_scores) if all_scores else 0
        
        # Identify reciprocity patterns
        reciprocity_patterns = {}
        for agent in self.processor.agents:
            agent_reciprocity = np.mean(list(reciprocity_scores[agent].values()))
            
            if agent_reciprocity > 0.8:
                pattern = "Strong Reciprocator"
            elif agent_reciprocity > 0.5:
                pattern = "Balanced Reciprocator"
            elif agent_reciprocity > 0.2:
                pattern = "Selective Reciprocator"
            else:
                pattern = "Non-Reciprocator"
                
            reciprocity_patterns[agent] = pattern
            
        return {
            'overall_reciprocity': overall_reciprocity,
            'reciprocity_scores': reciprocity_scores,
            'reciprocity_patterns': reciprocity_patterns,
            'reciprocity_chains': reciprocity_chains,
            'strong_reciprocal_pairs': len([
                chain for chain in reciprocity_chains 
                if chain['reciprocity_score'] > 0.8
            ])
        }
        
    def _classify_agent_strategies(
        self,
        agent_summary: pd.DataFrame,
        negotiation: Dict[str, Any],
        deception: Dict[str, Any],
        reciprocity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classify overall agent strategies"""
        agent_strategies = {}
        
        for agent in self.processor.agents:
            # Get agent characteristics
            agent_data = agent_summary[agent_summary['agent_id'] == agent]
            
            if len(agent_data) == 0:
                agent_strategies[agent] = "Unknown"
                continue
                
            agent_data = agent_data.iloc[0]
            
            # Get strategy components
            is_negotiator = agent in negotiation['top_negotiators']
            deception_strategy = deception['deception_strategies'].get(agent, "Unknown")
            reciprocity_pattern = reciprocity['reciprocity_patterns'].get(agent, "Unknown")
            
            # Calculate activity level
            activity_score = (
                agent_data['messages_sent'] + 
                agent_data['info_pieces_shared'] + 
                agent_data['tasks_completed']
            ) / agent_data['rounds_active'] if agent_data['rounds_active'] > 0 else 0
            
            # Classify overall strategy
            if activity_score < 1:
                strategy = "Passive Observer"
            elif deception_strategy in ["Habitual Deceiver", "Strategic Deceiver"] and is_negotiator:
                strategy = "Machiavellian"
            elif reciprocity_pattern == "Strong Reciprocator" and deception_strategy == "Honest":
                strategy = "Cooperative Partner"
            elif is_negotiator and reciprocity_pattern in ["Balanced Reciprocator", "Strong Reciprocator"]:
                strategy = "Diplomatic Trader"
            elif agent_data['tasks_completed'] > agent_data['info_pieces_shared']:
                strategy = "Competitive Achiever"
            elif agent_data['info_pieces_shared'] > agent_data['tasks_completed'] * 2:
                strategy = "Information Broker"
            else:
                strategy = "Balanced Player"
                
            agent_strategies[agent] = strategy
            
        # Calculate strategy diversity
        strategy_counts = pd.Series(list(agent_strategies.values())).value_counts()
        strategy_diversity = len(strategy_counts) / len(agent_strategies) if agent_strategies else 0
        
        return {
            'classifications': agent_strategies,
            'strategy_distribution': strategy_counts.to_dict(),
            'strategy_diversity': strategy_diversity
        }
        
    def _analyze_strategy_evolution(
        self,
        actions: pd.DataFrame,
        messages: pd.DataFrame,
        exchanges: pd.DataFrame,
        completions: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze how strategies evolve over time"""
        if 'round' not in actions.columns or len(self.processor.rounds) < 3:
            return {
                'early_vs_late_cooperation': 0.0,
                'strategy_shifts': [],
                'adaptation_score': 0.0
            }
            
        # Divide simulation into early and late phases
        mid_round = self.processor.rounds[len(self.processor.rounds) // 2]
        
        early_exchanges = exchanges[exchanges['round'] <= mid_round]
        late_exchanges = exchanges[exchanges['round'] > mid_round]
        
        # Compare cooperation levels
        early_truthfulness = early_exchanges['was_truthful'].mean() if len(early_exchanges) > 0 else 0
        late_truthfulness = late_exchanges['was_truthful'].mean() if len(late_exchanges) > 0 else 0
        
        cooperation_change = late_truthfulness - early_truthfulness
        
        # Track strategy shifts (changes in behavior patterns)
        strategy_shifts = []
        
        for agent in self.processor.agents:
            early_actions = actions[
                (actions['agent_id'] == agent) & 
                (actions['round'] <= mid_round)
            ]
            late_actions = actions[
                (actions['agent_id'] == agent) & 
                (actions['round'] > mid_round)
            ]
            
            if len(early_actions) > 0 and len(late_actions) > 0:
                # Compare action patterns
                early_comm_ratio = early_actions['is_communication'].mean()
                late_comm_ratio = late_actions['is_communication'].mean()
                
                if abs(early_comm_ratio - late_comm_ratio) > 0.3:
                    strategy_shifts.append({
                        'agent': agent,
                        'shift_type': 'communication_change',
                        'early_ratio': early_comm_ratio,
                        'late_ratio': late_comm_ratio
                    })
                    
        # Calculate adaptation score
        adaptation_score = len(strategy_shifts) / len(self.processor.agents)
        
        return {
            'early_vs_late_cooperation': cooperation_change,
            'strategy_shifts': strategy_shifts,
            'adaptation_score': adaptation_score,
            'early_truthfulness': early_truthfulness,
            'late_truthfulness': late_truthfulness
        }
        
    def _generate_summary(
        self,
        agent_strategies: Dict[str, Any],
        negotiation: Dict[str, Any],
        deception: Dict[str, Any],
        reciprocity: Dict[str, Any]
    ) -> str:
        """Generate summary of strategic behavior analysis"""
        # Get dominant strategy
        strategy_dist = agent_strategies['strategy_distribution']
        dominant_strategy = max(strategy_dist, key=strategy_dist.get) if strategy_dist else "Unknown"
        
        summary = f"""
Strategic behavior analysis reveals diverse approaches with "{dominant_strategy}" 
as the most common strategy ({strategy_dist.get(dominant_strategy, 0)} agents).

Negotiation occurs in {negotiation['negotiation_frequency']:.1%} of messages, 
with {negotiation['successful_negotiations']} successful negotiation chains leading 
to information exchanges.

Deception is present in {deception['deception_prevalence']:.1%} of information 
exchanges, with {sum(1 for s in deception['deception_strategies'].values() if s != 'Honest')} 
agents employing some form of deceptive strategy.

Reciprocity analysis shows an overall score of {reciprocity['overall_reciprocity']:.2f}, 
with {reciprocity['strong_reciprocal_pairs']} strongly reciprocal agent pairs identified.

Strategy diversity index is {agent_strategies['strategy_diversity']:.2f}, indicating 
{'high' if agent_strategies['strategy_diversity'] > 0.7 else 'moderate'} 
behavioral diversity in the simulation.
"""
        return summary.strip()
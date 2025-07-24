"""
Information Flow Analyzer

Analyzes how information moves through the network, including
truthfulness, asymmetry, and strategic sharing patterns.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer


class InformationFlowAnalyzer(BaseAnalyzer):
    """Analyzes information flow and asymmetry patterns"""
    
    @property
    def name(self) -> str:
        return "Information Flow"
        
    def analyze(self) -> Dict[str, Any]:
        """Perform information flow analysis"""
        # Get information exchange data
        exchanges = self.processor.get_information_exchanges()
        info_matrix = self.processor.get_information_flow_matrix()
        agent_summary = self.processor.get_agent_summary()
        
        # Calculate core metrics
        flow_metrics = self._analyze_flow_patterns(exchanges, agent_summary)
        asymmetry_metrics = self.metrics_calc.calculate_information_asymmetry(info_matrix)
        trust_metrics = self.metrics_calc.calculate_trust_metrics(exchanges)
        
        # Identify information brokers and bottlenecks
        brokers = self._identify_information_brokers(info_matrix, agent_summary)
        
        # Analyze sharing strategies
        sharing_strategies = self._analyze_sharing_strategies(exchanges, agent_summary)
        
        # Temporal analysis
        temporal_patterns = self._analyze_temporal_patterns(exchanges)
        
        results = {
            'flow_metrics': flow_metrics,
            'asymmetry_metrics': asymmetry_metrics,
            'trust_metrics': trust_metrics,
            'information_matrix': info_matrix,
            'information_brokers': brokers,
            'sharing_strategies': sharing_strategies,
            'temporal_patterns': temporal_patterns,
            'summary': self._generate_summary(
                flow_metrics, asymmetry_metrics, trust_metrics, brokers
            )
        }
        
        return results
        
    def get_metrics(self) -> Dict[str, float]:
        """Get key information flow metrics"""
        results = self.get_results()
        
        metrics = {}
        metrics.update(results['flow_metrics'])
        metrics.update(results['asymmetry_metrics'])
        metrics.update(results['trust_metrics'])
        
        return metrics
        
    def _analyze_flow_patterns(
        self, 
        exchanges: pd.DataFrame,
        agent_summary: pd.DataFrame
    ) -> Dict[str, float]:
        """Analyze overall information flow patterns"""
        if len(exchanges) == 0:
            return {
                'total_info_shared': 0,
                'avg_info_per_exchange': 0.0,
                'sharing_rate': 0.0,
                'reciprocal_sharing_rate': 0.0,
                'hoarding_index': 0.0
            }
            
        total_info = exchanges['info_count'].sum()
        n_agents = len(agent_summary)
        
        metrics = {
            'total_info_shared': total_info,
            'avg_info_per_exchange': exchanges['info_count'].mean(),
            'sharing_rate': len(exchanges) / n_agents if n_agents > 0 else 0
        }
        
        # Calculate reciprocal sharing rate
        reciprocal_pairs = 0
        total_pairs = 0
        
        for agent1 in agent_summary['agent_id']:
            for agent2 in agent_summary['agent_id']:
                if agent1 >= agent2:
                    continue
                    
                shared_1to2 = len(exchanges[
                    (exchanges['from_agent'] == agent1) & 
                    (exchanges['to_agent'] == agent2)
                ])
                shared_2to1 = len(exchanges[
                    (exchanges['from_agent'] == agent2) & 
                    (exchanges['to_agent'] == agent1)
                ])
                
                if shared_1to2 > 0 or shared_2to1 > 0:
                    total_pairs += 1
                    if shared_1to2 > 0 and shared_2to1 > 0:
                        reciprocal_pairs += 1
                        
        metrics['reciprocal_sharing_rate'] = (
            reciprocal_pairs / total_pairs if total_pairs > 0 else 0
        )
        
        # Calculate hoarding index (agents who receive more than they share)
        hoarding_scores = []
        for _, agent_data in agent_summary.iterrows():
            shared = agent_data['info_pieces_shared']
            received = agent_data['info_pieces_received']
            
            if shared + received > 0:
                hoarding_score = (received - shared) / (received + shared)
                hoarding_scores.append(hoarding_score)
                
        metrics['hoarding_index'] = np.mean(hoarding_scores) if hoarding_scores else 0
        
        return metrics
        
    def _identify_information_brokers(
        self, 
        info_matrix: pd.DataFrame,
        agent_summary: pd.DataFrame
    ) -> Dict[str, Dict[str, Any]]:
        """Identify agents who act as information brokers"""
        brokers = {}
        
        for agent in info_matrix.index:
            # Calculate broker metrics
            info_received = info_matrix[agent].sum()
            info_shared = info_matrix.loc[agent].sum()
            total_flow = info_received + info_shared
            
            # Count unique partners
            receive_partners = (info_matrix[agent] > 0).sum()
            share_partners = (info_matrix.loc[agent] > 0).sum()
            
            # Betweenness-like metric (simplified)
            # How much info flows through this agent
            flow_through = min(info_received, info_shared)
            
            # Classification
            if total_flow == 0:
                broker_type = "Isolated"
            elif info_shared > info_received * 1.5:
                broker_type = "Information Source"
            elif info_received > info_shared * 1.5:
                broker_type = "Information Sink"
            elif flow_through > info_matrix.values.mean() * 2:
                broker_type = "Central Broker"
            elif receive_partners > len(info_matrix) * 0.5 or share_partners > len(info_matrix) * 0.5:
                broker_type = "Hub"
            else:
                broker_type = "Regular"
                
            brokers[agent] = {
                'type': broker_type,
                'info_received': int(info_received),
                'info_shared': int(info_shared),
                'flow_through': int(flow_through),
                'connectivity': (receive_partners + share_partners) / (2 * (len(info_matrix) - 1))
            }
            
        return brokers
        
    def _analyze_sharing_strategies(
        self,
        exchanges: pd.DataFrame,
        agent_summary: pd.DataFrame
    ) -> Dict[str, str]:
        """Analyze information sharing strategies by agent"""
        strategies = {}
        
        for agent in agent_summary['agent_id']:
            agent_data = agent_summary[agent_summary['agent_id'] == agent].iloc[0]
            agent_exchanges = exchanges[exchanges['from_agent'] == agent]
            
            if len(agent_exchanges) == 0:
                strategies[agent] = "Non-sharer"
                continue
                
            # Calculate strategy indicators
            truthfulness_rate = agent_exchanges['was_truthful'].mean()
            avg_pieces_per_share = agent_exchanges['info_count'].mean()
            
            # Timing analysis (early vs late sharer)
            if 'round' in agent_exchanges.columns:
                avg_share_round = agent_exchanges['round'].mean()
                early_sharer = avg_share_round < exchanges['round'].mean()
            else:
                early_sharer = False
                
            # Classify strategy
            if truthfulness_rate < 0.5:
                strategy = "Deceptive"
            elif truthfulness_rate < 0.8:
                strategy = "Strategic Deceiver"
            elif avg_pieces_per_share > exchanges['info_count'].mean() * 1.5:
                strategy = "Generous Sharer"
            elif early_sharer:
                strategy = "Early Cooperator"
            elif agent_data['info_pieces_shared'] < agent_data['info_pieces_received']:
                strategy = "Selective Reciprocator"
            else:
                strategy = "Reliable Partner"
                
            strategies[agent] = strategy
            
        return strategies
        
    def _analyze_temporal_patterns(self, exchanges: pd.DataFrame) -> Dict[str, Any]:
        """Analyze how information sharing changes over time"""
        if len(exchanges) == 0 or 'round' not in exchanges.columns:
            return {
                'sharing_by_round': [],
                'truthfulness_by_round': [],
                'peak_sharing_round': None
            }
            
        # Group by round
        round_analysis = exchanges.groupby('round').agg({
            'info_count': ['sum', 'mean', 'count'],
            'was_truthful': 'mean'
        })
        
        round_analysis.columns = ['total_shared', 'avg_per_exchange', 'exchange_count', 'truthfulness_rate']
        
        # Find peak sharing round
        peak_round = round_analysis['total_shared'].idxmax() if len(round_analysis) > 0 else None
        
        return {
            'sharing_by_round': round_analysis['total_shared'].to_dict(),
            'truthfulness_by_round': round_analysis['truthfulness_rate'].to_dict(),
            'peak_sharing_round': int(peak_round) if peak_round is not None else None,
            'round_summary': round_analysis.to_dict()
        }
        
    def _generate_summary(
        self,
        flow_metrics: Dict[str, float],
        asymmetry_metrics: Dict[str, float],
        trust_metrics: Dict[str, float],
        brokers: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate summary of information flow analysis"""
        # Count broker types
        broker_types = [b['type'] for b in brokers.values()]
        central_brokers = sum(1 for t in broker_types if t == "Central Broker")
        
        summary = f"""
Information flow analysis shows {flow_metrics['total_info_shared']} pieces of 
information shared across the network, averaging {flow_metrics['avg_info_per_exchange']:.1f} 
pieces per exchange.

The network exhibits a Gini coefficient of {asymmetry_metrics['gini_coefficient']:.3f}, 
indicating {'high' if asymmetry_metrics['gini_coefficient'] > 0.5 else 'moderate'} 
inequality in information distribution. The asymmetry index of 
{asymmetry_metrics['asymmetry_index']:.3f} shows 
{'significant' if asymmetry_metrics['asymmetry_index'] > 0.5 else 'balanced'} 
directional bias in exchanges.

Trust metrics reveal {trust_metrics['overall_truthfulness']:.1%} truthfulness rate 
with {trust_metrics['deception_rate']:.1%} of exchanges containing false information. 
Trust variance of {trust_metrics['trust_variance']:.3f} indicates 
{'consistent' if trust_metrics['trust_variance'] < 0.1 else 'variable'} 
trustworthiness across agents.

The network has {central_brokers} central broker(s) facilitating information flow. 
The hoarding index of {flow_metrics['hoarding_index']:.3f} suggests 
{'significant hoarding' if flow_metrics['hoarding_index'] > 0.2 else 'balanced sharing'} 
behavior.
"""
        return summary.strip()
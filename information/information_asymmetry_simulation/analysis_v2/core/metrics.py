"""
Core Metrics Calculator

Provides efficient calculation of key metrics used across different analyzers.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats


class MetricsCalculator:
    """Calculates core metrics from processed event data"""
    
    @staticmethod
    def calculate_communication_efficiency(
        messages_df: pd.DataFrame, 
        info_exchanges_df: pd.DataFrame
    ) -> float:
        """
        Calculate ratio of information exchanges to total messages.
        
        Higher ratio indicates more efficient communication.
        """
        if len(messages_df) == 0:
            return 0.0
            
        # Count non-system messages
        real_messages = messages_df[messages_df['from_agent'] != 'system']
        
        if len(real_messages) == 0:
            return 0.0
            
        return len(info_exchanges_df) / len(real_messages)
        
    @staticmethod
    def calculate_information_asymmetry(
        info_matrix: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate measures of information asymmetry.
        
        Returns:
            - gini_coefficient: Inequality in information distribution
            - asymmetry_index: Directional asymmetry in exchanges
            - centralization: Degree of centralization in network
        """
        # Flatten matrix values
        all_values = info_matrix.values.flatten()
        
        # Gini coefficient for inequality
        gini = MetricsCalculator._calculate_gini(all_values)
        
        # Asymmetry index (how imbalanced are exchanges)
        asymmetry_scores = []
        for i in range(len(info_matrix)):
            for j in range(i + 1, len(info_matrix)):
                val1 = info_matrix.iloc[i, j]
                val2 = info_matrix.iloc[j, i]
                if val1 + val2 > 0:
                    asymmetry = abs(val1 - val2) / (val1 + val2)
                    asymmetry_scores.append(asymmetry)
                    
        asymmetry_index = np.mean(asymmetry_scores) if asymmetry_scores else 0
        
        # Centralization (how much flow goes through central agents)
        total_flow = info_matrix.sum().sum()
        if total_flow == 0:
            centralization = 0
        else:
            agent_flows = info_matrix.sum(axis=0) + info_matrix.sum(axis=1)
            max_flow = agent_flows.max()
            centralization = (max_flow * len(agent_flows) - total_flow) / (
                (len(agent_flows) - 1) * total_flow
            )
            
        return {
            'gini_coefficient': gini,
            'asymmetry_index': asymmetry_index,
            'centralization': centralization
        }
        
    @staticmethod
    def calculate_task_performance_metrics(
        completions_df: pd.DataFrame,
        agent_summary_df: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate task-related performance metrics"""
        if len(completions_df) == 0:
            return {
                'overall_success_rate': 0.0,
                'bonus_capture_rate': 0.0,
                'avg_completion_round': 0.0,
                'competitive_advantage': 0.0
            }
            
        # Overall success rate
        success_rate = completions_df['success'].mean()
        
        # Bonus capture rate (how often first completions get bonus)
        possible_bonuses = completions_df['task_id'].nunique()
        actual_bonuses = completions_df['got_bonus'].sum()
        bonus_rate = actual_bonuses / possible_bonuses if possible_bonuses > 0 else 0
        
        # Average completion round
        avg_round = completions_df[completions_df['success']]['round'].mean()
        
        # Competitive advantage (correlation between early action and success)
        if len(agent_summary_df) > 0:
            # Calculate correlation between task completion rate and bonus rate
            agent_summary_df['completion_rate'] = (
                agent_summary_df['tasks_completed'] / 
                agent_summary_df['rounds_active'].clip(lower=1)
            )
            agent_summary_df['bonus_rate'] = (
                agent_summary_df['tasks_with_bonus'] / 
                agent_summary_df['tasks_completed'].clip(lower=1)
            )
            
            competitive_advantage = agent_summary_df[
                ['completion_rate', 'bonus_rate']
            ].corr().iloc[0, 1]
        else:
            competitive_advantage = 0.0
            
        return {
            'overall_success_rate': success_rate,
            'bonus_capture_rate': bonus_rate,
            'avg_completion_round': avg_round,
            'competitive_advantage': competitive_advantage
        }
        
    @staticmethod
    def calculate_trust_metrics(
        info_exchanges_df: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate trust-related metrics from information exchanges"""
        if len(info_exchanges_df) == 0:
            return {
                'overall_truthfulness': 1.0,
                'deception_rate': 0.0,
                'trust_variance': 0.0
            }
            
        # Overall truthfulness
        truthfulness = info_exchanges_df['was_truthful'].mean()
        
        # Deception rate
        deception_rate = 1 - truthfulness
        
        # Trust variance (how much truthfulness varies by agent)
        agent_truthfulness = info_exchanges_df.groupby('from_agent')['was_truthful'].mean()
        trust_variance = agent_truthfulness.var() if len(agent_truthfulness) > 1 else 0
        
        return {
            'overall_truthfulness': truthfulness,
            'deception_rate': deception_rate,
            'trust_variance': trust_variance
        }
        
    @staticmethod
    def calculate_network_metrics(
        comm_matrix: pd.DataFrame,
        info_matrix: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate network structure metrics"""
        # Density (fraction of possible connections used)
        n_agents = len(comm_matrix)
        possible_connections = n_agents * (n_agents - 1)
        actual_connections = (comm_matrix > 0).sum().sum()
        density = actual_connections / possible_connections if possible_connections > 0 else 0
        
        # Reciprocity (fraction of mutual connections)
        reciprocal_pairs = 0
        for i in range(n_agents):
            for j in range(i + 1, n_agents):
                if comm_matrix.iloc[i, j] > 0 and comm_matrix.iloc[j, i] > 0:
                    reciprocal_pairs += 1
                    
        reciprocity = (2 * reciprocal_pairs) / actual_connections if actual_connections > 0 else 0
        
        # Clustering coefficient (simplified)
        # For each agent, what fraction of their contacts also contact each other
        clustering_scores = []
        for agent in comm_matrix.index:
            # Find agents this one communicates with
            contacts = comm_matrix.columns[
                (comm_matrix.loc[agent] > 0) | (comm_matrix[agent] > 0)
            ].tolist()
            
            if len(contacts) > 1:
                # Count connections between contacts
                contact_connections = 0
                possible_contact_connections = len(contacts) * (len(contacts) - 1)
                
                for i, c1 in enumerate(contacts):
                    for c2 in contacts[i + 1:]:
                        if comm_matrix.loc[c1, c2] > 0 or comm_matrix.loc[c2, c1] > 0:
                            contact_connections += 2
                            
                clustering = contact_connections / possible_contact_connections
                clustering_scores.append(clustering)
                
        avg_clustering = np.mean(clustering_scores) if clustering_scores else 0
        
        return {
            'network_density': density,
            'reciprocity': reciprocity,
            'clustering_coefficient': avg_clustering
        }
        
    @staticmethod
    def _calculate_gini(values: np.ndarray) -> float:
        """Calculate Gini coefficient for inequality measurement"""
        # Remove zeros and negative values
        values = values[values > 0]
        
        if len(values) == 0:
            return 0.0
            
        # Sort values
        sorted_values = np.sort(values)
        n = len(sorted_values)
        
        # Calculate Gini
        cumsum = np.cumsum(sorted_values)
        gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * cumsum[-1]) - (n + 1) / n
        
        return float(np.clip(gini, 0, 1))
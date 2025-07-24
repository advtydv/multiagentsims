"""
Event Processor for Data Normalization and Extraction

Provides efficient methods to extract specific event types and
compute derived data structures from the raw event stream.
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict


class EventProcessor:
    """Processes and extracts structured data from event DataFrame"""
    
    def __init__(self, events_df: pd.DataFrame):
        """
        Initialize the event processor.
        
        Args:
            events_df: DataFrame of events from DataLoader
        """
        self.events_df = events_df
        self._agents = None
        self._rounds = None
        
    @property
    def agents(self) -> List[str]:
        """Get list of unique agent IDs"""
        if self._agents is None:
            # Extract from multiple event types to ensure completeness
            agent_cols = ['agent_id', 'from_agent', 'to_agent']
            agents = set()
            
            for col in agent_cols:
                if col in self.events_df.columns:
                    agents.update(self.events_df[col].dropna().unique())
                    
            # Filter out system messages
            agents.discard('system')
            self._agents = sorted(list(agents))
            
        return self._agents
        
    @property
    def rounds(self) -> List[int]:
        """Get list of round numbers"""
        if self._rounds is None:
            if 'round' in self.events_df.columns:
                self._rounds = sorted(self.events_df['round'].dropna().unique().astype(int).tolist())
            else:
                self._rounds = []
                
        return self._rounds
        
    def get_messages(self) -> pd.DataFrame:
        """Extract all messages with enhanced metadata"""
        messages = self.events_df[self.events_df['event_type'] == 'message'].copy()
        
        if len(messages) == 0:
            return pd.DataFrame()
            
        # Add derived fields
        messages['is_broadcast'] = messages['msg_type'] == 'broadcast'
        messages['is_system'] = messages['from_agent'] == 'system'
        
        # Extract round number from nearest agent action
        messages['round'] = self._get_round_for_events(messages.index)
        
        return messages
        
    def get_information_exchanges(self) -> pd.DataFrame:
        """Extract information exchange events"""
        exchanges = self.events_df[self.events_df['event_type'] == 'information_exchange'].copy()
        
        if len(exchanges) == 0:
            return pd.DataFrame()
            
        # Parse information list
        exchanges['info_count'] = exchanges['information'].apply(
            lambda x: len(json.loads(x)) if pd.notna(x) else 0
        )
        
        # Add round information
        exchanges['round'] = self._get_round_for_events(exchanges.index)
        
        return exchanges
        
    def get_task_completions(self) -> pd.DataFrame:
        """Extract task completion events"""
        completions = self.events_df[self.events_df['event_type'] == 'task_completion'].copy()
        
        if len(completions) == 0:
            return pd.DataFrame()
            
        # Add round information
        completions['round'] = self._get_round_for_events(completions.index)
        
        # Calculate completion order for bonus tracking
        completions['completion_order'] = completions.groupby('task_id').cumcount() + 1
        completions['got_bonus'] = completions['completion_order'] == 1
        
        return completions
        
    def get_agent_actions(self) -> pd.DataFrame:
        """Extract agent actions with metadata"""
        actions = self.events_df[self.events_df['event_type'] == 'agent_action'].copy()
        
        if len(actions) == 0:
            return pd.DataFrame()
            
        # Categorize actions
        actions['is_communication'] = actions['action_type'].isin(['send_message', 'broadcast'])
        actions['is_information_share'] = actions['action_type'] == 'send_information'
        actions['is_task_submit'] = actions['action_type'] == 'submit_task'
        
        return actions
        
    def get_communication_matrix(self) -> pd.DataFrame:
        """Build communication frequency matrix between agents"""
        messages = self.get_messages()
        
        if len(messages) == 0:
            return pd.DataFrame(0, index=self.agents, columns=self.agents)
            
        # Count direct messages between agents
        direct_msgs = messages[
            (messages['msg_type'] == 'direct') & 
            (~messages['is_system'])
        ]
        
        # Create frequency matrix
        comm_matrix = pd.crosstab(
            direct_msgs['from_agent'], 
            direct_msgs['to_agent'],
            margins=False
        )
        
        # Ensure all agents are represented
        comm_matrix = comm_matrix.reindex(
            index=self.agents, 
            columns=self.agents, 
            fill_value=0
        )
        
        return comm_matrix
        
    def get_information_flow_matrix(self) -> pd.DataFrame:
        """Build information sharing matrix with truthfulness rates"""
        exchanges = self.get_information_exchanges()
        
        if len(exchanges) == 0:
            return pd.DataFrame(0, index=self.agents, columns=self.agents)
            
        # Calculate sharing frequency and truthfulness
        flow_data = exchanges.groupby(['from_agent', 'to_agent']).agg({
            'info_count': 'sum',
            'was_truthful': ['sum', 'count']
        })
        
        # Calculate truthfulness rate
        flow_data.columns = ['total_shared', 'truthful_count', 'exchange_count']
        flow_data['truthfulness_rate'] = flow_data['truthful_count'] / flow_data['exchange_count']
        
        # Create matrix for total information shared
        info_matrix = flow_data['total_shared'].unstack(fill_value=0)
        
        # Ensure all agents are represented
        info_matrix = info_matrix.reindex(
            index=self.agents, 
            columns=self.agents, 
            fill_value=0
        )
        
        return info_matrix
        
    def get_round_summary(self) -> pd.DataFrame:
        """Summarize activity by round"""
        if not self.rounds:
            return pd.DataFrame()
            
        round_data = []
        
        messages = self.get_messages()
        exchanges = self.get_information_exchanges()
        completions = self.get_task_completions()
        actions = self.get_agent_actions()
        
        for round_num in self.rounds:
            # Filter data for this round
            round_msgs = messages[messages['round'] == round_num]
            round_exchanges = exchanges[exchanges['round'] == round_num]
            round_completions = completions[completions['round'] == round_num]
            round_actions = actions[actions['round'] == round_num]
            
            round_data.append({
                'round': round_num,
                'message_count': len(round_msgs),
                'broadcast_count': round_msgs['is_broadcast'].sum(),
                'information_exchanges': len(round_exchanges),
                'total_info_shared': round_exchanges['info_count'].sum(),
                'truthful_exchanges': round_exchanges['was_truthful'].sum(),
                'tasks_completed': round_completions['success'].sum(),
                'unique_agents_active': round_actions['agent_id'].nunique(),
                'total_actions': len(round_actions)
            })
            
        return pd.DataFrame(round_data)
        
    def get_agent_summary(self) -> pd.DataFrame:
        """Summarize activity by agent"""
        agent_data = []
        
        messages = self.get_messages()
        exchanges = self.get_information_exchanges()
        completions = self.get_task_completions()
        actions = self.get_agent_actions()
        
        for agent in self.agents:
            # Messages sent
            sent_msgs = messages[messages['from_agent'] == agent]
            received_msgs = messages[messages['to_agent'] == agent]
            
            # Information exchanges
            sent_info = exchanges[exchanges['from_agent'] == agent]
            received_info = exchanges[exchanges['to_agent'] == agent]
            
            # Task completions
            agent_tasks = completions[completions['agent_id'] == agent]
            
            # Actions
            agent_actions = actions[actions['agent_id'] == agent]
            
            agent_data.append({
                'agent_id': agent,
                'messages_sent': int(len(sent_msgs)),
                'messages_received': int(len(received_msgs)),
                'broadcasts_sent': int(sent_msgs['is_broadcast'].sum()),
                'info_pieces_shared': int(sent_info['info_count'].sum()),
                'info_pieces_received': int(received_info['info_count'].sum()),
                'truthful_shares': int(sent_info['was_truthful'].sum()),
                'deceptive_shares': int((~sent_info['was_truthful']).sum()),
                'tasks_completed': int(agent_tasks['success'].sum()),
                'tasks_with_bonus': int(agent_tasks['got_bonus'].sum()),
                'total_actions': int(len(agent_actions)),
                'rounds_active': int(agent_actions['round'].nunique())
            })
            
        return pd.DataFrame(agent_data)
        
    def _get_round_for_events(self, timestamps: pd.DatetimeIndex) -> List[Optional[int]]:
        """Get round number for events based on timestamp"""
        # Get agent actions with rounds
        round_markers = self.events_df[
            (self.events_df['event_type'] == 'agent_action') & 
            (self.events_df['round'].notna())
        ][['round']].copy()
        
        if len(round_markers) == 0:
            return [None] * len(timestamps)
            
        # For each timestamp, find the nearest previous agent action
        rounds = []
        for ts in timestamps:
            prev_actions = round_markers[round_markers.index <= ts]
            if len(prev_actions) > 0:
                rounds.append(int(prev_actions.iloc[-1]['round']))
            else:
                rounds.append(None)
                
        return rounds
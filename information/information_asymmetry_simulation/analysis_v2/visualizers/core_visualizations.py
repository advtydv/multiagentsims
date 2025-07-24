"""
Core Visualizations

Implements the 5 essential visualizations that capture the essence
of information asymmetry dynamics:

1. Information Flow Network - trust networks and bottlenecks
2. Task Completion Timeline - competitive dynamics
3. Agent Performance Dashboard - strategy assessment  
4. Communication Efficiency Heatmap - strategic patterns
5. Round-by-Round Dynamics - simulation progression
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import networkx as nx
from .base_visualizer import BaseVisualizer, COLORS, PALETTES


class CoreVisualizer(BaseVisualizer):
    """Creates the 5 core visualizations for information asymmetry analysis"""
    
    def __init__(self, analysis_results: Dict[str, Any], output_dir: str):
        """
        Initialize the core visualizer.
        
        Args:
            analysis_results: Combined results from all analyzers
            output_dir: Directory to save visualizations
        """
        super().__init__(output_dir)
        self.results = analysis_results
        
    def create_all_visualizations(self):
        """Create all 5 core visualizations"""
        print("\nCreating core visualizations...")
        
        # 1. Information Flow Network
        self._create_information_flow_network()
        print("✓ Information flow network created")
        
        # 2. Task Completion Timeline
        self._create_task_completion_timeline()
        print("✓ Task completion timeline created")
        
        # 3. Agent Performance Dashboard
        self._create_agent_performance_dashboard()
        print("✓ Agent performance dashboard created")
        
        # 4. Communication Efficiency Heatmap
        self._create_communication_efficiency_heatmap()
        print("✓ Communication efficiency heatmap created")
        
        # 5. Round-by-Round Dynamics
        self._create_round_dynamics()
        print("✓ Round-by-round dynamics created")
        
    def _create_information_flow_network(self):
        """
        Create network visualization showing information flow patterns.
        Edge thickness = volume, color = truthfulness rate
        """
        # Get data
        info_matrix = self.results['information_flow']['information_matrix']
        trust_data = self._calculate_trust_rates()
        brokers = self.results['information_flow']['information_brokers']
        
        # Create figure
        fig, ax = self.create_figure(figsize=(12, 10), 
                                    title="Information Flow Network")
        
        # Create network graph
        G = nx.DiGraph()
        
        # Add nodes with broker types
        for agent in info_matrix.index:
            broker_type = brokers[agent]['type']
            G.add_node(agent, broker_type=broker_type)
            
        # Add edges with weights and trust rates
        for from_agent in info_matrix.index:
            for to_agent in info_matrix.columns:
                weight = info_matrix.loc[from_agent, to_agent]
                if weight > 0:
                    trust_rate = trust_data.get((from_agent, to_agent), 1.0)
                    G.add_edge(from_agent, to_agent, weight=weight, trust=trust_rate)
                    
        # Layout
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        
        # Draw nodes - color by broker type
        node_colors = {
            'Central Broker': COLORS['primary'],
            'Information Source': COLORS['success'],
            'Information Sink': COLORS['warning'],
            'Hub': COLORS['info'],
            'Regular': COLORS['light'],
            'Isolated': COLORS['danger']
        }
        
        for broker_type, color in node_colors.items():
            nodes = [n for n, d in G.nodes(data=True) if d['broker_type'] == broker_type]
            nx.draw_networkx_nodes(G, pos, nodelist=nodes, node_color=color,
                                 node_size=1000, alpha=0.8, ax=ax, label=broker_type)
                                 
        # Draw edges - thickness by weight, color by trust
        edges = G.edges(data=True)
        for (u, v, d) in edges:
            width = np.log1p(d['weight']) * 2  # Log scale for better visibility
            trust = d['trust']
            
            # Color gradient from red (low trust) to green (high trust)
            if trust < 0.5:
                color = COLORS['danger']
            elif trust < 0.8:
                color = COLORS['warning']
            else:
                color = COLORS['success']
                
            nx.draw_networkx_edges(G, pos, [(u, v)], width=width, alpha=0.6,
                                 edge_color=color, arrows=True, 
                                 arrowsize=15, ax=ax)
                                 
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)
        
        # Add legend
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        # Add edge legend
        trust_legend = [
            mpatches.Patch(color=COLORS['success'], label='High Dependency (>80%)'),
            mpatches.Patch(color=COLORS['warning'], label='Medium Dependency (50-80%)'),
            mpatches.Patch(color=COLORS['danger'], label='Low Dependency (<50%)')
        ]
        ax.legend(handles=trust_legend, loc='upper left', bbox_to_anchor=(1, 0.5))
        
        self.format_axis(ax, title="Information Flow Network", grid=False)
        ax.axis('off')
        
        self.save_figure(fig, "information_flow_network")
        
    def _create_task_completion_timeline(self):
        """
        Create Gantt-style timeline showing task completions.
        Color-coded by bonus vs regular completion.
        """
        # Get task completion data
        task_data = self.results['task_performance']['completion_patterns']
        timeline_dict = task_data.get('completion_timeline', {})
        
        if not timeline_dict:
            return
            
        # Create figure
        fig, ax = self.create_figure(figsize=(12, 8),
                                    title="Task Completion Timeline")
        
        # Convert timeline data - handle both dict of dicts and DataFrame formats
        if hasattr(timeline_dict, 'to_dict'):
            # It's a DataFrame, convert to dict
            timeline_df = timeline_dict
            rounds = list(timeline_df.index)
            completions = timeline_df['successful'].tolist() if 'successful' in timeline_df else []
            bonuses = timeline_df['with_bonus'].tolist() if 'with_bonus' in timeline_df else []
        else:
            # It's already a dict
            rounds = sorted(timeline_dict.keys())
            if rounds and isinstance(timeline_dict[rounds[0]], dict):
                completions = [timeline_dict[r].get('successful', 0) for r in rounds]
                bonuses = [timeline_dict[r].get('with_bonus', 0) for r in rounds]
            else:
                # Might be a different structure
                return
                
        if not completions:
            return
            
        regular = [c - b for c, b in zip(completions, bonuses)]
        
        # Create stacked bar chart
        x = np.arange(len(rounds))
        width = 0.6
        
        # Plot bars
        bars1 = ax.bar(x, bonuses, width, label='With Bonus', 
                       color=COLORS['success'], alpha=0.8)
        bars2 = ax.bar(x, regular, width, bottom=bonuses, 
                       label='Regular', color=COLORS['primary'], alpha=0.8)
        
        # Add value labels
        for i, (b, r) in enumerate(zip(bonuses, regular)):
            if b > 0:
                ax.text(i, b/2, str(b), ha='center', va='center', 
                       fontsize=9, fontweight='bold')
            if r > 0:
                ax.text(i, b + r/2, str(r), ha='center', va='center',
                       fontsize=9, fontweight='bold')
                
        # Add cumulative line
        cumulative = np.cumsum(completions)
        ax2 = ax.twinx()
        line = ax2.plot(x, cumulative, color=COLORS['secondary'], 
                       linewidth=3, marker='o', markersize=8, 
                       label='Cumulative')
        ax2.set_ylabel('Cumulative Completions', fontsize=12)
        
        # Format
        ax.set_xticks(x)
        ax.set_xticklabels([f'Round {r}' for r in rounds])
        
        self.format_axis(ax, xlabel="Simulation Round", 
                        ylabel="Tasks Completed",
                        title="Task Completion Timeline")
        
        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        self.save_figure(fig, "task_completion_timeline")
        
    def _create_agent_performance_dashboard(self):
        """
        Create 2x2 dashboard showing key performance metrics per agent.
        """
        # Get agent data
        agent_summary = self.results['agent_summary']
        strategies = self.results['strategy']['agent_strategies']['classifications']
        
        # Create figure with subplots
        fig, axes = self.create_subplots(2, 2, figsize=(14, 10),
                                        title="Agent Performance Dashboard")
        axes = axes.flatten()
        
        # Prepare data
        agents = agent_summary['agent_id'].tolist()
        agents_display = self.truncate_labels(agents, 10)
        
        # 1. Task Success Rate
        ax = axes[0]
        success_rate = []
        for agent in agents:
            data = agent_summary[agent_summary['agent_id'] == agent].iloc[0]
            rate = data['tasks_completed'] / max(data['rounds_active'], 1)
            success_rate.append(rate)
            
        bars = ax.bar(agents_display, success_rate, color=COLORS['success'], alpha=0.8)
        self.add_value_labels(ax, bars, '{:.2f}')
        self.format_axis(ax, xlabel="Agent", ylabel="Tasks/Round",
                        title="Task Completion Rate")
        ax.tick_params(axis='x', rotation=45)
        
        # 2. Information Sharing Rate
        ax = axes[1]
        sharing_rate = []
        for agent in agents:
            data = agent_summary[agent_summary['agent_id'] == agent].iloc[0]
            rate = data['info_pieces_shared'] / max(data['rounds_active'], 1)
            sharing_rate.append(rate)
            
        bars = ax.bar(agents_display, sharing_rate, color=COLORS['info'], alpha=0.8)
        self.add_value_labels(ax, bars, '{:.2f}')
        self.format_axis(ax, xlabel="Agent", ylabel="Info Shared/Round",
                        title="Information Sharing Rate")
        ax.tick_params(axis='x', rotation=45)
        
        # 3. Trust Score (Truthfulness)
        ax = axes[2]
        trust_scores = []
        for agent in agents:
            data = agent_summary[agent_summary['agent_id'] == agent].iloc[0]
            if data['info_pieces_shared'] > 0:
                score = data['truthful_shares'] / data['info_pieces_shared']
            else:
                score = 1.0
            trust_scores.append(score)
            
        bars = ax.bar(agents_display, trust_scores, color=COLORS['primary'], alpha=0.8)
        self.add_value_labels(ax, bars, '{:.1%}')
        self.format_axis(ax, xlabel="Agent", ylabel="Truthfulness Rate",
                        title="Trust Score")
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylim(0, 1.1)
        
        # 4. Strategy Distribution
        ax = axes[3]
        strategy_counts = pd.Series(list(strategies.values())).value_counts()
        colors = PALETTES['categorical'][:len(strategy_counts)]
        
        wedges, texts, autotexts = ax.pie(strategy_counts.values, 
                                          labels=strategy_counts.index,
                                          colors=colors,
                                          autopct='%1.0f%%',
                                          startangle=90)
        
        # Improve text readability
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            
        ax.set_title("Strategy Distribution", fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        self.save_figure(fig, "agent_performance_dashboard")
        
    def _create_communication_efficiency_heatmap(self):
        """
        Create heatmap showing communication efficiency by agent.
        """
        # Get communication data
        comm_matrix = self.results['communication']['communication_matrix']
        info_matrix = self.results['information_flow']['information_matrix']
        
        # Calculate efficiency matrix
        efficiency_matrix = pd.DataFrame(
            np.zeros_like(comm_matrix.values),
            index=comm_matrix.index,
            columns=comm_matrix.columns
        )
        
        for i in range(len(comm_matrix)):
            for j in range(len(comm_matrix)):
                if i != j and comm_matrix.iloc[i, j] > 0:
                    # Efficiency = info shared / messages sent
                    efficiency = info_matrix.iloc[i, j] / comm_matrix.iloc[i, j]
                    efficiency_matrix.iloc[i, j] = efficiency
                    
        # Create figure
        fig, ax = self.create_figure(figsize=(10, 8),
                                    title="Communication Efficiency Heatmap")
        
        # Create heatmap
        mask = efficiency_matrix == 0  # Mask zero values
        
        sns.heatmap(efficiency_matrix, 
                   mask=mask,
                   cmap='RdYlGn',
                   center=0.5,
                   vmin=0, vmax=1,
                   square=True,
                   linewidths=0.5,
                   cbar_kws={"shrink": 0.8, "label": "Efficiency\n(Info/Message)"},
                   annot=True,
                   fmt='.2f',
                   annot_kws={'size': 9},
                   ax=ax)
                   
        # Format
        ax.set_xlabel("To Agent", fontsize=12)
        ax.set_ylabel("From Agent", fontsize=12)
        ax.set_title("Communication Efficiency: Information Pieces per Message",
                    fontsize=14, fontweight='bold', pad=20)
        
        # Rotate labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        plt.setp(ax.get_yticklabels(), rotation=0)
        
        self.save_figure(fig, "communication_efficiency_heatmap")
        
    def _create_round_dynamics(self):
        """
        Create multi-line plot showing round-by-round dynamics.
        """
        # Get round summary data
        round_summary = self.results['round_summary']
        
        if round_summary.empty:
            return
            
        # Create figure
        fig, ax = self.create_figure(figsize=(12, 8),
                                    title="Round-by-Round Simulation Dynamics")
        
        # Prepare data
        rounds = round_summary['round'].tolist()
        
        # Plot different metrics
        ax2 = ax.twinx()
        
        # Primary axis - Activity metrics
        l1 = ax.plot(rounds, round_summary['message_count'], 
                    color=COLORS['primary'], linewidth=2.5,
                    marker='o', markersize=8, label='Messages')
        
        l2 = ax.plot(rounds, round_summary['information_exchanges'],
                    color=COLORS['success'], linewidth=2.5,
                    marker='s', markersize=8, label='Info Exchanges')
        
        l3 = ax.plot(rounds, round_summary['tasks_completed'],
                    color=COLORS['warning'], linewidth=2.5,
                    marker='^', markersize=8, label='Tasks Completed')
        
        # Secondary axis - Cumulative score approximation
        cumulative_score = round_summary['tasks_completed'].cumsum() * 10
        l4 = ax2.plot(rounds, cumulative_score,
                     color=COLORS['secondary'], linewidth=3,
                     linestyle='--', marker='D', markersize=6,
                     label='Cumulative Score')
        
        # Format axes
        self.format_axis(ax, xlabel="Round", ylabel="Count",
                        title="Simulation Activity Over Time")
        ax2.set_ylabel("Cumulative Score", fontsize=12)
        
        # Combine legends
        lines = l1 + l2 + l3 + l4
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Highlight high activity rounds
        high_activity_threshold = round_summary['total_actions'].mean() + round_summary['total_actions'].std()
        for i, row in round_summary.iterrows():
            if row['total_actions'] > high_activity_threshold:
                ax.axvspan(row['round'] - 0.5, row['round'] + 0.5,
                          alpha=0.1, color=COLORS['accent1'])
                
        self.save_figure(fig, "round_dynamics")
        
    def _calculate_trust_rates(self) -> Dict[tuple, float]:
        """Calculate trust rates between agent pairs"""
        exchanges = self.results.get('information_exchanges', pd.DataFrame())
        
        if exchanges.empty:
            return {}
            
        trust_rates = {}
        
        # Group by agent pairs
        for (from_agent, to_agent), group in exchanges.groupby(['from_agent', 'to_agent']):
            trust_rate = group['was_truthful'].mean()
            trust_rates[(from_agent, to_agent)] = trust_rate
            
        return trust_rates
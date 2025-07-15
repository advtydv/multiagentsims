"""
Comprehensive visualization module for information asymmetry simulation analysis.

This module creates publication-ready visualizations for all aspects of the simulation.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
from datetime import datetime
import warnings

# Try to import optional packages
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    warnings.warn("NetworkX not installed. Network visualizations will be skipped.")

try:
    from wordcloud import WordCloud
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False
    warnings.warn("WordCloud not installed. Word cloud visualizations will be skipped.")

# Set up matplotlib style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Define consistent color scheme
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#E63946',
    'success': '#06D6A0',
    'warning': '#F77F00',
    'info': '#7209B7',
    'dark': '#212529',
    'light': '#F8F9FA',
    'agent_colors': plt.cm.tab10.colors
}


class SimulationVisualizer:
    """Creates comprehensive visualizations for simulation analysis."""
    
    def __init__(self, log_data: List[Dict[str, Any]], results: Dict[str, Any], output_dir: Path):
        """
        Initialize the visualizer.
        
        Args:
            log_data: List of all log events
            results: Analysis results dictionary
            output_dir: Directory to save visualizations
        """
        self.log_data = log_data
        self.results = results
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Extract different event types
        self._extract_events()
        
    def _extract_events(self):
        """Extract different types of events from log data."""
        self.messages = []
        self.actions = []
        self.private_thoughts = []
        self.negotiations = []
        self.deceptions = []
        
        for event in self.log_data:
            event_type = event.get('event_type')
            data = event.get('data', {})
            
            if event_type == 'message':
                self.messages.append(data)
            elif event_type == 'agent_action':
                self.actions.append(data)
            elif event_type == 'private_thoughts':
                self.private_thoughts.append(data)
            elif event_type == 'negotiation':
                self.negotiations.append(data)
            elif event_type == 'deception_attempt':
                self.deceptions.append(data)
                
    def create_all_visualizations(self):
        """Create all visualizations."""
        print("Creating visualizations...")
        
        # 1. Agent Performance Dashboard
        self._create_agent_performance_dashboard()
        print("✓ Agent performance dashboard created")
        
        # 2. Communication Network Graph
        if HAS_NETWORKX:
            self._create_communication_network()
            print("✓ Communication network created")
        
        # 3. Information Flow Heatmap
        self._create_information_flow_heatmap()
        print("✓ Information flow heatmap created")
        
        # 4. Negotiation Analysis Visualizations
        self._create_negotiation_visualizations()
        print("✓ Negotiation visualizations created")
        
        # 5. Temporal Analysis
        self._create_temporal_analysis()
        print("✓ Temporal analysis created")
        
        # 6. Strategic Behavior Analysis
        self._create_strategic_behavior_analysis()
        print("✓ Strategic behavior analysis created")
        
        print(f"\nAll visualizations saved to: {self.output_dir}")
        
    def _create_agent_performance_dashboard(self):
        """Create multi-panel dashboard showing agent performance metrics."""
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
        
        # Get agent data
        fm = self.results.get('foundational_metrics', {})
        agent_metrics = fm.get('agent_metrics', {})
        
        if not agent_metrics:
            print("Warning: No agent metrics found")
            return
            
        agents = list(agent_metrics.keys())
        
        # 1. Agent Rankings Bar Chart
        ax1 = fig.add_subplot(gs[0, :])
        rankings = fm.get('rankings', {})
        if rankings:
            sorted_agents = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
            agent_names = [a[0] for a in sorted_agents]
            scores = [a[1] for a in sorted_agents]
            
            bars = ax1.bar(range(len(agent_names)), scores, color=COLORS['primary'])
            ax1.set_xticks(range(len(agent_names)))
            ax1.set_xticklabels(agent_names, rotation=45, ha='right')
            ax1.set_title('Agent Rankings by Final Score', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Score')
            
            # Add value labels on bars
            for i, (bar, score) in enumerate(zip(bars, scores)):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{score}', ha='center', va='bottom')
        
        # 2. Cooperation Scores
        ax2 = fig.add_subplot(gs[1, 0])
        coop_scores = []
        for agent in agents:
            metrics = agent_metrics[agent]
            # Calculate cooperation score based on fulfillment rate
            coop_score = metrics.get('fulfillment_rate', 0) * 100
            coop_scores.append((agent, coop_score))
        
        coop_scores.sort(key=lambda x: x[1])
        y_pos = np.arange(len(coop_scores))
        ax2.barh(y_pos, [s[1] for s in coop_scores], color=COLORS['success'])
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels([s[0] for s in coop_scores])
        ax2.set_xlabel('Cooperation Score (%)')
        ax2.set_title('Agent Cooperation Levels', fontsize=12, fontweight='bold')
        ax2.set_xlim(0, 100)
        
        # 3. Deception Scores
        ax3 = fig.add_subplot(gs[1, 1])
        deception_scores = []
        da = self.results.get('deception_analysis', {})
        agent_deception = da.get('agent_analysis', {})
        
        for agent in agents:
            deception_rate = agent_deception.get(agent, {}).get('deception_rate', 0) * 100
            deception_scores.append((agent, deception_rate))
        
        deception_scores.sort(key=lambda x: x[1])
        y_pos = np.arange(len(deception_scores))
        ax3.barh(y_pos, [s[1] for s in deception_scores], color=COLORS['secondary'])
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels([s[0] for s in deception_scores])
        ax3.set_xlabel('Deception Rate (%)')
        ax3.set_title('Agent Deception Levels', fontsize=12, fontweight='bold')
        ax3.set_xlim(0, max([s[1] for s in deception_scores] + [10]))
        
        # 4. Combined Scatter Plot
        ax4 = fig.add_subplot(gs[2, :])
        coop_dict = dict(coop_scores)
        decep_dict = dict(deception_scores)
        
        x_vals = [coop_dict.get(agent, 0) for agent in agents]
        y_vals = [decep_dict.get(agent, 0) for agent in agents]
        sizes = [rankings.get(agent, 0) * 10 for agent in agents]
        
        scatter = ax4.scatter(x_vals, y_vals, s=sizes, alpha=0.6, 
                            c=range(len(agents)), cmap='viridis')
        
        # Add agent labels
        for i, agent in enumerate(agents):
            ax4.annotate(agent, (x_vals[i], y_vals[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax4.set_xlabel('Cooperation Score (%)')
        ax4.set_ylabel('Deception Rate (%)')
        ax4.set_title('Agent Strategy Space (size = final score)', fontsize=14, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # Add quadrant labels
        ax4.text(75, max(y_vals)*0.9, 'Cooperative\nDeceptive', ha='center', 
                fontsize=10, style='italic', alpha=0.5)
        ax4.text(25, max(y_vals)*0.9, 'Uncooperative\nDeceptive', ha='center', 
                fontsize=10, style='italic', alpha=0.5)
        ax4.text(75, max(y_vals)*0.1, 'Cooperative\nHonest', ha='center', 
                fontsize=10, style='italic', alpha=0.5)
        ax4.text(25, max(y_vals)*0.1, 'Uncooperative\nHonest', ha='center', 
                fontsize=10, style='italic', alpha=0.5)
        
        plt.suptitle('Agent Performance Dashboard', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'agent_performance_dashboard.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def _create_communication_network(self):
        """Create network visualization of agent communications."""
        if not HAS_NETWORKX:
            return
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Build communication graph
        G = nx.DiGraph()
        
        # Count messages between agents
        message_counts = defaultdict(lambda: defaultdict(int))
        info_transfer_counts = defaultdict(lambda: defaultdict(int))
        total_messages_per_agent = defaultdict(int)
        
        for msg in self.messages:
            from_agent = msg.get('from')
            msg_type = msg.get('type')
            
            if from_agent:
                total_messages_per_agent[from_agent] += 1
                
                if msg_type == 'direct':
                    to_agent = msg.get('to')
                    if to_agent:
                        message_counts[from_agent][to_agent] += 1
                        
                        # Check if this is an information transfer
                        content = msg.get('content', '').lower()
                        if any(word in content for word in ['here is', 'the answer', 'i have']):
                            info_transfer_counts[from_agent][to_agent] += 1
        
        # Add nodes
        agents = list(set(total_messages_per_agent.keys()))
        for agent in agents:
            G.add_node(agent)
        
        # Add edges for general messages
        for from_agent, to_dict in message_counts.items():
            for to_agent, count in to_dict.items():
                if count > 0:
                    G.add_edge(from_agent, to_agent, weight=count, type='message')
        
        # Plot 1: General Communication Network
        pos = nx.circular_layout(G)
        
        # Node sizes based on total messages
        node_sizes = [total_messages_per_agent.get(node, 1) * 100 for node in G.nodes()]
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                             node_color=COLORS['primary'], alpha=0.7, ax=ax1)
        
        # Draw edges with width based on message frequency
        edges = G.edges()
        weights = [G[u][v]['weight'] for u, v in edges]
        if weights:
            max_weight = max(weights)
            edge_widths = [w/max_weight * 5 for w in weights]
            nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.5, 
                                 edge_color=COLORS['dark'], arrows=True, ax=ax1)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax1)
        
        ax1.set_title('Communication Network\n(Node size = total messages, Edge width = frequency)', 
                     fontsize=12, fontweight='bold')
        ax1.axis('off')
        
        # Plot 2: Information Transfer Network
        G2 = nx.DiGraph()
        for agent in agents:
            G2.add_node(agent)
            
        for from_agent, to_dict in info_transfer_counts.items():
            for to_agent, count in to_dict.items():
                if count > 0:
                    G2.add_edge(from_agent, to_agent, weight=count)
        
        # Draw information transfer network
        nx.draw_networkx_nodes(G2, pos, node_size=node_sizes, 
                             node_color=COLORS['success'], alpha=0.7, ax=ax2)
        
        edges2 = G2.edges()
        if edges2:
            weights2 = [G2[u][v]['weight'] for u, v in edges2]
            max_weight2 = max(weights2) if weights2 else 1
            edge_widths2 = [w/max_weight2 * 5 for w in weights2]
            nx.draw_networkx_edges(G2, pos, width=edge_widths2, alpha=0.5, 
                                 edge_color=COLORS['info'], arrows=True, ax=ax2)
        
        nx.draw_networkx_labels(G2, pos, font_size=10, font_weight='bold', ax=ax2)
        
        ax2.set_title('Information Transfer Network\n(Shows actual information sharing)', 
                     fontsize=12, fontweight='bold')
        ax2.axis('off')
        
        plt.suptitle('Agent Communication Networks', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'communication_networks.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def _create_information_flow_heatmap(self):
        """Create heatmap showing information flow between agents."""
        # Get unique agents
        agents = set()
        for msg in self.messages:
            if msg.get('from'):
                agents.add(msg['from'])
            if msg.get('to') and msg['type'] == 'direct':
                agents.add(msg['to'])
        
        agents = sorted(list(agents))
        n_agents = len(agents)
        
        # Create matrix for information shares
        info_matrix = np.zeros((n_agents, n_agents))
        
        for msg in self.messages:
            from_agent = msg.get('from')
            if not from_agent or from_agent not in agents:
                continue
                
            from_idx = agents.index(from_agent)
            content = msg.get('content', '').lower()
            
            # Check if this is information sharing
            if any(word in content for word in ['here is', 'the answer', 'i have', 'information']):
                if msg['type'] == 'direct':
                    to_agent = msg.get('to')
                    if to_agent and to_agent in agents:
                        to_idx = agents.index(to_agent)
                        info_matrix[from_idx][to_idx] += 1
                else:  # broadcast
                    for i, agent in enumerate(agents):
                        if agent != from_agent:
                            info_matrix[from_idx][i] += 0.5  # Weight broadcasts less
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create heatmap
        mask = np.eye(n_agents, dtype=bool)  # Mask diagonal
        sns.heatmap(info_matrix, mask=mask, annot=True, fmt='.0f', 
                   xticklabels=agents, yticklabels=agents,
                   cmap='YlOrRd', cbar_kws={'label': 'Information Shares'},
                   ax=ax, square=True, linewidths=0.5)
        
        ax.set_xlabel('To Agent', fontweight='bold')
        ax.set_ylabel('From Agent', fontweight='bold')
        ax.set_title('Information Flow Matrix\n(Number of information shares between agents)', 
                    fontsize=14, fontweight='bold')
        
        # Rotate labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        plt.setp(ax.get_yticklabels(), rotation=0)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'information_flow_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def _create_negotiation_visualizations(self):
        """Create visualizations for negotiation analysis."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        na = self.results.get('negotiation_analysis', {})
        
        # 1. Success Rate by Agent
        agent_outcomes = na.get('agent_negotiation_stats', {})
        if agent_outcomes:
            agents = []
            success_rates = []
            
            for agent, stats in agent_outcomes.items():
                total = stats.get('total_negotiations', 0)
                if total > 0:
                    success_rate = stats.get('successful', 0) / total * 100
                    agents.append(agent)
                    success_rates.append(success_rate)
            
            if agents:
                y_pos = np.arange(len(agents))
                bars = ax1.barh(y_pos, success_rates, color=COLORS['success'])
                ax1.set_yticks(y_pos)
                ax1.set_yticklabels(agents)
                ax1.set_xlabel('Success Rate (%)')
                ax1.set_title('Negotiation Success Rate by Agent', fontweight='bold')
                ax1.set_xlim(0, 100)
                
                # Add value labels
                for i, (bar, rate) in enumerate(zip(bars, success_rates)):
                    ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                            f'{rate:.1f}%', va='center')
        
        # 2. Negotiation Network Graph
        if HAS_NETWORKX:
            G = nx.Graph()
            negotiation_pairs = na.get('negotiation_network', {})
            
            for pair, count in negotiation_pairs.items():
                if isinstance(pair, tuple) and len(pair) == 2:
                    G.add_edge(pair[0], pair[1], weight=count)
            
            if G.nodes():
                pos = nx.spring_layout(G)
                nx.draw_networkx_nodes(G, pos, node_color=COLORS['info'], 
                                     node_size=500, alpha=0.7, ax=ax2)
                
                edges = G.edges()
                weights = [G[u][v]['weight'] for u, v in edges]
                if weights:
                    max_weight = max(weights)
                    edge_widths = [w/max_weight * 5 for w in weights]
                    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.5, ax=ax2)
                
                nx.draw_networkx_labels(G, pos, font_size=8, ax=ax2)
                ax2.set_title('Negotiation Network\n(Edge width = number of negotiations)', 
                            fontweight='bold')
                ax2.axis('off')
        
        # 3. Complexity Distribution
        complexity_dist = na.get('complexity_analysis', {}).get('complexity_distribution', {})
        if complexity_dist:
            labels = list(complexity_dist.keys())
            sizes = list(complexity_dist.values())
            colors = [COLORS['agent_colors'][i % len(COLORS['agent_colors'])] 
                     for i in range(len(labels))]
            
            ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax3.set_title('Negotiation Complexity Distribution', fontweight='bold')
        
        # 4. Negotiation Outcomes Over Time
        temporal = na.get('temporal_patterns', {})
        if temporal and isinstance(temporal, dict):
            rounds = []
            success_rates = []
            
            for round_num, round_data in temporal.items():
                if isinstance(round_data, dict):
                    total = round_data.get('total', 0)
                    if total > 0:
                        success_rate = round_data.get('successful', 0) / total * 100
                        rounds.append(int(round_num))
                        success_rates.append(success_rate)
            
            if rounds:
                sorted_pairs = sorted(zip(rounds, success_rates))
                rounds, success_rates = zip(*sorted_pairs)
                ax4.plot(rounds, success_rates, marker='o', color=COLORS['primary'], linewidth=2)
                ax4.fill_between(rounds, success_rates, alpha=0.3, color=COLORS['primary'])
            
            ax4.set_xlabel('Round')
            ax4.set_ylabel('Success Rate (%)')
            ax4.set_title('Negotiation Success Rate Over Time', fontweight='bold')
            ax4.grid(True, alpha=0.3)
            ax4.set_ylim(0, 100)
        
        plt.suptitle('Negotiation Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'negotiation_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def _create_temporal_analysis(self):
        """Create temporal analysis visualizations."""
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        
        # 1. Task Completion Timeline
        fm = self.results.get('foundational_metrics', {})
        temporal_metrics = fm.get('temporal_metrics', {})
        
        if temporal_metrics:
            rounds = sorted(temporal_metrics.keys())
            completions = [temporal_metrics[r].get('tasks_completed', 0) for r in rounds]
            
            ax1.bar(rounds, completions, color=COLORS['success'], alpha=0.7)
            ax1.set_xlabel('Round')
            ax1.set_ylabel('Tasks Completed')
            ax1.set_title('Task Completion Timeline', fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. Message Volume Over Rounds
        if temporal_metrics:
            message_volumes = [temporal_metrics[r].get('messages_sent', 0) for r in rounds]
            
            ax2.plot(rounds, message_volumes, marker='o', color=COLORS['primary'], 
                    linewidth=2, markersize=8)
            ax2.fill_between(rounds, message_volumes, alpha=0.3, color=COLORS['primary'])
            ax2.set_xlabel('Round')
            ax2.set_ylabel('Number of Messages')
            ax2.set_title('Communication Volume Over Time', fontweight='bold')
            ax2.grid(True, alpha=0.3)
        
        # 3. Deception Events Over Time
        da = self.results.get('deception_analysis', {})
        deception_timeline = da.get('temporal_analysis', {}).get('deceptions_by_round', {})
        
        if deception_timeline:
            rounds = sorted(deception_timeline.keys())
            deceptions = [deception_timeline[r] for r in rounds]
            
            ax3.scatter(rounds, deceptions, color=COLORS['secondary'], s=100, alpha=0.7)
            ax3.plot(rounds, deceptions, color=COLORS['secondary'], alpha=0.5, linestyle='--')
            ax3.set_xlabel('Round')
            ax3.set_ylabel('Deception Events')
            ax3.set_title('Deception Events Over Time', fontweight='bold')
            ax3.grid(True, alpha=0.3)
        
        plt.suptitle('Temporal Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'temporal_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def _create_strategic_behavior_analysis(self):
        """Create strategic behavior analysis visualizations."""
        fig = plt.figure(figsize=(14, 10))
        gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
        
        # 1. Word Cloud from Private Thoughts
        ax1 = fig.add_subplot(gs[0, :])
        if HAS_WORDCLOUD and self.private_thoughts:
            # Combine all private thoughts
            all_thoughts = ' '.join([thought['thoughts'] for thought in self.private_thoughts])
            
            # Create word cloud
            wordcloud = WordCloud(width=800, height=400, 
                                background_color='white',
                                colormap='viridis').generate(all_thoughts)
            
            ax1.imshow(wordcloud, interpolation='bilinear')
            ax1.set_title('Private Thoughts Word Cloud', fontsize=14, fontweight='bold')
            ax1.axis('off')
        else:
            ax1.text(0.5, 0.5, 'Word Cloud Not Available\n(Install wordcloud package)', 
                    ha='center', va='center', fontsize=12)
            ax1.axis('off')
        
        # 2. Response Latency Histogram
        ax2 = fig.add_subplot(gs[1, 0])
        
        # Simulate response latency data (in real scenario, this would come from logs)
        # For now, we'll analyze message frequency patterns
        fm = self.results.get('foundational_metrics', {})
        agent_metrics = fm.get('agent_metrics', {})
        
        message_counts = []
        for agent, metrics in agent_metrics.items():
            count = metrics.get('messages_sent', 0)
            message_counts.append(count)
        
        if message_counts:
            ax2.hist(message_counts, bins=10, color=COLORS['info'], alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Messages Sent')
            ax2.set_ylabel('Number of Agents')
            ax2.set_title('Message Activity Distribution', fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. Broadcast vs Direct Message Usage
        ax3 = fig.add_subplot(gs[1, 1])
        
        broadcast_metrics = fm.get('broadcast_metrics', {})
        total_broadcasts = broadcast_metrics.get('total_broadcasts', 0)
        total_direct = len([m for m in self.messages if m.get('type') == 'direct'])
        
        if total_broadcasts + total_direct > 0:
            labels = ['Broadcasts', 'Direct Messages']
            sizes = [total_broadcasts, total_direct]
            colors = [COLORS['warning'], COLORS['primary']]
            
            wedges, texts, autotexts = ax3.pie(sizes, labels=labels, colors=colors, 
                                              autopct='%1.1f%%', startangle=90)
            ax3.set_title('Communication Type Distribution', fontweight='bold')
            
            # Add total count in center
            total = sum(sizes)
            ax3.text(0, 0, f'Total:\n{total}', ha='center', va='center', 
                    fontsize=12, fontweight='bold')
        
        plt.suptitle('Strategic Behavior Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'strategic_behavior_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()


def create_visualizations(log_data: List[Dict[str, Any]], 
                        analysis_results: Dict[str, Any], 
                        output_dir: Path):
    """
    Main entry point for creating visualizations.
    
    Args:
        log_data: List of all log events
        analysis_results: Dictionary containing all analysis results
        output_dir: Directory to save visualizations
    """
    visualizer = SimulationVisualizer(log_data, analysis_results, output_dir)
    visualizer.create_all_visualizations()
"""
Enhanced Visualizer for Information Asymmetry Simulation
Creates focused, meaningful visualizations from simulation logs
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import defaultdict
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Professional color scheme
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#27AE60',
    'warning': '#F39C12',
    'danger': '#E74C3C',
    'info': '#3498DB',
    'dark': '#2C3E50',
    'light': '#ECF0F1'
}

plt.style.use('seaborn-v0_8-darkgrid')


class EnhancedVisualizer:
    """Creates focused visualizations from simulation logs"""
    
    def __init__(self, log_data, output_dir):
        self.log_data = log_data
        self.output_dir = output_dir
        self.agents = self._extract_agents()
        self.rounds = self._extract_rounds()
        
    def _extract_agents(self):
        """Extract unique agent IDs from the log"""
        agents = set()
        for event in self.log_data:
            if event['event_type'] == 'agent_action':
                agents.add(event['data']['agent_id'])
        return sorted(list(agents))
    
    def _extract_rounds(self):
        """Extract round numbers from the log"""
        rounds = set()
        for event in self.log_data:
            if event['event_type'] == 'agent_action':
                rounds.add(event['data']['round'])
        return sorted(list(rounds))
    
    def create_all_visualizations(self):
        """Create all enhanced visualizations"""
        print("Creating enhanced visualizations...")
        
        # 1. Message flow heatmap
        self._create_message_flow_heatmap()
        print("✓ Message flow heatmap created")
        
        # 2. Information transfer heatmap
        self._create_information_transfer_heatmap()
        print("✓ Information transfer heatmap created")
        
        # 3. Task completion timeline
        self._create_task_completion_timeline()
        print("✓ Task completion timeline created")
        
        # 4. Activity correlation analysis
        self._create_activity_correlation()
        print("✓ Activity correlation analysis created")
        
        # 5. Round-by-round dynamics
        self._create_round_dynamics()
        print("✓ Round dynamics visualization created")
        
        # 6. Agent efficiency dashboard
        self._create_efficiency_dashboard()
        print("✓ Agent efficiency dashboard created")
        
        # 7. Communication patterns over time
        self._create_communication_timeline()
        print("✓ Communication timeline created")
        
        # 8. Information distribution evolution
        self._create_information_distribution()
        print("✓ Information distribution visualization created")
    
    def _create_message_flow_heatmap(self):
        """Create heatmap showing message counts between agents"""
        # Initialize matrix
        n_agents = len(self.agents)
        message_matrix = np.zeros((n_agents, n_agents))
        
        # Count messages
        for event in self.log_data:
            if event['event_type'] == 'message' and event['data']['type'] == 'direct':
                from_agent = event['data']['from']
                to_agent = event['data']['to']
                
                if from_agent in self.agents and to_agent in self.agents:
                    from_idx = self.agents.index(from_agent)
                    to_idx = self.agents.index(to_agent)
                    message_matrix[from_idx, to_idx] += 1
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Create heatmap with annotations
        sns.heatmap(message_matrix, 
                    xticklabels=self.agents,
                    yticklabels=self.agents,
                    annot=True, 
                    fmt='.0f',
                    cmap='Blues',
                    square=True,
                    cbar_kws={'label': 'Number of Messages'},
                    ax=ax)
        
        ax.set_xlabel('To Agent', fontsize=12, fontweight='bold')
        ax.set_ylabel('From Agent', fontsize=12, fontweight='bold')
        ax.set_title('Message Flow Between Agents', fontsize=16, fontweight='bold', pad=20)
        
        # Add total messages sent/received
        sent_totals = message_matrix.sum(axis=1)
        received_totals = message_matrix.sum(axis=0)
        
        # Add totals as text
        for i, agent in enumerate(self.agents):
            ax.text(n_agents + 0.5, i + 0.5, f'Sent: {int(sent_totals[i])}', 
                   ha='left', va='center', fontsize=9)
            ax.text(i + 0.5, -0.5, f'Recv: {int(received_totals[i])}', 
                   ha='center', va='bottom', fontsize=9, rotation=0)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/message_flow_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_information_transfer_heatmap(self):
        """Create heatmap showing information pieces transferred between agents"""
        # Initialize matrix
        n_agents = len(self.agents)
        info_matrix = np.zeros((n_agents, n_agents))
        
        # Count information transfers
        for event in self.log_data:
            if event['event_type'] == 'information_exchange':
                from_agent = event['data']['from_agent']
                to_agent = event['data']['to_agent']
                info_count = len(event['data']['information'])
                
                if from_agent in self.agents and to_agent in self.agents:
                    from_idx = self.agents.index(from_agent)
                    to_idx = self.agents.index(to_agent)
                    info_matrix[from_idx, to_idx] += info_count
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Create heatmap
        sns.heatmap(info_matrix, 
                    xticklabels=self.agents,
                    yticklabels=self.agents,
                    annot=True, 
                    fmt='.0f',
                    cmap='Greens',
                    square=True,
                    cbar_kws={'label': 'Information Pieces Transferred'},
                    ax=ax)
        
        ax.set_xlabel('To Agent', fontsize=12, fontweight='bold')
        ax.set_ylabel('From Agent', fontsize=12, fontweight='bold')
        ax.set_title('Information Transfer Between Agents', fontsize=16, fontweight='bold', pad=20)
        
        # Add totals
        sent_totals = info_matrix.sum(axis=1)
        received_totals = info_matrix.sum(axis=0)
        
        for i, agent in enumerate(self.agents):
            ax.text(n_agents + 0.5, i + 0.5, f'Shared: {int(sent_totals[i])}', 
                   ha='left', va='center', fontsize=9)
            ax.text(i + 0.5, -0.5, f'Rcvd: {int(received_totals[i])}', 
                   ha='center', va='bottom', fontsize=9, rotation=0)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/information_transfer_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_task_completion_timeline(self):
        """Create timeline showing when agents complete tasks"""
        # Extract task completions
        task_completions = []
        for event in self.log_data:
            if event['event_type'] == 'task_completion':
                task_completions.append({
                    'agent': event['data']['agent_id'],
                    'round': event['data'].get('round', 0),
                    'success': event['data']['success'],
                    'task_id': event['data']['task_id']
                })
        
        if not task_completions:
            # Create placeholder if no task completions
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, 'No task completions recorded', 
                   ha='center', va='center', fontsize=16)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            plt.savefig(f"{self.output_dir}/task_completion_timeline.png", dpi=300, bbox_inches='tight')
            plt.close()
            return
        
        # Create timeline visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[3, 1])
        
        # Plot 1: Timeline of completions
        agent_positions = {agent: i for i, agent in enumerate(self.agents)}
        colors = ['green' if tc['success'] else 'red' for tc in task_completions]
        
        for tc in task_completions:
            if tc['agent'] in agent_positions:
                y_pos = agent_positions[tc['agent']]
                color = 'green' if tc['success'] else 'red'
                ax1.scatter(tc['round'], y_pos, c=color, s=200, alpha=0.7, edgecolors='black')
        
        ax1.set_yticks(range(len(self.agents)))
        ax1.set_yticklabels(self.agents)
        ax1.set_xlabel('Round', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Agent', fontsize=12, fontweight='bold')
        ax1.set_title('Task Completion Timeline', fontsize=16, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add legend
        ax1.scatter([], [], c='green', s=200, label='Successful')
        ax1.scatter([], [], c='red', s=200, label='Failed')
        ax1.legend(loc='upper right')
        
        # Plot 2: Completions per round
        completions_per_round = defaultdict(int)
        for tc in task_completions:
            if tc['success']:
                completions_per_round[tc['round']] += 1
        
        rounds = sorted(completions_per_round.keys())
        counts = [completions_per_round[r] for r in rounds]
        
        ax2.bar(rounds, counts, color=COLORS['primary'], alpha=0.7)
        ax2.set_xlabel('Round', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Completions', fontsize=12, fontweight='bold')
        ax2.set_title('Task Completions per Round', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/task_completion_timeline.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_activity_correlation(self):
        """Create correlation analysis between activities and outcomes"""
        # Collect agent statistics
        agent_stats = defaultdict(lambda: {
            'messages_sent': 0,
            'messages_received': 0,
            'info_sent': 0,
            'info_received': 0,
            'tasks_completed': 0,
            'tasks_attempted': 0
        })
        
        # Count activities
        for event in self.log_data:
            if event['event_type'] == 'message' and event['data']['type'] == 'direct':
                from_agent = event['data']['from']
                to_agent = event['data']['to']
                if from_agent != 'system':
                    agent_stats[from_agent]['messages_sent'] += 1
                if to_agent != 'system':
                    agent_stats[to_agent]['messages_received'] += 1
                    
            elif event['event_type'] == 'information_exchange':
                from_agent = event['data']['from_agent']
                to_agent = event['data']['to_agent']
                info_count = len(event['data']['information'])
                agent_stats[from_agent]['info_sent'] += info_count
                agent_stats[to_agent]['info_received'] += info_count
                
            elif event['event_type'] == 'task_completion':
                agent = event['data']['agent_id']
                agent_stats[agent]['tasks_attempted'] += 1
                if event['data']['success']:
                    agent_stats[agent]['tasks_completed'] += 1
        
        # Create visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Prepare data
        agents = sorted(agent_stats.keys())
        if 'system' in agents:
            agents.remove('system')
        
        messages_sent = [agent_stats[a]['messages_sent'] for a in agents]
        tasks_completed = [agent_stats[a]['tasks_completed'] for a in agents]
        info_sent = [agent_stats[a]['info_sent'] for a in agents]
        info_received = [agent_stats[a]['info_received'] for a in agents]
        
        # Plot 1: Messages sent vs Tasks completed
        ax1.scatter(messages_sent, tasks_completed, s=200, alpha=0.7, color=COLORS['primary'])
        for i, agent in enumerate(agents):
            ax1.annotate(agent, (messages_sent[i], tasks_completed[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=9)
        ax1.set_xlabel('Messages Sent', fontweight='bold')
        ax1.set_ylabel('Tasks Completed', fontweight='bold')
        ax1.set_title('Communication Activity vs Task Completion', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Information shared vs Tasks completed
        ax2.scatter(info_sent, tasks_completed, s=200, alpha=0.7, color=COLORS['success'])
        for i, agent in enumerate(agents):
            ax2.annotate(agent, (info_sent[i], tasks_completed[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=9)
        ax2.set_xlabel('Information Pieces Shared', fontweight='bold')
        ax2.set_ylabel('Tasks Completed', fontweight='bold')
        ax2.set_title('Information Sharing vs Task Completion', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Efficiency ratio (tasks per message)
        efficiency = []
        for a in agents:
            if agent_stats[a]['messages_sent'] > 0:
                eff = agent_stats[a]['tasks_completed'] / agent_stats[a]['messages_sent']
                efficiency.append(eff)
            else:
                efficiency.append(0)
        
        y_pos = np.arange(len(agents))
        ax3.barh(y_pos, efficiency, color=COLORS['warning'], alpha=0.7)
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(agents)
        ax3.set_xlabel('Tasks Completed per Message Sent', fontweight='bold')
        ax3.set_title('Agent Communication Efficiency', fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')
        
        # Plot 4: Activity balance
        categories = ['Msgs Sent', 'Msgs Rcvd', 'Info Sent', 'Info Rcvd']
        x = np.arange(len(categories))
        width = 0.8 / len(agents)
        
        for i, agent in enumerate(agents[:5]):  # Show top 5 agents
            values = [
                agent_stats[agent]['messages_sent'],
                agent_stats[agent]['messages_received'],
                agent_stats[agent]['info_sent'],
                agent_stats[agent]['info_received']
            ]
            ax4.bar(x + i * width, values, width, label=agent, alpha=0.8)
        
        ax4.set_xlabel('Activity Type', fontweight='bold')
        ax4.set_ylabel('Count', fontweight='bold')
        ax4.set_title('Activity Distribution (Top 5 Agents)', fontweight='bold')
        ax4.set_xticks(x + width * 2)
        ax4.set_xticklabels(categories)
        ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('Agent Activity Correlation Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/activity_correlation.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_round_dynamics(self):
        """Create visualization showing how dynamics change over rounds"""
        # Collect round-by-round statistics
        round_stats = defaultdict(lambda: {
            'messages': 0,
            'info_transfers': 0,
            'task_completions': 0,
            'unique_senders': set(),
            'unique_receivers': set()
        })
        
        for event in self.log_data:
            if 'round' in event['data'] or (event['event_type'] == 'agent_action' and 'round' in event['data']):
                round_num = event['data'].get('round', 0)
                
                if event['event_type'] == 'message' and event['data']['type'] == 'direct':
                    round_stats[round_num]['messages'] += 1
                    round_stats[round_num]['unique_senders'].add(event['data']['from'])
                    round_stats[round_num]['unique_receivers'].add(event['data']['to'])
                    
                elif event['event_type'] == 'information_exchange':
                    round_stats[round_num]['info_transfers'] += len(event['data']['information'])
                    
                elif event['event_type'] == 'task_completion' and event['data']['success']:
                    round_stats[round_num]['task_completions'] += 1
        
        # Prepare data
        rounds = sorted(round_stats.keys())
        messages = [round_stats[r]['messages'] for r in rounds]
        info_transfers = [round_stats[r]['info_transfers'] for r in rounds]
        task_completions = [round_stats[r]['task_completions'] for r in rounds]
        active_agents = [len(round_stats[r]['unique_senders'] | round_stats[r]['unique_receivers']) for r in rounds]
        
        # Create visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Messages over rounds
        ax1.plot(rounds, messages, marker='o', linewidth=2, markersize=8, color=COLORS['primary'])
        ax1.fill_between(rounds, messages, alpha=0.3, color=COLORS['primary'])
        ax1.set_xlabel('Round', fontweight='bold')
        ax1.set_ylabel('Number of Messages', fontweight='bold')
        ax1.set_title('Message Volume Over Time', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Information transfers over rounds
        ax2.plot(rounds, info_transfers, marker='s', linewidth=2, markersize=8, color=COLORS['success'])
        ax2.fill_between(rounds, info_transfers, alpha=0.3, color=COLORS['success'])
        ax2.set_xlabel('Round', fontweight='bold')
        ax2.set_ylabel('Information Pieces Transferred', fontweight='bold')
        ax2.set_title('Information Sharing Over Time', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Task completions over rounds
        ax3.bar(rounds, task_completions, color=COLORS['warning'], alpha=0.7, width=0.6)
        ax3.set_xlabel('Round', fontweight='bold')
        ax3.set_ylabel('Tasks Completed', fontweight='bold')
        ax3.set_title('Task Completion Rate', fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Plot 4: Active agents over rounds
        ax4.plot(rounds, active_agents, marker='D', linewidth=2, markersize=8, color=COLORS['danger'])
        ax4.fill_between(rounds, active_agents, alpha=0.3, color=COLORS['danger'])
        ax4.set_xlabel('Round', fontweight='bold')
        ax4.set_ylabel('Number of Active Agents', fontweight='bold')
        ax4.set_title('Agent Participation Over Time', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, max(active_agents) + 2 if active_agents else 12)
        
        plt.suptitle('Simulation Dynamics Over Rounds', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/round_dynamics.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_efficiency_dashboard(self):
        """Create dashboard showing agent efficiency metrics"""
        # Calculate efficiency metrics
        agent_metrics = defaultdict(lambda: {
            'messages_sent': 0,
            'info_received': 0,
            'info_sent': 0,
            'tasks_completed': 0,
            'tasks_attempted': 0,
            'unique_partners': set(),
            'response_time': []
        })
        
        # Collect metrics
        for event in self.log_data:
            if event['event_type'] == 'message' and event['data']['type'] == 'direct':
                from_agent = event['data']['from']
                to_agent = event['data']['to']
                if from_agent != 'system':
                    agent_metrics[from_agent]['messages_sent'] += 1
                    agent_metrics[from_agent]['unique_partners'].add(to_agent)
                    
            elif event['event_type'] == 'information_exchange':
                from_agent = event['data']['from_agent']
                to_agent = event['data']['to_agent']
                info_count = len(event['data']['information'])
                agent_metrics[from_agent]['info_sent'] += info_count
                agent_metrics[to_agent]['info_received'] += info_count
                
            elif event['event_type'] == 'task_completion':
                agent = event['data']['agent_id']
                agent_metrics[agent]['tasks_attempted'] += 1
                if event['data']['success']:
                    agent_metrics[agent]['tasks_completed'] += 1
        
        # Prepare data
        agents = sorted([a for a in agent_metrics.keys() if a != 'system'])
        
        # Calculate efficiency scores
        efficiency_scores = []
        for agent in agents:
            m = agent_metrics[agent]
            # Efficiency = (tasks completed * 10 + info sent * 2) / (messages sent + 1)
            score = (m['tasks_completed'] * 10 + m['info_sent'] * 2) / (m['messages_sent'] + 1)
            efficiency_scores.append(score)
        
        # Create visualization
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Main efficiency ranking
        ax1 = fig.add_subplot(gs[0:2, 0:2])
        y_pos = np.arange(len(agents))
        colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(agents)))
        
        bars = ax1.barh(y_pos, efficiency_scores, color=colors)
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(agents)
        ax1.set_xlabel('Efficiency Score', fontsize=12, fontweight='bold')
        ax1.set_title('Agent Efficiency Ranking', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (bar, score) in enumerate(zip(bars, efficiency_scores)):
            ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    f'{score:.2f}', va='center', fontsize=9)
        
        # Task completion rate
        ax2 = fig.add_subplot(gs[0, 2])
        completion_rates = []
        for agent in agents[:5]:  # Top 5 agents
            m = agent_metrics[agent]
            rate = m['tasks_completed'] / (m['tasks_attempted'] + 0.001) * 100
            completion_rates.append(rate)
        
        ax2.bar(agents[:5], completion_rates, color=COLORS['success'], alpha=0.7)
        ax2.set_ylabel('Completion Rate (%)', fontweight='bold')
        ax2.set_title('Task Success Rate', fontweight='bold')
        ax2.set_xticklabels(agents[:5], rotation=45)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Network diversity
        ax3 = fig.add_subplot(gs[1, 2])
        network_sizes = [len(agent_metrics[a]['unique_partners']) for a in agents[:5]]
        ax3.bar(agents[:5], network_sizes, color=COLORS['info'], alpha=0.7)
        ax3.set_ylabel('Unique Partners', fontweight='bold')
        ax3.set_title('Network Diversity', fontweight='bold')
        ax3.set_xticklabels(agents[:5], rotation=45)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Information flow balance
        ax4 = fig.add_subplot(gs[2, :])
        info_balance = []
        for agent in agents:
            m = agent_metrics[agent]
            balance = m['info_received'] - m['info_sent']
            info_balance.append(balance)
        
        colors = ['red' if b < 0 else 'green' for b in info_balance]
        ax4.bar(agents, info_balance, color=colors, alpha=0.7)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.set_xlabel('Agent', fontweight='bold')
        ax4.set_ylabel('Information Balance (Received - Sent)', fontweight='bold')
        ax4.set_title('Information Flow Balance', fontweight='bold')
        ax4.set_xticklabels(agents, rotation=45)
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('Agent Efficiency Dashboard', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/efficiency_dashboard.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_communication_timeline(self):
        """Create timeline showing communication patterns"""
        # Extract communication events with timestamps
        comm_events = []
        for event in self.log_data:
            if event['event_type'] == 'message' and event['data']['type'] == 'direct':
                if event['data']['from'] != 'system':
                    comm_events.append({
                        'timestamp': event['timestamp'],
                        'from': event['data']['from'],
                        'to': event['data']['to'],
                        'round': event.get('data', {}).get('round', 0)
                    })
        
        # Sort by timestamp
        comm_events.sort(key=lambda x: x['timestamp'])
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), height_ratios=[3, 1])
        
        # Plot 1: Communication timeline
        agent_y = {agent: i for i, agent in enumerate(self.agents)}
        
        for i, event in enumerate(comm_events):
            if event['from'] in agent_y and event['to'] in agent_y:
                y1 = agent_y[event['from']]
                y2 = agent_y[event['to']]
                ax1.plot([i, i], [y1, y2], 'b-', alpha=0.3, linewidth=1)
                ax1.scatter(i, y1, c='red', s=20, alpha=0.7, zorder=3)
                ax1.scatter(i, y2, c='green', s=20, alpha=0.7, zorder=3)
        
        ax1.set_yticks(range(len(self.agents)))
        ax1.set_yticklabels(self.agents)
        ax1.set_xlabel('Communication Event', fontweight='bold')
        ax1.set_ylabel('Agent', fontweight='bold')
        ax1.set_title('Communication Timeline', fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='x')
        
        # Add legend
        ax1.scatter([], [], c='red', s=50, label='Sender')
        ax1.scatter([], [], c='green', s=50, label='Receiver')
        ax1.plot([], [], 'b-', alpha=0.5, linewidth=2, label='Message')
        ax1.legend(loc='upper right')
        
        # Plot 2: Communication density over time
        window_size = max(1, len(comm_events) // 20)
        densities = []
        positions = []
        
        for i in range(0, len(comm_events) - window_size, window_size // 2):
            window_events = comm_events[i:i+window_size]
            density = len(window_events)
            densities.append(density)
            positions.append(i + window_size // 2)
        
        ax2.fill_between(positions, densities, alpha=0.5, color=COLORS['primary'])
        ax2.plot(positions, densities, color=COLORS['primary'], linewidth=2)
        ax2.set_xlabel('Communication Event', fontweight='bold')
        ax2.set_ylabel('Message Density', fontweight='bold')
        ax2.set_title('Communication Intensity Over Time', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/communication_timeline.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_information_distribution(self):
        """Create visualization showing how information spreads"""
        # Track information distribution over rounds
        info_distribution = defaultdict(lambda: defaultdict(set))
        
        # Initial distribution from simulation start
        for event in self.log_data:
            if event['event_type'] == 'simulation_start':
                # Extract initial information distribution if available
                pass
        
        # Track transfers
        for event in self.log_data:
            if event['event_type'] == 'information_exchange':
                round_num = event.get('data', {}).get('round', 0)
                to_agent = event['data']['to_agent']
                for info in event['data']['information']:
                    info_distribution[round_num][to_agent].add(info)
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Plot 1: Information spread over rounds
        rounds = sorted(set(r for r in info_distribution.keys()))
        if rounds:
            info_counts = []
            for round_num in rounds:
                total_pieces = sum(len(pieces) for pieces in info_distribution[round_num].values())
                info_counts.append(total_pieces)
            
            ax1.plot(rounds, info_counts, marker='o', linewidth=3, markersize=10, color=COLORS['success'])
            ax1.fill_between(rounds, info_counts, alpha=0.3, color=COLORS['success'])
            ax1.set_xlabel('Round', fontweight='bold')
            ax1.set_ylabel('Total Information Pieces Distributed', fontweight='bold')
            ax1.set_title('Information Spread Over Time', fontweight='bold')
            ax1.grid(True, alpha=0.3)
        
        # Plot 2: Information concentration
        final_distribution = defaultdict(int)
        for event in self.log_data:
            if event['event_type'] == 'information_exchange':
                to_agent = event['data']['to_agent']
                final_distribution[to_agent] += len(event['data']['information'])
        
        if final_distribution:
            agents = sorted(final_distribution.keys())
            counts = [final_distribution[a] for a in agents]
            
            # Create pie chart
            colors = plt.cm.Set3(np.linspace(0, 1, len(agents)))
            wedges, texts, autotexts = ax2.pie(counts, labels=agents, colors=colors, 
                                               autopct='%1.1f%%', startangle=90)
            ax2.set_title('Final Information Distribution', fontweight='bold')
            
            # Make percentage text more readable
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontsize(10)
                autotext.set_fontweight('bold')
        
        plt.suptitle('Information Distribution Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/information_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()


def create_enhanced_visualizations(log_data, output_dir):
    """Main function to create all enhanced visualizations"""
    visualizer = EnhancedVisualizer(log_data, output_dir)
    visualizer.create_all_visualizations()
    print(f"\nAll enhanced visualizations saved to: {output_dir}")
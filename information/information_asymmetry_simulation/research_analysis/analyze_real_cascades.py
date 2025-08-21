#!/usr/bin/env python3
"""
Analyze real cascade patterns from simulations with uncooperative agents
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.1)

def analyze_cascade_patterns(sim_path):
    """Extract real cascade data from simulation logs"""
    
    log_file = Path(sim_path) / 'simulation_log.jsonl'
    
    # Track cascade metrics per round
    cascade_data = defaultdict(lambda: {
        'manipulations': 0,
        'agents_with_bad_info': set(),
        'penalties': 0,
        'affected_agents': set(),
        'info_transfers': 0,
        'bad_info_transfers': 0,
        'task_attempts_with_bad_info': 0,
        'agents_sending_bad_info': set(),
        'recovery_actions': 0
    })
    
    # Track which agents are uncooperative
    uncooperative_agents = set()
    
    # Track bad information pieces and their spread
    bad_info_tracking = defaultdict(lambda: {
        'origin': None,
        'spread_to': set(),
        'rounds_active': set()
    })
    
    # Track agent states
    agent_bad_info = defaultdict(set)  # Which bad info each agent has
    agent_penalties = defaultdict(list)  # When agents got penalized
    
    print(f"Analyzing {sim_path}...")
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                
                # Identify uncooperative agents
                if event['event_type'] == 'simulation_start':
                    config = event['data'].get('config', {})
                    agent_types = config.get('agent_types', {})
                    for agent_id, agent_type in agent_types.items():
                        if agent_type == 'uncooperative':
                            uncooperative_agents.add(agent_id)
                    print(f"  Found {len(uncooperative_agents)} uncooperative agents: {uncooperative_agents}")
                
                # Track round-based events
                if 'round' in event.get('data', {}):
                    round_num = event['data']['round']
                    
                    # Track information exchanges
                    if event['event_type'] == 'information_exchange':
                        sender = event['data'].get('from')
                        receiver = event['data'].get('to')
                        cascade_data[round_num]['info_transfers'] += 1
                        
                        # Check if manipulation occurred
                        if event['data'].get('value_manipulated'):
                            cascade_data[round_num]['manipulations'] += 1
                            cascade_data[round_num]['agents_sending_bad_info'].add(sender)
                            
                            # Track bad info spread
                            info_pieces = event['data'].get('information', [])
                            for piece in info_pieces:
                                bad_info_tracking[piece]['origin'] = sender
                                bad_info_tracking[piece]['spread_to'].add(receiver)
                                bad_info_tracking[piece]['rounds_active'].add(round_num)
                                agent_bad_info[receiver].add(piece)
                            
                            cascade_data[round_num]['agents_with_bad_info'].add(receiver)
                            cascade_data[round_num]['bad_info_transfers'] += 1
                    
                    # Track penalties (detection of bad info)
                    elif event['event_type'] == 'penalty_applied':
                        agent_id = event['data'].get('agent_id')
                        cascade_data[round_num]['penalties'] += 1
                        cascade_data[round_num]['affected_agents'].add(agent_id)
                        agent_penalties[agent_id].append(round_num)
                        
                        # After penalty, agent might avoid using that bad info
                        cascade_data[round_num]['recovery_actions'] += 1
                    
                    # Track task attempts with bad info
                    elif event['event_type'] == 'task_attempt':
                        agent_id = event['data'].get('agent_id')
                        if agent_bad_info[agent_id]:
                            cascade_data[round_num]['task_attempts_with_bad_info'] += 1
                
            except Exception as e:
                continue
    
    # Convert to dataframe for analysis
    rounds_list = []
    for round_num in sorted(cascade_data.keys()):
        data = cascade_data[round_num]
        rounds_list.append({
            'round': round_num,
            'manipulations': data['manipulations'],
            'agents_affected': len(data['agents_with_bad_info']),
            'penalties': data['penalties'],
            'bad_transfers': data['bad_info_transfers'],
            'total_transfers': data['info_transfers'],
            'contamination_rate': data['bad_info_transfers'] / max(1, data['info_transfers']),
            'unique_spreaders': len(data['agents_sending_bad_info']),
            'recovery_actions': data['recovery_actions']
        })
    
    df = pd.DataFrame(rounds_list)
    
    # Calculate cumulative effects
    df['cumulative_affected'] = df['agents_affected'].cumsum()
    df['cumulative_penalties'] = df['penalties'].cumsum()
    
    # Calculate cascade "waves"
    df['cascade_intensity'] = df['agents_affected'].rolling(window=3, min_periods=1).mean()
    
    return df, uncooperative_agents, bad_info_tracking

def create_improved_cascade_visualization():
    """Create realistic cascade visualization from actual data"""
    
    # Analyze multiple simulations with uncooperative agents
    simulations_to_analyze = [
        ('logs/simulation_20250818_212648', '2 Uncoop, Open, 20 rounds'),
        ('logs/simulation_20250814_214134', '2 Uncoop, Closed, 20 rounds'),
        ('logs/simulation_20250818_132631', '1 Uncoop, Open, 20 rounds'),
    ]
    
    all_data = []
    
    for sim_path, description in simulations_to_analyze:
        if Path(sim_path).exists():
            print(f"\nAnalyzing: {description}")
            df, uncoop_agents, bad_info = analyze_cascade_patterns(sim_path)
            if not df.empty:
                df['simulation'] = description
                all_data.append(df)
    
    if not all_data:
        print("No cascade data found, using synthetic example")
        return create_synthetic_cascade()
    
    # Combine data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Finding 4: Real Information Manipulation Cascades', fontsize=14, fontweight='bold')
    
    # Plot 1: Cascade propagation over time (real data)
    ax = axes[0, 0]
    
    for sim_desc in combined_df['simulation'].unique():
        sim_data = combined_df[combined_df['simulation'] == sim_desc]
        if '2 Uncoop' in sim_desc:
            color = 'red' if 'Closed' in sim_desc else 'blue'
            label = sim_desc.split(',')[1].strip()  # Get system type
            
            # Plot cascade intensity
            ax.plot(sim_data['round'], sim_data['cascade_intensity'], 
                   label=f'{label} (2 uncoop)', linewidth=2, alpha=0.8, color=color)
            ax.fill_between(sim_data['round'], 0, sim_data['cascade_intensity'], 
                           alpha=0.2, color=color)
    
    ax.set_xlabel('Round')
    ax.set_ylabel('Cascade Intensity (Avg Affected Agents)')
    ax.set_title('Real Cascade Propagation Patterns')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Contamination spread and recovery
    ax = axes[0, 1]
    
    # Focus on one simulation with good data
    best_sim = combined_df[combined_df['simulation'].str.contains('2 Uncoop')].groupby('simulation').first().index[0]
    sim_data = combined_df[combined_df['simulation'] == best_sim]
    
    if not sim_data.empty:
        # Show contamination rate
        ax.plot(sim_data['round'], sim_data['contamination_rate'] * 100, 
               'r-', linewidth=2, label='Contamination Rate')
        
        # Show penalties as recovery markers
        penalty_rounds = sim_data[sim_data['penalties'] > 0]
        ax.scatter(penalty_rounds['round'], penalty_rounds['contamination_rate'] * 100, 
                  color='green', s=100, marker='v', label='Penalties Applied', zorder=5)
        
        ax.set_xlabel('Round')
        ax.set_ylabel('Bad Information Rate (%)')
        ax.set_title('Contamination and Recovery Dynamics')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    # Plot 3: Cumulative impact
    ax = axes[1, 0]
    
    for sim_desc in combined_df['simulation'].unique():
        if '2 Uncoop' in sim_desc:
            sim_data = combined_df[combined_df['simulation'] == sim_desc]
            color = 'red' if 'Closed' in sim_desc else 'blue'
            label = sim_desc.split(',')[1].strip()
            
            ax.plot(sim_data['round'], sim_data['cumulative_affected'], 
                   label=f'{label}', linewidth=2, color=color, marker='o', markersize=3)
    
    ax.set_xlabel('Round')
    ax.set_ylabel('Cumulative Agents Affected')
    ax.set_title('Cascade Reach Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 4: Network resilience (penalties vs new contaminations)
    ax = axes[1, 1]
    
    # Calculate resilience metric
    for sim_desc in combined_df['simulation'].unique()[:2]:  # Top 2 simulations
        sim_data = combined_df[combined_df['simulation'] == sim_desc]
        
        # Resilience = ability to contain spread after detection
        sim_data['resilience'] = 1 - (sim_data['bad_transfers'] / max(1, sim_data['total_transfers']))
        sim_data['resilience_smooth'] = sim_data['resilience'].rolling(window=3, min_periods=1).mean()
        
        color = 'blue' if 'Open' in sim_desc else 'red'
        system = 'Open' if 'Open' in sim_desc else 'Closed'
        
        ax.plot(sim_data['round'], sim_data['resilience_smooth'] * 100, 
               label=f'{system} System', linewidth=2, color=color)
    
    ax.set_xlabel('Round')
    ax.set_ylabel('System Resilience (%)')
    ax.set_title('Recovery and Adaptation')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 105])
    
    plt.tight_layout()
    plt.savefig('research_analysis/finding4_cascade_effects_improved.png', bbox_inches='tight', dpi=150)
    print("\nGenerated: finding4_cascade_effects_improved.png")
    plt.show()
    
    return combined_df

def create_synthetic_cascade():
    """Create synthetic but realistic cascade pattern if no real data available"""
    
    rounds = np.arange(1, 21)
    
    # More realistic cascade pattern
    cascade = np.zeros(20)
    
    # Initial manipulation at round 3
    manip_start = 3
    
    # Gradual spread with network effects
    for i in range(manip_start - 1, 20):
        if i == manip_start - 1:
            cascade[i] = 1  # Initial manipulator
        elif i < manip_start + 4:
            # Exponential growth phase
            cascade[i] = cascade[i-1] * 1.8 + np.random.normal(0, 0.2)
        elif i < manip_start + 7:
            # Plateau as network saturates
            cascade[i] = cascade[i-1] + np.random.normal(0, 0.5)
        else:
            # Gradual recovery with occasional resurgence
            recovery_rate = 0.85 + 0.1 * np.sin(i * 0.5)
            cascade[i] = max(0, cascade[i-1] * recovery_rate + np.random.normal(0, 0.3))
            
            # Occasional resurgence
            if np.random.random() < 0.2:
                cascade[i] += np.random.uniform(0.5, 1.5)
    
    cascade = np.clip(cascade, 0, 10)
    
    # Create simple plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.plot(rounds, cascade, 'r-', linewidth=2.5, label='Cascade Intensity')
    ax.fill_between(rounds, 0, cascade, alpha=0.3, color='red')
    
    # Mark key events
    ax.axvline(x=manip_start, color='red', linestyle='--', alpha=0.7, label='Initial Manipulation')
    ax.axvline(x=manip_start + 5, color='orange', linestyle='--', alpha=0.7, label='Detection Begin')
    ax.axvline(x=manip_start + 7, color='green', linestyle='--', alpha=0.7, label='Recovery Phase')
    
    ax.set_xlabel('Round')
    ax.set_ylabel('Number of Affected Agents')
    ax.set_title('Information Manipulation Cascade (Synthetic Example)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('research_analysis/finding4_cascade_synthetic.png', bbox_inches='tight', dpi=150)
    plt.show()
    
    return pd.DataFrame({'round': rounds, 'cascade': cascade})

def main():
    print("="*80)
    print("ANALYZING REAL CASCADE PATTERNS")
    print("="*80)
    
    # Create improved visualization
    cascade_data = create_improved_cascade_visualization()
    
    # Summary statistics
    if isinstance(cascade_data, pd.DataFrame) and not cascade_data.empty:
        print("\n=== CASCADE STATISTICS ===")
        
        # Average cascade metrics
        avg_contamination = cascade_data['contamination_rate'].mean() * 100
        max_affected = cascade_data['agents_affected'].max()
        recovery_time = len(cascade_data[cascade_data['penalties'] > 0])
        
        print(f"Average contamination rate: {avg_contamination:.1f}%")
        print(f"Maximum agents affected in one round: {max_affected}")
        print(f"Rounds with penalties (recovery): {recovery_time}")
        
        # Compare open vs closed if available
        if 'simulation' in cascade_data.columns:
            open_data = cascade_data[cascade_data['simulation'].str.contains('Open')]
            closed_data = cascade_data[cascade_data['simulation'].str.contains('Closed')]
            
            if not open_data.empty and not closed_data.empty:
                print(f"\nOpen system cascade intensity: {open_data['cascade_intensity'].mean():.2f}")
                print(f"Closed system cascade intensity: {closed_data['cascade_intensity'].mean():.2f}")
    
    print("\n✅ Improved cascade analysis complete!")
    
    return cascade_data

if __name__ == "__main__":
    results = main()
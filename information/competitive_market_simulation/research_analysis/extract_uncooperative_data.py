#!/usr/bin/env python3
"""
Extract actual uncooperative agent performance data from simulations
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Publication settings
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.1)

def extract_final_rankings(sim_path):
    """Extract final rankings and identify uncooperative agent"""
    log_file = Path(sim_path) / 'simulation_log.jsonl'
    
    final_rankings = {}
    agent_types = {}
    uncooperative_agent = None
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                
                if event['event_type'] == 'simulation_start':
                    config = event['data']['config']
                    agent_types = config.get('agent_types', {})
                    # Find uncooperative agent
                    for agent_id, agent_type in agent_types.items():
                        if agent_type == 'uncooperative':
                            uncooperative_agent = agent_id
                            print(f"Found uncooperative agent: {agent_id}")
                            
                elif event['event_type'] == 'simulation_end':
                    final_rankings = event['data'].get('final_rankings', {})
                    
            except Exception as e:
                continue
    
    return final_rankings, uncooperative_agent, agent_types

def analyze_uncooperative_paradox():
    """Analyze the actual data for uncooperative agent paradox"""
    
    # The two key simulations
    open_sim = 'logs/simulation_20250818_132638'  # Open system with uncooperative
    closed_sim = 'logs/simulation_20250818_132631'  # Closed system with uncooperative
    
    print("="*60)
    print("EXTRACTING REAL DATA FOR UNCOOPERATIVE AGENT PARADOX")
    print("="*60)
    
    # Extract data from open system
    print(f"\nAnalyzing OPEN system: {open_sim}")
    open_rankings, open_uncoop, open_types = extract_final_rankings(open_sim)
    
    if open_rankings and open_uncoop:
        # Sort agents by revenue
        open_sorted = sorted(open_rankings.items(), key=lambda x: x[1], reverse=True)
        print("\nOpen System Final Rankings:")
        for rank, (agent, revenue) in enumerate(open_sorted, 1):
            agent_type = "UNCOOPERATIVE" if agent == open_uncoop else "cooperative"
            print(f"  Rank {rank}: {agent} - ${revenue:,.0f} ({agent_type})")
    
    # Extract data from closed system
    print(f"\nAnalyzing CLOSED system: {closed_sim}")
    closed_rankings, closed_uncoop, closed_types = extract_final_rankings(closed_sim)
    
    if closed_rankings and closed_uncoop:
        # Sort agents by revenue
        closed_sorted = sorted(closed_rankings.items(), key=lambda x: x[1], reverse=True)
        print("\nClosed System Final Rankings:")
        for rank, (agent, revenue) in enumerate(closed_sorted, 1):
            agent_type = "UNCOOPERATIVE" if agent == closed_uncoop else "cooperative"
            print(f"  Rank {rank}: {agent} - ${revenue:,.0f} ({agent_type})")
    
    # Create the visualization with real data
    if open_rankings and closed_rankings and open_uncoop and closed_uncoop:
        create_real_paradox_plot(
            open_rankings, open_uncoop,
            closed_rankings, closed_uncoop
        )
    
    return {
        'open': {'rankings': open_rankings, 'uncoop': open_uncoop},
        'closed': {'rankings': closed_rankings, 'uncoop': closed_uncoop}
    }

def create_real_paradox_plot(open_rankings, open_uncoop, closed_rankings, closed_uncoop):
    """Create the paradox visualization with actual data"""
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 7))
    fig.suptitle('ACTUAL DATA: Uncooperative Agent Paradox', fontsize=14, fontweight='bold')
    
    # Prepare data
    agents = []
    open_revenues = []
    closed_revenues = []
    
    # Get all unique agents
    all_agents = set(list(open_rankings.keys()) + list(closed_rankings.keys()))
    
    # Separate uncooperative from cooperative agents
    uncoop_open_rev = open_rankings.get(open_uncoop, 0)
    uncoop_closed_rev = closed_rankings.get(closed_uncoop, 0)
    
    # Collect cooperative agents' revenues (excluding uncooperative)
    coop_agents_open = [(a, r) for a, r in open_rankings.items() if a != open_uncoop]
    coop_agents_closed = [(a, r) for a, r in closed_rankings.items() if a != closed_uncoop]
    
    # Sort cooperative agents by their average performance
    coop_agents_open_sorted = sorted(coop_agents_open, key=lambda x: x[1], reverse=True)
    coop_agents_closed_sorted = sorted(coop_agents_closed, key=lambda x: x[1], reverse=True)
    
    # Build the data for plotting
    # First add cooperative agents
    for i in range(min(9, len(coop_agents_open_sorted))):  # Show top 9 cooperative
        agents.append(f'Agent {i+1}')
        open_revenues.append(coop_agents_open_sorted[i][1] if i < len(coop_agents_open_sorted) else 0)
        closed_revenues.append(coop_agents_closed_sorted[i][1] if i < len(coop_agents_closed_sorted) else 0)
    
    # Add uncooperative agent at the end for emphasis
    agents.append('UNCOOP')
    open_revenues.append(uncoop_open_rev)
    closed_revenues.append(uncoop_closed_rev)
    
    # Create the plot
    x = np.arange(len(agents))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, open_revenues, width, label='Open System', color='blue', alpha=0.7)
    bars2 = ax.bar(x + width/2, closed_revenues, width, label='Closed System', color='red', alpha=0.7)
    
    # Highlight uncooperative agent with special formatting
    bars1[-1].set_color('darkblue')
    bars1[-1].set_edgecolor('gold')
    bars1[-1].set_linewidth(3)
    bars2[-1].set_color('darkred')
    bars2[-1].set_edgecolor('gold')
    bars2[-1].set_linewidth(3)
    
    # Find uncooperative agent's rank in each system
    open_sorted = sorted(open_rankings.items(), key=lambda x: x[1], reverse=True)
    closed_sorted = sorted(closed_rankings.items(), key=lambda x: x[1], reverse=True)
    
    open_uncoop_rank = next((i+1 for i, (a, _) in enumerate(open_sorted) if a == open_uncoop), None)
    closed_uncoop_rank = next((i+1 for i, (a, _) in enumerate(closed_sorted) if a == closed_uncoop), None)
    
    # Add rank annotations for uncooperative agent
    ax.text(x[-1] - width/2, uncoop_open_rev + 1000, 
           f'Rank: {open_uncoop_rank}/10', ha='center', fontweight='bold', fontsize=10)
    ax.text(x[-1] + width/2, uncoop_closed_rev + 500, 
           f'Rank: {closed_uncoop_rank}/10', ha='center', fontweight='bold', fontsize=10)
    
    ax.set_xlabel('Agents (Cooperative agents 1-9, then Uncooperative agent)')
    ax.set_ylabel('Final Revenue ($)')
    ax.set_title(f'Real Data: Uncooperative Ranks #{open_uncoop_rank} in Open but #{closed_uncoop_rank} in Closed!')
    ax.set_xticks(x)
    ax.set_xticklabels(agents, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add summary text box
    summary_text = (
        f"Open System: Uncooperative agent ranks {open_uncoop_rank}/10 with ${uncoop_open_rev:,.0f}\n"
        f"Closed System: Uncooperative agent ranks {closed_uncoop_rank}/10 with ${uncoop_closed_rev:,.0f}\n"
        f"Paradox: Uncooperative succeeds in transparent environment!"
    )
    
    ax.text(0.02, 0.98, summary_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('research_analysis/uncooperative_paradox_real_data.png', bbox_inches='tight', dpi=150)
    print(f"\nSaved visualization to: uncooperative_paradox_real_data.png")
    
    # Print summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(f"Open System - Uncooperative Performance:")
    print(f"  Revenue: ${uncoop_open_rev:,.0f}")
    print(f"  Rank: {open_uncoop_rank}/10")
    print(f"\nClosed System - Uncooperative Performance:")
    print(f"  Revenue: ${uncoop_closed_rev:,.0f}")
    print(f"  Rank: {closed_uncoop_rank}/10")
    print(f"\nDifference:")
    print(f"  Revenue: ${uncoop_open_rev - uncoop_closed_rev:,.0f} more in open system")
    print(f"  Rank: {closed_uncoop_rank - open_uncoop_rank} positions higher in open system")

def main():
    """Run the analysis"""
    results = analyze_uncooperative_paradox()
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    
    return results

if __name__ == "__main__":
    results = main()
#!/usr/bin/env python3
"""
Create accurate uncooperative paradox plot with real data from analysis_results.json
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Publication settings
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.1)

def create_accurate_paradox_visualization():
    """Create the paradox plot with actual data from Aug 18 simulations"""
    
    # Load the analysis results
    with open('logs/simulation_20250818_132638/analysis_results.json', 'r') as f:
        open_data = json.load(f)
    
    with open('logs/simulation_20250818_132631/analysis_results.json', 'r') as f:
        closed_data = json.load(f)
    
    # Extract rankings
    open_rankings = open_data['metrics']['agent_revenue_ranking']
    closed_rankings = closed_data['metrics']['agent_revenue_ranking']
    
    # Identify uncooperative agents (agent_1 in open, agent_2 in closed)
    open_uncoop_id = 'agent_1'
    closed_uncoop_id = 'agent_2'
    
    # Find uncooperative agent data
    open_uncoop_data = next(a for a in open_rankings if a['agent_id'] == open_uncoop_id)
    closed_uncoop_data = next(a for a in closed_rankings if a['agent_id'] == closed_uncoop_id)
    
    print("="*60)
    print("ACTUAL DATA FROM SIMULATIONS")
    print("="*60)
    print(f"\nOPEN SYSTEM (simulation_20250818_132638):")
    print(f"  Uncooperative agent ({open_uncoop_id}):")
    print(f"    Rank: {open_uncoop_data['rank']}/10")
    print(f"    Revenue: ${open_uncoop_data['revenue']:,}")
    print(f"    Tasks: {open_uncoop_data['tasks_completed']}")
    
    print(f"\nCLOSED SYSTEM (simulation_20250818_132631):")
    print(f"  Uncooperative agent ({closed_uncoop_id}):")
    print(f"    Rank: {closed_uncoop_data['rank']}/10")
    print(f"    Revenue: ${closed_uncoop_data['revenue']:,}")
    print(f"    Tasks: {closed_uncoop_data['tasks_completed']}")
    
    # Create the visualization
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    fig.suptitle('ACTUAL DATA: Uncooperative Agent Paradox (Aug 18, 2025 Simulations)', 
                 fontsize=14, fontweight='bold')
    
    # Prepare data for plotting
    # We'll show the uncooperative agent separately and group other agents
    agents = []
    open_revenues = []
    closed_revenues = []
    
    # Add top cooperative agents (excluding uncooperative)
    num_coop_to_show = 9
    
    # Get cooperative agents from each system
    open_coop = [a for a in open_rankings if a['agent_id'] != open_uncoop_id][:num_coop_to_show]
    closed_coop = [a for a in closed_rankings if a['agent_id'] != closed_uncoop_id][:num_coop_to_show]
    
    # Add cooperative agents
    for i in range(num_coop_to_show):
        agents.append(f'Coop {i+1}')
        if i < len(open_coop):
            open_revenues.append(open_coop[i]['revenue'])
        else:
            open_revenues.append(0)
        
        if i < len(closed_coop):
            closed_revenues.append(closed_coop[i]['revenue'])
        else:
            closed_revenues.append(0)
    
    # Add uncooperative agent at the end for emphasis
    agents.append('UNCOOP\nAGENT')
    open_revenues.append(open_uncoop_data['revenue'])
    closed_revenues.append(closed_uncoop_data['revenue'])
    
    # Create the plot
    x = np.arange(len(agents))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, open_revenues, width, label='Open System (Full Transparency)', 
                   color='blue', alpha=0.7)
    bars2 = ax.bar(x + width/2, closed_revenues, width, label='Closed System (Limited Visibility)', 
                   color='red', alpha=0.7)
    
    # Highlight uncooperative agent with special formatting
    bars1[-1].set_color('darkblue')
    bars1[-1].set_edgecolor('gold')
    bars1[-1].set_linewidth(4)
    bars2[-1].set_color('darkred')
    bars2[-1].set_edgecolor('gold')
    bars2[-1].set_linewidth(4)
    
    # Add value labels on bars for uncooperative agent
    ax.text(x[-1] - width/2, open_revenues[-1] + 2000, 
           f'${open_revenues[-1]:,}\nRank #{open_uncoop_data["rank"]}', 
           ha='center', fontweight='bold', fontsize=11, color='darkblue')
    ax.text(x[-1] + width/2, closed_revenues[-1] + 2000, 
           f'${closed_revenues[-1]:,}\nRank #{closed_uncoop_data["rank"]}', 
           ha='center', fontweight='bold', fontsize=11, color='darkred')
    
    # Add arrow showing the paradox
    ax.annotate('', xy=(x[-1] + width/2, closed_revenues[-1]), 
                xytext=(x[-1] - width/2, open_revenues[-1]),
                arrowprops=dict(arrowstyle='->', color='orange', lw=2, alpha=0.7))
    
    ax.text(x[-1], (open_revenues[-1] + closed_revenues[-1])/2, 
           'PARADOX!', ha='center', fontweight='bold', 
           fontsize=12, color='orange', rotation=45)
    
    ax.set_xlabel('Agents (Top 9 Cooperative Agents + Uncooperative Agent)', fontsize=12)
    ax.set_ylabel('Final Revenue ($)', fontsize=12)
    ax.set_title(f'Uncooperative Agent: Ranks #{open_uncoop_data["rank"]} in Open but #{closed_uncoop_data["rank"]} in Closed System!', 
                fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(agents)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add summary statistics box
    summary_text = (
        f"VERIFIED RESULTS:\n"
        f"Open System (Full Transparency):\n"
        f"  • Uncooperative agent ranks #{open_uncoop_data['rank']}/10\n"
        f"  • Revenue: ${open_uncoop_data['revenue']:,}\n"
        f"  • Completed {open_uncoop_data['tasks_completed']} tasks\n\n"
        f"Closed System (Limited Visibility):\n"
        f"  • Uncooperative agent ranks #{closed_uncoop_data['rank']}/10\n"
        f"  • Revenue: ${closed_uncoop_data['revenue']:,}\n"
        f"  • Completed {closed_uncoop_data['tasks_completed']} task(s)\n\n"
        f"Key Insight: Transparency enables identification\n"
        f"and exploitation by uncooperative agents!"
    )
    
    ax.text(0.02, 0.97, summary_text, transform=ax.transAxes,
           fontsize=9, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
    
    # Add system performance comparison
    open_total = sum(a['revenue'] for a in open_rankings)
    closed_total = sum(a['revenue'] for a in closed_rankings)
    
    system_text = (
        f"System-wide Performance:\n"
        f"Open: ${open_total:,} total\n"
        f"Closed: ${closed_total:,} total\n"
        f"Difference: ${abs(open_total - closed_total):,}"
    )
    
    ax.text(0.98, 0.97, system_text, transform=ax.transAxes,
           fontsize=9, verticalalignment='top', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9))
    
    plt.tight_layout()
    plt.savefig('research_analysis/surprising_discoveries_accurate.png', bbox_inches='tight', dpi=150)
    print(f"\nSaved accurate visualization to: surprising_discoveries_accurate.png")
    
    # Print detailed comparison
    print("\n" + "="*60)
    print("DETAILED COMPARISON")
    print("="*60)
    
    print("\nRevenue Difference for Uncooperative Agent:")
    print(f"  Open - Closed = ${open_uncoop_data['revenue'] - closed_uncoop_data['revenue']:,}")
    print(f"  Multiplier: {open_uncoop_data['revenue'] / closed_uncoop_data['revenue']:.2f}x better in open")
    
    print("\nRank Difference:")
    print(f"  Open rank - Closed rank = {open_uncoop_data['rank'] - closed_uncoop_data['rank']}")
    print(f"  (Negative means better rank in open system)")
    
    print("\nTasks Completed:")
    print(f"  Open: {open_uncoop_data['tasks_completed']} tasks")
    print(f"  Closed: {closed_uncoop_data['tasks_completed']} task(s)")
    print(f"  Difference: {open_uncoop_data['tasks_completed'] - closed_uncoop_data['tasks_completed']} more tasks in open")
    
    print("\nSystem-wide Impact:")
    print(f"  Open system total tasks: {open_data['metrics']['total_tasks_completed']}")
    print(f"  Closed system total tasks: {closed_data['metrics']['total_tasks_completed']}")
    print(f"  Difference: {open_data['metrics']['total_tasks_completed'] - closed_data['metrics']['total_tasks_completed']} more tasks in open")
    
    return {
        'open_uncoop': open_uncoop_data,
        'closed_uncoop': closed_uncoop_data,
        'open_total': open_total,
        'closed_total': closed_total
    }

if __name__ == "__main__":
    results = create_accurate_paradox_visualization()
    print("\n✅ Analysis complete with real data!")
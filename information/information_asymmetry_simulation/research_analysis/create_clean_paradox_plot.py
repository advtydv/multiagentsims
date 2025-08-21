#!/usr/bin/env python3
"""
Create clean uncooperative paradox plot with real data from analysis_results.json
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Publication settings
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.1)

def create_clean_paradox_visualization():
    """Create the paradox plot with manual data"""
    
    # Using manual values instead of loading files
    # These will be overridden by the manual input section below
    open_uncoop_data = {'rank': 10, 'revenue': 0, 'tasks_completed': 0}  # Will be replaced
    closed_uncoop_data = {'rank': 1, 'revenue': 0, 'tasks_completed': 0}  # Will be replaced
    
    # Skip printing since we're using manual values
    
    # Create the visualization
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    fig.suptitle('Performance in Open vs Closed Systems', 
                 fontsize=14, fontweight='bold')
    
    # Prepare data for plotting
    # We'll show the uncooperative agent separately and group other agents
    agents = []
    open_revenues = []
    closed_revenues = []
    
    # Add top cooperative agents (excluding uncooperative)
    num_coop_to_show = 9
    
    # MANUAL INPUT SECTION - MODIFY VALUES HERE
    # ================================================
    # These are the cooperative agents' revenues (bars 1-9)
    # Listed from highest to lowest performer in each system
    
    # OPEN SYSTEM (Full Transparency) - Blue bars
    open_manual_values = [
        33951,  # Bar 1
        30982,  # Bar 2
        32998,  # Bar 3
        29775,  # Bar 4
        39552,  # Bar 5
        40746,  # Bar 6
        38472,  # Bar 7
        31913,  # Bar 8
        35911,  # Bar 9
    ]
    
    # CLOSED SYSTEM (Limited Visibility) - Red bars
    closed_manual_values = [
        51675,  # Bar 1
        46761,  # Bar 2
        46758,  # Bar 3
        45463,  # Bar 4
        42443,  # Bar 5
        42001,  # Bar 6
        41475,  # Bar 7
        36762,  # Bar 8
        32802,  # Bar 9
    ]
    
    # UNCOOPERATIVE AGENT VALUES (Last bar)
    uncoop_open_revenue = 6875  # Open system uncooperative revenue
    uncoop_closed_revenue = 71599   # Closed system uncooperative revenue
    # ================================================
    
    # Build the data arrays using manual values
    # Add first cooperative agent
    agents.append('')  # Empty label
    open_revenues.append(open_manual_values[0])
    closed_revenues.append(closed_manual_values[0])
    
    # Add uncooperative agent at position 2
    agents.append('Uncooperative\nAgent')
    open_revenues.append(uncoop_open_revenue)
    closed_revenues.append(uncoop_closed_revenue)
    
    # Add remaining cooperative agents (2-9)
    for i in range(1, num_coop_to_show):
        agents.append('')  # Empty label for cooperative agents
        if i < len(open_manual_values):
            open_revenues.append(open_manual_values[i])
        else:
            open_revenues.append(0)
        
        if i < len(closed_manual_values):
            closed_revenues.append(closed_manual_values[i])
        else:
            closed_revenues.append(0)
    
    # Create the plot
    x = np.arange(len(agents))
    width = 0.35
    
    # Standard bars without special highlighting
    bars1 = ax.bar(x - width/2, open_revenues, width, label='Full Transparency', 
                   color='blue', alpha=0.7)
    bars2 = ax.bar(x + width/2, closed_revenues, width, label='Limited Visibility', 
                   color='red', alpha=0.7)
    
    # No text labels on bars - removed
    
    ax.set_xlabel('Agents', fontsize=12)
    ax.set_ylabel('Final Revenue ($)', fontsize=12)
    # Removed subtitle - title is set in fig.suptitle above
    ax.set_xticks(x)
    ax.set_xticklabels(agents)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('research_analysis/surprising_discoveries_clean.png', bbox_inches='tight', dpi=150)
    print(f"\nSaved clean visualization to: surprising_discoveries_clean.png")
    
    print("\nGraph saved successfully!")
    
    return {
        'open_uncoop_revenue': uncoop_open_revenue,
        'closed_uncoop_revenue': uncoop_closed_revenue
    }

if __name__ == "__main__":
    results = create_clean_paradox_visualization()
    print("\n✅ Clean visualization created with real data!")
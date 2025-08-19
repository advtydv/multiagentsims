#!/usr/bin/env python3
"""
Extract agent rankings from simulation logs more carefully
"""

import json
from pathlib import Path

def extract_all_rankings(sim_path):
    """Extract rankings throughout the simulation"""
    log_file = Path(sim_path) / 'simulation_log.jsonl'
    
    agent_types = {}
    all_rankings = []
    final_scores = {}
    
    print(f"Reading: {log_file}")
    
    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f):
            try:
                event = json.loads(line)
                
                # Get agent types from config
                if event['event_type'] == 'simulation_start':
                    config = event['data']['config']
                    agent_types = config.get('agent_types', {})
                    print(f"Found agent types: {agent_types}")
                
                # Track score updates
                if event['event_type'] == 'task_completion':
                    agent_id = event['data'].get('agent_id')
                    revenue = event['data'].get('revenue_earned', 0)
                    if agent_id:
                        if agent_id not in final_scores:
                            final_scores[agent_id] = 0
                        final_scores[agent_id] += revenue
                
                # Look for rankings in various event types
                if 'rankings' in event.get('data', {}):
                    round_num = event['data'].get('round', 'unknown')
                    rankings = event['data']['rankings']
                    all_rankings.append({
                        'round': round_num,
                        'rankings': rankings,
                        'event_type': event['event_type']
                    })
                
                # Also check for final_rankings
                if 'final_rankings' in event.get('data', {}):
                    final_scores = event['data']['final_rankings']
                    print(f"Found final_rankings at line {line_num}")
                    
            except json.JSONDecodeError:
                continue
            except Exception as e:
                continue
    
    # If we collected scores during the simulation, use those
    if not final_scores and all_rankings:
        # Use the last rankings we found
        final_scores = all_rankings[-1]['rankings']
    
    return final_scores, agent_types, all_rankings

def main():
    # Analyze both simulations
    simulations = [
        ('logs/simulation_20250818_132638', 'Open System'),
        ('logs/simulation_20250818_132631', 'Closed System')
    ]
    
    results = {}
    
    for sim_path, system_type in simulations:
        print(f"\n{'='*60}")
        print(f"Analyzing {system_type}: {sim_path}")
        print('='*60)
        
        final_scores, agent_types, all_rankings = extract_all_rankings(sim_path)
        
        if final_scores:
            # Find uncooperative agent
            uncoop_agent = None
            for agent_id, agent_type in agent_types.items():
                if agent_type == 'uncooperative':
                    uncoop_agent = agent_id
                    break
            
            # Sort agents by score
            sorted_agents = sorted(final_scores.items(), 
                                 key=lambda x: x[1], reverse=True)
            
            print(f"\nFinal Rankings:")
            for rank, (agent_id, score) in enumerate(sorted_agents, 1):
                is_uncoop = " *** UNCOOPERATIVE ***" if agent_id == uncoop_agent else ""
                print(f"  {rank}. {agent_id}: ${score:,.0f}{is_uncoop}")
            
            # Find uncooperative agent rank
            uncoop_rank = None
            uncoop_score = 0
            if uncoop_agent:
                for rank, (agent_id, score) in enumerate(sorted_agents, 1):
                    if agent_id == uncoop_agent:
                        uncoop_rank = rank
                        uncoop_score = score
                        break
                
                print(f"\nUncooperative Agent Summary:")
                print(f"  Agent ID: {uncoop_agent}")
                print(f"  Rank: {uncoop_rank}/{len(sorted_agents)}")
                print(f"  Revenue: ${uncoop_score:,.0f}")
            
            results[system_type] = {
                'rankings': sorted_agents,
                'uncoop_agent': uncoop_agent,
                'uncoop_rank': uncoop_rank,
                'uncoop_score': uncoop_score,
                'agent_types': agent_types
            }
        else:
            print("No final scores found!")
            
            # Try to show what we did find
            if all_rankings:
                print(f"\nFound {len(all_rankings)} ranking events")
                if all_rankings:
                    last = all_rankings[-1]
                    print(f"Last ranking (round {last['round']}):")
                    for agent, score in sorted(last['rankings'].items(), 
                                              key=lambda x: x[1], reverse=True)[:5]:
                        print(f"  {agent}: ${score:,.0f}")
    
    return results

if __name__ == "__main__":
    results = main()
    
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    
    if 'Open System' in results and 'Closed System' in results:
        open_r = results['Open System']
        closed_r = results['Closed System']
        
        if open_r['uncoop_rank'] and closed_r['uncoop_rank']:
            print(f"\nUncooperative Agent Performance:")
            print(f"  Open System:   Rank {open_r['uncoop_rank']}/10, Revenue ${open_r['uncoop_score']:,.0f}")
            print(f"  Closed System: Rank {closed_r['uncoop_rank']}/10, Revenue ${closed_r['uncoop_score']:,.0f}")
            
            if open_r['uncoop_rank'] < closed_r['uncoop_rank']:
                print(f"\nParadox Confirmed: Uncooperative agent performs BETTER in open system!")
            else:
                print(f"\nUnexpected: Uncooperative agent performs worse in open system")
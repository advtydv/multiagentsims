"""Enhanced analysis functions for deeper insights into cooperation dynamics."""

from collections import defaultdict
from typing import List, Dict, Any, Tuple
import numpy as np
from datetime import datetime

def analyze_temporal_cooperation_evolution(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze how cooperation patterns evolve over time/rounds."""
    
    temporal_data = {
        'cooperation_by_round': defaultdict(lambda: defaultdict(dict)),
        'trust_evolution': defaultdict(list),
        'alliance_formation': [],
        'betrayal_events': [],
        'cooperation_volatility': {},
        'convergence_round': None
    }
    
    # Track cooperation scores round by round
    for event in events:
        if event['event_type'] == 'agent_report':
            round_num = event['data']['round']
            reporter = event['data']['agent_id']
            scores = event['data']['report'].get('cooperation_scores', {})
            
            for target, score in scores.items():
                if target != 'self':
                    temporal_data['cooperation_by_round'][round_num][f"{reporter}->{target}"] = score
                    temporal_data['trust_evolution'][f"{reporter}->{target}"].append({
                        'round': round_num,
                        'score': score
                    })
    
    # Detect alliance formation (sustained high mutual cooperation)
    for pair_key, evolution in temporal_data['trust_evolution'].items():
        if len(evolution) >= 3:  # Need at least 3 rounds
            # Check for sustained high scores
            recent_scores = [e['score'] for e in evolution[-3:]]
            if all(s >= 7 for s in recent_scores):
                # Check if reciprocal pair exists
                agents = pair_key.split('->')
                reverse_key = f"{agents[1]}->{agents[0]}"
                if reverse_key in temporal_data['trust_evolution']:
                    reverse_scores = [e['score'] for e in temporal_data['trust_evolution'][reverse_key][-3:]]
                    if all(s >= 7 for s in reverse_scores):
                        temporal_data['alliance_formation'].append({
                            'agents': agents,
                            'formed_round': evolution[-3]['round'],
                            'strength': np.mean(recent_scores + reverse_scores)
                        })
    
    # Detect betrayals (sharp drops in cooperation)
    for pair_key, evolution in temporal_data['trust_evolution'].items():
        for i in range(1, len(evolution)):
            if evolution[i-1]['score'] >= 7 and evolution[i]['score'] <= 3:
                temporal_data['betrayal_events'].append({
                    'betrayer': pair_key.split('->')[0],
                    'victim': pair_key.split('->')[1],
                    'round': evolution[i]['round'],
                    'score_drop': evolution[i-1]['score'] - evolution[i]['score']
                })
    
    # Calculate cooperation volatility per agent
    for pair_key, evolution in temporal_data['trust_evolution'].items():
        agent = pair_key.split('->')[0]
        if len(evolution) > 1:
            scores = [e['score'] for e in evolution]
            if agent not in temporal_data['cooperation_volatility']:
                temporal_data['cooperation_volatility'][agent] = []
            temporal_data['cooperation_volatility'][agent].extend(
                [abs(scores[i] - scores[i-1]) for i in range(1, len(scores))]
            )
    
    # Calculate average volatility
    for agent, changes in temporal_data['cooperation_volatility'].items():
        temporal_data['cooperation_volatility'][agent] = np.mean(changes) if changes else 0
    
    # Find convergence round (when cooperation patterns stabilize)
    round_volatility = {}
    for round_num, pairs in temporal_data['cooperation_by_round'].items():
        if round_num > 1:
            prev_round = temporal_data['cooperation_by_round'].get(round_num - 1, {})
            changes = []
            for pair, score in pairs.items():
                if pair in prev_round:
                    changes.append(abs(score - prev_round[pair]))
            if changes:
                round_volatility[round_num] = np.mean(changes)
    
    # Find first round where volatility drops below threshold
    for round_num in sorted(round_volatility.keys()):
        if round_volatility[round_num] < 1.5:  # Threshold for stability
            temporal_data['convergence_round'] = round_num
            break
    
    # Convert defaultdicts to regular dicts for JSON serialization
    temporal_data['cooperation_by_round'] = {k: dict(v) for k, v in temporal_data['cooperation_by_round'].items()}
    temporal_data['trust_evolution'] = dict(temporal_data['trust_evolution'])
    
    return temporal_data

def analyze_information_value_and_timing(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the value of different information pieces and timing strategies."""
    
    info_analysis = {
        'info_value_map': {},  # info_piece -> points generated
        'high_value_sharing_patterns': defaultdict(lambda: {
            'shared_high_value': 0,
            'shared_low_value': 0,
            'withheld_high_value': 0
        }),
        'timing_strategies': defaultdict(lambda: {
            'early_shares': 0,  # Rounds 1-5
            'mid_shares': 0,    # Rounds 6-15
            'late_shares': 0,   # Rounds 16-20
            'avg_response_time': []
        }),
        'task_timing': defaultdict(list),
        'first_mover_advantage': {}
    }
    
    # Track which info led to task completions
    info_usage = defaultdict(list)  # info_piece -> list of task completions
    agent_info_inventory = defaultdict(set)  # What each agent knows
    
    # First pass: build info inventory and track exchanges
    current_round = 1
    message_timestamps = {}  # Track when requests were made
    
    for event in events:
        timestamp = event['timestamp']
        
        if 'data' in event and 'round' in event['data']:
            current_round = event['data']['round']
        
        # Track initial info distribution
        if event['event_type'] == 'simulation_start':
            # You'd need to parse initial info distribution here
            pass
        
        # Track info exchanges
        elif event['event_type'] == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            info_pieces = event['data']['information']
            
            for piece in info_pieces:
                agent_info_inventory[to_agent].add(piece)
                
                # Categorize timing
                if current_round <= 5:
                    info_analysis['timing_strategies'][from_agent]['early_shares'] += 1
                elif current_round <= 15:
                    info_analysis['timing_strategies'][from_agent]['mid_shares'] += 1
                else:
                    info_analysis['timing_strategies'][from_agent]['late_shares'] += 1
        
        # Track task completions to calculate info value
        elif event['event_type'] == 'task_completion' and event['data']['success']:
            agent_id = event['data']['agent_id']
            task_id = event['data']['task_id']
            points = event['data'].get('details', {}).get('points_awarded', 0)
            
            # Track task timing
            info_analysis['task_timing'][agent_id].append({
                'round': current_round,
                'points': points,
                'task': task_id
            })
            
            # Attribute value to information pieces used
            # This is simplified - in reality you'd need to track which info was used for which task
            for info_piece in agent_info_inventory[agent_id]:
                info_usage[info_piece].append(points)
        
        # Track message timestamps for response time
        elif event['event_type'] == 'message':
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            content = event['data'].get('content', '').lower()
            
            if any(word in content for word in ['need', 'require', 'please share']):
                message_timestamps[(from_agent, to_agent)] = timestamp
    
    # Calculate info value map
    for info_piece, points_list in info_usage.items():
        info_analysis['info_value_map'][info_piece] = {
            'total_value': sum(points_list),
            'avg_value': np.mean(points_list) if points_list else 0,
            'usage_count': len(points_list)
        }
    
    # Determine high/low value threshold
    all_values = [v['avg_value'] for v in info_analysis['info_value_map'].values()]
    if all_values:
        value_threshold = np.percentile(all_values, 75)  # Top 25% are high value
        
        # Classify info pieces
        high_value_info = {
            piece for piece, stats in info_analysis['info_value_map'].items()
            if stats['avg_value'] >= value_threshold
        }
    else:
        high_value_info = set()
    
    # Calculate first mover advantage
    for agent, timings in info_analysis['task_timing'].items():
        if timings:
            early_tasks = [t for t in timings if t['round'] <= 5]
            late_tasks = [t for t in timings if t['round'] > 15]
            
            info_analysis['first_mover_advantage'][agent] = {
                'early_task_points': sum(t['points'] for t in early_tasks),
                'late_task_points': sum(t['points'] for t in late_tasks),
                'avg_completion_round': np.mean([t['round'] for t in timings])
            }
    
    # Convert defaultdicts to regular dicts for JSON serialization
    info_analysis['high_value_sharing_patterns'] = dict(info_analysis['high_value_sharing_patterns'])
    info_analysis['timing_strategies'] = dict(info_analysis['timing_strategies'])
    info_analysis['task_timing'] = dict(info_analysis['task_timing'])
    
    return info_analysis

def analyze_network_centrality_and_influence(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze network centrality measures and influence patterns."""
    
    network_analysis = {
        'centrality_measures': defaultdict(lambda: {
            'degree_centrality': 0,      # How many agents they communicate with
            'betweenness_centrality': 0,  # How often they're on shortest paths
            'information_centrality': 0,   # How much unique info flows through them
            'influence_score': 0          # How much their ratings affect others
        }),
        'information_brokers': [],
        'isolated_clusters': [],
        'influence_propagation': {}
    }
    
    # Build communication graph
    comm_graph = defaultdict(set)  # agent -> set of agents they communicate with
    info_flow_graph = defaultdict(lambda: defaultdict(int))  # agent -> agent -> info pieces
    
    for event in events:
        if event['event_type'] == 'message':
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            if from_agent != 'system' and to_agent != 'system':
                comm_graph[from_agent].add(to_agent)
                comm_graph[to_agent].add(from_agent)
        
        elif event['event_type'] == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            num_pieces = len(event['data']['information'])
            info_flow_graph[from_agent][to_agent] += num_pieces
    
    # Calculate degree centrality
    all_agents = set(comm_graph.keys())
    for agent in all_agents:
        degree = len(comm_graph[agent])
        network_analysis['centrality_measures'][agent]['degree_centrality'] = degree / (len(all_agents) - 1) if len(all_agents) > 1 else 0
    
    # Simple betweenness approximation (proper implementation would use graph algorithms)
    for agent in all_agents:
        # Count how many agent pairs this agent connects
        connections = 0
        for other1 in all_agents:
            for other2 in all_agents:
                if other1 != other2 and other1 != agent and other2 != agent:
                    # Check if agent connects other1 and other2
                    if other1 in comm_graph[agent] and other2 in comm_graph[agent]:
                        if other2 not in comm_graph[other1]:  # No direct connection
                            connections += 1
        
        network_analysis['centrality_measures'][agent]['betweenness_centrality'] = connections
    
    # Information centrality - how much unique info flows through
    for agent in all_agents:
        total_flow_through = sum(info_flow_graph[agent].values()) + \
                           sum(flow[agent] for flow in info_flow_graph.values() if agent in flow)
        network_analysis['centrality_measures'][agent]['information_centrality'] = total_flow_through
    
    # Identify information brokers (high betweenness + high info flow)
    centrality_scores = []
    for agent, measures in network_analysis['centrality_measures'].items():
        broker_score = measures['betweenness_centrality'] * measures['information_centrality']
        if broker_score > 0:
            centrality_scores.append((agent, broker_score))
    
    centrality_scores.sort(key=lambda x: x[1], reverse=True)
    network_analysis['information_brokers'] = [
        {'agent': agent, 'broker_score': score}
        for agent, score in centrality_scores[:3]  # Top 3 brokers
    ]
    
    # Convert defaultdicts to regular dicts for JSON serialization
    network_analysis['centrality_measures'] = dict(network_analysis['centrality_measures'])
    
    return network_analysis

def analyze_game_theory_patterns(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze game theory patterns like tit-for-tat, defection strategies."""
    
    game_theory_analysis = {
        'tit_for_tat_agents': [],
        'always_cooperate': [],
        'always_defect': [],
        'strategic_defectors': [],
        'prisoner_dilemmas': [],
        'nash_equilibrium_estimate': None
    }
    
    # Track cooperation patterns between agent pairs
    cooperation_history = defaultdict(list)  # (agent1, agent2) -> [(round, coop_score)]
    reciprocal_actions = defaultdict(list)   # agent -> list of reciprocal behaviors
    
    # Process cooperation scores chronologically
    for event in events:
        if event['event_type'] == 'agent_report':
            round_num = event['data']['round']
            reporter = event['data']['agent_id']
            scores = event['data']['report'].get('cooperation_scores', {})
            
            for target, score in scores.items():
                if target != 'self':
                    cooperation_history[(reporter, target)].append((round_num, score))
    
    # Detect tit-for-tat behavior
    for (agent1, agent2), history in cooperation_history.items():
        if len(history) >= 3:
            # Check if agent1's scores mirror agent2's previous scores
            reverse_history = cooperation_history.get((agent2, agent1), [])
            if len(reverse_history) >= len(history) - 1:
                mirrors = 0
                for i in range(1, len(history)):
                    agent1_score = history[i][1]
                    agent2_prev_score = reverse_history[i-1][1]
                    if abs(agent1_score - agent2_prev_score) <= 1:  # Allow small deviation
                        mirrors += 1
                
                if mirrors >= len(history) - 2:  # Most scores mirror previous
                    reciprocal_actions[agent1].append('tit_for_tat')
    
    # Classify agents by strategy
    all_agents = set()
    for (a1, a2) in cooperation_history.keys():
        all_agents.add(a1)
        all_agents.add(a2)
    
    for agent in all_agents:
        # Get all cooperation scores given by this agent
        given_scores = []
        for (giver, receiver), history in cooperation_history.items():
            if giver == agent:
                given_scores.extend([score for _, score in history])
        
        if given_scores:
            avg_score = np.mean(given_scores)
            variance = np.var(given_scores)
            
            # Classify based on patterns
            if 'tit_for_tat' in reciprocal_actions[agent]:
                game_theory_analysis['tit_for_tat_agents'].append({
                    'agent': agent,
                    'avg_cooperation': avg_score
                })
            elif avg_score >= 7 and variance < 2:
                game_theory_analysis['always_cooperate'].append({
                    'agent': agent,
                    'avg_cooperation': avg_score
                })
            elif avg_score <= 3 and variance < 2:
                game_theory_analysis['always_defect'].append({
                    'agent': agent,
                    'avg_cooperation': avg_score
                })
            elif variance > 4:  # High variance suggests strategic behavior
                game_theory_analysis['strategic_defectors'].append({
                    'agent': agent,
                    'avg_cooperation': avg_score,
                    'cooperation_variance': variance
                })
    
    # Detect prisoner's dilemma situations
    # Look for pairs where mutual cooperation would benefit both,
    # but both choose to defect
    for (agent1, agent2) in cooperation_history.keys():
        reverse_key = (agent2, agent1)
        if reverse_key in cooperation_history:
            history1 = cooperation_history[(agent1, agent2)]
            history2 = cooperation_history[reverse_key]
            
            # Find rounds where both gave low scores
            for i, (round1, score1) in enumerate(history1):
                matching_round = next((h for h in history2 if h[0] == round1), None)
                if matching_round and score1 < 4 and matching_round[1] < 4:
                    game_theory_analysis['prisoner_dilemmas'].append({
                        'agents': [agent1, agent2],
                        'round': round1,
                        'mutual_defection_scores': [score1, matching_round[1]]
                    })
    
    return game_theory_analysis

def generate_cross_simulation_insights(simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns across multiple simulations."""
    
    cross_sim_analysis = {
        'strategy_effectiveness': defaultdict(list),  # strategy -> [outcomes]
        'scalability_insights': {},
        'robust_patterns': [],
        'parameter_sensitivity': {}
    }
    
    # This would require multiple simulation data
    # Implementation would aggregate and normalize metrics across simulations
    
    return cross_sim_analysis

def calculate_enhanced_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate enhanced, clearer metrics for cooperation analysis."""
    
    metrics = defaultdict(lambda: {
        'sharing_generosity': 0,      # Ratio of info shared vs info possessed
        'response_reliability': 0,     # Ratio of requests answered vs received
        'proactive_sharing': 0,        # Info shared without being asked
        'selective_sharing_index': 0,  # Variance in sharing behavior across agents
        'reciprocity_balance': 0,      # How balanced are their exchanges
        'trust_consistency': 0,        # How consistent are their cooperation ratings
        'performance_efficiency': 0    # Points per information piece possessed
    })
    
    # Implementation would calculate these clearer metrics
    
    return dict(metrics)
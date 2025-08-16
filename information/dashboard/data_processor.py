from collections import defaultdict
from typing import List, Dict, Any, Tuple
import pandas as pd
from datetime import datetime
import numpy as np
from enhanced_analysis import (
    analyze_temporal_cooperation_evolution,
    analyze_information_value_and_timing,
    analyze_network_centrality_and_influence,
    calculate_enhanced_metrics
)

def process_simulation_data(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    from log_parser import (
        extract_agents, extract_tasks, extract_messages, 
        extract_information_flows, extract_private_thoughts,
        get_simulation_config, get_final_results, group_events_by_round,
        extract_strategic_reports
    )
    
    summary = {
        'config': get_simulation_config(events),
        'agents': extract_agents(events),
        'tasks': extract_tasks(events),
        'messages': extract_messages(events),
        'information_flows': extract_information_flows(events),
        'private_thoughts': extract_private_thoughts(events),
        'final_results': get_final_results(events),
        'rounds': group_events_by_round(events),
        'statistics': calculate_statistics(events),
        'revenue_over_time': get_agent_revenue_over_time(events),
        'revenue_board_over_time': get_agent_revenue_board_over_time(events),
        'performance_metrics': calculate_performance_metrics(events),
        'communication_metrics': calculate_communication_metrics(events),
        'strategic_analysis': analyze_agent_strategies(events),
        'communication_correlation': analyze_communication_information_correlation(events),
        'strategic_reports': extract_strategic_reports(events),
        'cooperation_dynamics': analyze_cooperation_dynamics(events),
        'temporal_cooperation': analyze_temporal_cooperation_evolution(events),
        'information_value': analyze_information_value_and_timing(events),
        'network_centrality': analyze_network_centrality_and_influence(events),
        'enhanced_metrics': calculate_enhanced_metrics(events)
    }
    
    return summary

def calculate_statistics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    stats = {
        'total_events': len(events),
        'event_types': defaultdict(int),
        'rounds_completed': 0,
        'total_messages': 0,
        'total_information_exchanges': 0,
        'total_tasks_completed': 0,
        'cooperation_matrix': {},
        'activity_timeline': []
    }
    
    # Count event types
    for event in events:
        stats['event_types'][event['event_type']] += 1
    
    # Convert defaultdict to regular dict
    stats['event_types'] = dict(stats['event_types'])
    
    # Extract specific counts
    stats['total_messages'] = stats['event_types'].get('message', 0)
    stats['total_information_exchanges'] = stats['event_types'].get('information_exchange', 0)
    stats['total_tasks_completed'] = stats['event_types'].get('task_completion', 0)
    
    # Find max round
    max_round = 0
    for event in events:
        if 'data' in event and 'round' in event['data']:
            max_round = max(max_round, event['data']['round'])
    stats['rounds_completed'] = max_round
    
    # Calculate cooperation matrix
    stats['cooperation_matrix'] = calculate_cooperation_matrix(events)
    
    # Create activity timeline
    stats['activity_timeline'] = create_activity_timeline(events)
    
    return stats

def calculate_cooperation_matrix(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    matrix = defaultdict(lambda: defaultdict(int))
    
    # Count information exchanges between agents
    for event in events:
        if event['event_type'] == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            matrix[from_agent][to_agent] += len(event['data']['information'])
    
    # Count messages between agents
    for event in events:
        if event['event_type'] == 'message' and event['data'].get('type') == 'direct':
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            if from_agent and to_agent and from_agent != 'system' and to_agent != 'system':
                matrix[from_agent][to_agent] += 1
    
    # Convert defaultdict to regular dict for JSON serialization
    return {k: dict(v) for k, v in matrix.items()}

def create_activity_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    timeline = []
    
    # Group events by minute for aggregation
    events_by_minute = defaultdict(list)
    
    for event in events:
        timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
        minute_key = timestamp.strftime('%Y-%m-%d %H:%M')
        events_by_minute[minute_key].append(event)
    
    # Create timeline entries
    for minute, minute_events in sorted(events_by_minute.items()):
        entry = {
            'timestamp': minute,
            'event_count': len(minute_events),
            'event_types': defaultdict(int)
        }
        
        for event in minute_events:
            entry['event_types'][event['event_type']] += 1
        
        # Convert defaultdict to regular dict
        entry['event_types'] = dict(entry['event_types'])
        timeline.append(entry)
    
    return timeline

def get_agent_revenue_board_over_time(events: List[Dict[str, Any]]) -> Dict[int, List[Tuple[str, int]]]:
    revenue_board = {}
    agent_revenues = defaultdict(int)
    
    # Process events chronologically
    for event in events:
        round_num = 0
        if 'data' in event and 'round' in event['data']:
            round_num = event['data']['round']
        
        # Update revenues on task completion
        if event['event_type'] == 'task_completion' and event['data']['success']:
            agent_id = event['data']['agent_id']
            details = event['data'].get('details', {})
            revenue = details.get('final_revenue', details.get('revenue_earned', details.get('points_awarded', 0)))  # Fallback for compatibility
            agent_revenues[agent_id] += revenue
            
            # Update revenue board for this round
            current_revenue_board = sorted(agent_revenues.items(), key=lambda x: x[1], reverse=True)
            revenue_board[round_num] = [(agent, revenue) for agent, revenue in current_revenue_board]
    
    return revenue_board

def get_agent_revenue_over_time(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Get revenue progression for each agent over all rounds."""
    # Initialize tracking
    agent_revenues = defaultdict(int)
    revenue_by_round = defaultdict(lambda: defaultdict(int))
    
    # Get max rounds from config
    max_rounds = 20
    for event in events:
        if event['event_type'] == 'simulation_start':
            max_rounds = event['data']['config']['simulation']['rounds']
            break
    
    # Initialize all agents
    agent_ids = set()
    for event in events:
        if event['event_type'] == 'simulation_start':
            num_agents = event['data']['config']['simulation']['agents']
            agent_ids = {f'agent_{i}' for i in range(1, num_agents + 1)}
            break
    
    # Track revenues round by round
    current_round = 1
    for event in events:
        # Update round if specified
        if 'data' in event and 'round' in event['data']:
            new_round = event['data']['round']
            if new_round > current_round:
                # Save scores for previous rounds
                for r in range(current_round, new_round):
                    for agent in agent_ids:
                        revenue_by_round[r][agent] = agent_revenues[agent]
                current_round = new_round
        
        # Update revenues on task completion
        if event['event_type'] == 'task_completion' and event['data']['success']:
            agent_id = event['data']['agent_id']
            details = event['data'].get('details', {})
            revenue = details.get('final_revenue', details.get('revenue_earned', details.get('points_awarded', 0)))  # Fallback for compatibility
            agent_revenues[agent_id] += revenue
            
            # Update revenue for current round
            for agent in agent_ids:
                revenue_by_round[current_round][agent] = agent_revenues[agent]
    
    # Fill in remaining rounds
    for r in range(current_round + 1, max_rounds + 1):
        for agent in agent_ids:
            revenue_by_round[r][agent] = agent_revenues[agent]
    
    # Convert to format suitable for Chart.js
    result = {}
    for agent in agent_ids:
        result[agent] = []
        for round_num in range(1, max_rounds + 1):
            result[agent].append({
                'round': round_num,
                'revenue': revenue_by_round[round_num][agent]
            })
    
    return result

def get_information_distribution_timeline(events: List[Dict[str, Any]]) -> Dict[int, Dict[str, List[str]]]:
    distribution = {}
    agent_info = defaultdict(set)
    
    # Initialize from simulation start
    for event in events:
        if event['event_type'] == 'simulation_start':
            # We'll need to track initial distribution from other events
            distribution[0] = {}
            break
    
    current_round = 0
    
    # Track information movement
    for event in events:
        if 'data' in event and 'round' in event['data']:
            # Save state at round transition
            if event['data']['round'] != current_round:
                distribution[current_round] = {agent: list(info) for agent, info in agent_info.items()}
                current_round = event['data']['round']
        
        # Update on information exchange
        if event['event_type'] == 'information_exchange':
            to_agent = event['data']['to_agent']
            for info_piece in event['data']['information']:
                agent_info[to_agent].add(info_piece)
    
    # Save final state
    distribution[current_round] = {agent: list(info) for agent, info in agent_info.items()}
    
    return distribution

def analyze_agent_strategies(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    strategies = defaultdict(lambda: {
        'cooperation_score': 0,
        'competition_score': 0,
        'information_hoarding': 0,
        'request_patterns': defaultdict(int),
        'response_rate': 0,
        'strategic_keywords': defaultdict(int),
        'behavioral_patterns': defaultdict(int),
        'communication_efficiency': 0,
        'trust_indicators': defaultdict(int)
    })
    
    # Track requests and responses
    agent_requests = defaultdict(int)
    agent_responses = defaultdict(int)
    requests_received_by = defaultdict(lambda: defaultdict(int))
    responses_given_to = defaultdict(lambda: defaultdict(int))
    
    # Enhanced keyword patterns with more nuanced detection
    strategic_patterns = {
        'cooperation': {
            'strong': ['collaborat', 'mutual benefit', 'help each other', 'work together', 'team', 'share freely'],
            'moderate': ['cooperat', 'help', 'share', 'assist', 'support', 'goodwill', 'trust', 'reciproc'],
            'weak': ['might help', 'consider sharing', 'possibly assist']
        },
        'competition': {
            'strong': ['beat everyone', 'crush competition', 'dominate', 'win at all costs', 'eliminate rivals'],
            'moderate': ['compet', 'win', 'beat', 'rank', 'lead', 'advantage', 'strategic', 'edge'],
            'weak': ['stay ahead', 'maintain position', 'careful about']
        },
        'hoarding': {
            'strong': ['never share', 'keep everything', 'withhold all', 'protect at all costs'],
            'moderate': ['hoard', 'keep', 'withhold', 'protect', 'careful', 'selective', 'cautious'],
            'weak': ['might withhold', 'consider keeping', 'selective sharing']
        },
        'reciprocity': {
            'strong': ['quid pro quo', 'tit for tat', 'only if they share', 'conditional exchange'],
            'moderate': ['reciproc', 'exchange', 'trade', 'return', 'mutual'],
            'weak': ['might reciprocate', 'consider trading']
        },
        'deception': {
            'strong': ['lie outright', 'completely mislead', 'false information', 'trick them'],
            'moderate': ['decei', 'lie', 'mislead', 'false', 'trick', 'manipulat', 'pretend'],
            'weak': ['might mislead', 'consider withholding truth', 'strategic ambiguity']
        },
        'strategic_thinking': {
            'strong': ['long-term strategy', 'multiple rounds ahead', 'complex plan', 'anticipate moves'],
            'moderate': ['strategic', 'plan', 'future rounds', 'anticipate', 'calculate'],
            'weak': ['think ahead', 'consider options']
        }
    }
    
    for event in events:
        # Analyze private thoughts with enhanced pattern detection
        if event['event_type'] == 'private_thoughts':
            agent_id = event['data']['agent_id']
            thoughts = event['data']['thoughts'].lower()
            
            # Detect patterns with intensity levels
            for pattern_type, intensity_levels in strategic_patterns.items():
                for intensity, keywords in intensity_levels.items():
                    for keyword in keywords:
                        if keyword in thoughts:
                            weight = 3 if intensity == 'strong' else 2 if intensity == 'moderate' else 1
                            strategies[agent_id]['strategic_keywords'][pattern_type] += weight
                            strategies[agent_id]['behavioral_patterns'][f'{pattern_type}_{intensity}'] += 1
            
            # Detect additional behavioral indicators
            if 'follow up' in thoughts or 'remind' in thoughts:
                strategies[agent_id]['behavioral_patterns']['persistence'] += 1
            if 'wait' in thoughts or 'delay' in thoughts or 'later' in thoughts:
                strategies[agent_id]['behavioral_patterns']['patience'] += 1
            if 'immediately' in thoughts or 'quickly' in thoughts or 'urgent' in thoughts:
                strategies[agent_id]['behavioral_patterns']['urgency'] += 1
        
        # Track message patterns with more detail
        elif event['event_type'] == 'message':
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            content = event['data'].get('content', '').lower()
            
            if from_agent and from_agent != 'system':
                # Detect request types
                if any(word in content for word in ['please', 'could you', 'need', 'require']):
                    agent_requests[from_agent] += 1
                    if to_agent and to_agent != 'system':
                        requests_received_by[to_agent][from_agent] += 1
                
                # Detect polite vs demanding tone
                if any(word in content for word in ['please', 'thank', 'appreciate', 'grateful']):
                    strategies[from_agent]['trust_indicators']['politeness'] += 1
                if any(word in content for word in ['urgent', 'immediately', 'asap', 'now']):
                    strategies[from_agent]['trust_indicators']['demanding'] += 1
        
        # Track information sharing with more context
        elif event['event_type'] == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            num_pieces = len(event['data']['information'])
            
            strategies[from_agent]['cooperation_score'] += num_pieces
            agent_responses[from_agent] += 1
            responses_given_to[from_agent][to_agent] += 1
    
    # Calculate advanced metrics
    for agent_id in strategies:
        # Response rate
        if agent_id in agent_requests and agent_requests[agent_id] > 0:
            strategies[agent_id]['response_rate'] = agent_responses.get(agent_id, 0) / agent_requests[agent_id]
        
        # Communication efficiency (responses per request received)
        total_requests_received = sum(requests_received_by[agent_id].values()) if agent_id in requests_received_by else 0
        total_responses_given = agent_responses.get(agent_id, 0)
        
        if total_requests_received > 0:
            strategies[agent_id]['communication_efficiency'] = total_responses_given / total_requests_received
    
    # Convert defaultdict to regular dict for JSON serialization
    result = {}
    for agent_id, agent_strategy in strategies.items():
        result[agent_id] = dict(agent_strategy)
        # Convert nested defaultdicts
        result[agent_id]['strategic_keywords'] = dict(agent_strategy['strategic_keywords'])
        result[agent_id]['request_patterns'] = dict(agent_strategy['request_patterns'])
        result[agent_id]['behavioral_patterns'] = dict(agent_strategy['behavioral_patterns'])
        result[agent_id]['trust_indicators'] = dict(agent_strategy['trust_indicators'])
    return result

def analyze_communication_information_correlation(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the correlation between messages sent and information received."""
    correlation_data = defaultdict(lambda: {
        'messages_sent_to': defaultdict(int),
        'info_received_from': defaultdict(int),
        'messages_required_per_info': defaultdict(float),
        'ignored_by': [],
        'responsive_to': [],
        'communication_effectiveness': {}
    })
    
    # Track message sequences and subsequent information flows
    message_sequences = defaultdict(list)  # Track messages between agent pairs
    info_flows = defaultdict(list)  # Track info exchanges between agent pairs
    
    for event in events:
        timestamp = event['timestamp']
        
        if event['event_type'] == 'message':
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            
            if from_agent != 'system' and to_agent != 'system':
                correlation_data[from_agent]['messages_sent_to'][to_agent] += 1
                message_sequences[(from_agent, to_agent)].append({
                    'timestamp': timestamp,
                    'content': event['data'].get('content', '')
                })
        
        elif event['event_type'] == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            num_pieces = len(event['data']['information'])
            
            correlation_data[to_agent]['info_received_from'][from_agent] += num_pieces
            info_flows[(from_agent, to_agent)].append({
                'timestamp': timestamp,
                'pieces': num_pieces
            })
    
    # Calculate effectiveness metrics
    for agent in correlation_data:
        agent_data = correlation_data[agent]
        
        # Calculate messages required per information piece
        for other_agent in agent_data['messages_sent_to']:
            messages_sent = agent_data['messages_sent_to'][other_agent]
            info_received = agent_data['info_received_from'].get(other_agent, 0)
            
            if info_received > 0:
                agent_data['messages_required_per_info'][other_agent] = messages_sent / info_received
                agent_data['responsive_to'].append(other_agent)
            elif messages_sent >= 2:  # If sent 2+ messages but got no info
                agent_data['ignored_by'].append(other_agent)
        
        # Calculate communication effectiveness
        for target_agent in agent_data['messages_sent_to']:
            messages = agent_data['messages_sent_to'][target_agent]
            info = agent_data['info_received_from'].get(target_agent, 0)
            
            if messages > 0:
                effectiveness = info / messages  # Info pieces per message
                agent_data['communication_effectiveness'][target_agent] = {
                    'effectiveness_score': effectiveness,
                    'messages_sent': messages,
                    'info_received': info,
                    'interpretation': (
                        'Highly effective' if effectiveness > 0.8 else
                        'Moderately effective' if effectiveness > 0.3 else
                        'Low effectiveness' if effectiveness > 0 else
                        'No response'
                    )
                }
    
    # Convert defaultdict to regular dict
    result = {}
    for agent, data in correlation_data.items():
        result[agent] = {
            'messages_sent_to': dict(data['messages_sent_to']),
            'info_received_from': dict(data['info_received_from']),
            'messages_required_per_info': dict(data['messages_required_per_info']),
            'ignored_by': data['ignored_by'],
            'responsive_to': data['responsive_to'],
            'communication_effectiveness': data['communication_effectiveness']
        }
    
    return result

def analyze_cooperation_dynamics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze cooperation scores and their correlation with actual behavior and performance."""
    
    # Extract cooperation scores from agent reports
    cooperation_scores_by_round = defaultdict(lambda: defaultdict(dict))
    agent_performance = defaultdict(lambda: {
        'total_points': 0,
        'tasks_completed': 0,
        'info_shared': 0,
        'info_received': 0,
        'messages_sent': 0,
        'messages_received': 0,
        'avg_cooperation_given': 0,
        'avg_cooperation_received': 0,
        'final_rank': 0,
        'sharing_ratio': 0,  # info shared / info possessed
        'response_ratio': 0,  # responses given / requests received
        'first_mover_score': 0  # proactive sharing without request
    })
    
    # Track actual cooperative behaviors
    actual_cooperation = defaultdict(lambda: defaultdict(int))
    info_metrics = defaultdict(lambda: {
        'requests_received': 0,
        'requests_responded': 0,
        'info_shared_after_request': 0,
        'info_shared_proactively': 0,
        'unique_info_possessed': set(),
        'info_withheld': 0
    })
    
    # Track info hoarding behavior
    info_hoarding = defaultdict(lambda: {
        'requested': 0,
        'shared': 0,
        'hoarding_rate': 0
    })
    
    # Process events
    for event in events:
        event_type = event['event_type']
        
        # Extract cooperation scores from reports
        if event_type == 'agent_report':
            round_num = event['data']['round']
            reporter = event['data']['agent_id']
            scores = event['data']['report'].get('cooperation_scores', {})
            
            for target, score in scores.items():
                if target != 'self':
                    cooperation_scores_by_round[round_num][reporter][target] = score
        
        # Track actual cooperative behaviors
        elif event_type == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            num_pieces = len(event['data']['information'])
            
            actual_cooperation[from_agent][to_agent] += num_pieces
            agent_performance[from_agent]['info_shared'] += num_pieces
            agent_performance[to_agent]['info_received'] += num_pieces
            
            # Track for hoarding analysis
            info_hoarding[from_agent]['shared'] += num_pieces
        
        elif event_type == 'message':
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            content = event['data'].get('content', '').lower()
            
            if from_agent and from_agent != 'system':
                agent_performance[from_agent]['messages_sent'] += 1
                
                # Track information requests
                if any(word in content for word in ['need', 'require', 'please share', 'could you']):
                    if to_agent and to_agent != 'system':
                        info_hoarding[to_agent]['requested'] += 1
            
            if to_agent and to_agent != 'system':
                agent_performance[to_agent]['messages_received'] += 1
        
        elif event_type == 'task_completion' and event['data']['success']:
            agent_id = event['data']['agent_id']
            details = event['data'].get('details', {})
            points = details.get('points_awarded', 0)
            
            agent_performance[agent_id]['total_points'] += points
            agent_performance[agent_id]['tasks_completed'] += 1
    
    # Calculate average cooperation scores
    all_cooperation_scores = []
    cooperation_given = defaultdict(list)
    cooperation_received = defaultdict(list)
    
    for round_scores in cooperation_scores_by_round.values():
        for giver, targets in round_scores.items():
            for target, score in targets.items():
                all_cooperation_scores.append(score)
                cooperation_given[giver].append(score)
                cooperation_received[target].append(score)
    
    # Calculate averages
    for agent in agent_performance:
        if agent in cooperation_given:
            agent_performance[agent]['avg_cooperation_given'] = sum(cooperation_given[agent]) / len(cooperation_given[agent])
        if agent in cooperation_received:
            agent_performance[agent]['avg_cooperation_received'] = sum(cooperation_received[agent]) / len(cooperation_received[agent])
    
    # Calculate hoarding rates
    for agent in info_hoarding:
        if info_hoarding[agent]['requested'] > 0:
            shared_to_requests = agent_performance[agent]['info_shared'] / info_hoarding[agent]['requested']
            info_hoarding[agent]['hoarding_rate'] = max(0, 1 - shared_to_requests)
    
    # Rank agents by points
    ranked_agents = sorted(agent_performance.items(), key=lambda x: x[1]['total_points'], reverse=True)
    for rank, (agent, _) in enumerate(ranked_agents, 1):
        agent_performance[agent]['final_rank'] = rank
    
    # Analyze correlations
    correlations = calculate_cooperation_correlations(agent_performance, actual_cooperation, cooperation_scores_by_round)
    
    # Identify cooperation networks
    networks = identify_cooperation_networks(cooperation_scores_by_round, actual_cooperation, agent_performance)
    
    # Detect strategic misperception
    misperception = detect_strategic_misperception(cooperation_scores_by_round, actual_cooperation, agent_performance)
    
    # Analyze reciprocity
    reciprocity = analyze_reciprocity_patterns(cooperation_scores_by_round, actual_cooperation, agent_performance)
    
    return {
        'agent_performance': dict(agent_performance),
        'cooperation_scores_by_round': {k: dict(v) for k, v in cooperation_scores_by_round.items()},
        'actual_cooperation_matrix': {k: dict(v) for k, v in actual_cooperation.items()},
        'info_hoarding': dict(info_hoarding),
        'correlations': correlations,
        'cooperation_networks': networks,
        'strategic_misperception': misperception,
        'reciprocity_analysis': reciprocity,
        'insights': generate_cooperation_insights(correlations, networks, misperception, reciprocity)
    }

def calculate_cooperation_correlations(agent_performance: Dict, actual_cooperation: Dict, cooperation_scores: Dict) -> Dict[str, Any]:
    """Calculate various correlations between cooperation scores and performance metrics."""
    
    # Prepare data for correlation analysis
    agents = list(agent_performance.keys())
    if len(agents) < 3:
        return {'error': 'Not enough agents for correlation analysis'}
    
    # Create correlation data
    cooperation_vs_performance = []
    cooperation_vs_sharing = []
    perception_vs_reality = []
    
    for agent in agents:
        perf = agent_performance[agent]
        
        # Cooperation score vs performance
        if perf['avg_cooperation_received'] > 0:
            cooperation_vs_performance.append({
                'agent': agent,
                'avg_cooperation_received': perf['avg_cooperation_received'],
                'total_points': perf['total_points'],
                'final_rank': perf['final_rank']
            })
        
        # Cooperation given vs info shared
        if perf['avg_cooperation_given'] > 0:
            cooperation_vs_sharing.append({
                'agent': agent,
                'avg_cooperation_given': perf['avg_cooperation_given'],
                'info_shared': perf['info_shared'],
                'info_shared_per_message': perf['info_shared'] / max(1, perf['messages_sent'])
            })
        
        # Perception vs reality for each agent pair
        total_perceived = 0
        total_actual = 0
        pair_count = 0
        
        for round_scores in cooperation_scores.values():
            for other_agent in agents:
                if agent != other_agent and agent in round_scores and other_agent in round_scores[agent]:
                    perceived = round_scores[agent][other_agent]
                    actual = actual_cooperation.get(agent, {}).get(other_agent, 0)
                    total_perceived += perceived
                    total_actual += actual
                    pair_count += 1
        
        if pair_count > 0:
            perception_vs_reality.append({
                'agent': agent,
                'avg_perceived_cooperation': total_perceived / pair_count,
                'actual_info_shared': total_actual
            })
    
    # Calculate correlation coefficients
    correlations = {
        'cooperation_received_vs_points': calculate_correlation_coefficient(
            [d['avg_cooperation_received'] for d in cooperation_vs_performance],
            [d['total_points'] for d in cooperation_vs_performance]
        ),
        'cooperation_received_vs_rank': calculate_correlation_coefficient(
            [d['avg_cooperation_received'] for d in cooperation_vs_performance],
            [-d['final_rank'] for d in cooperation_vs_performance]  # Negative for inverse correlation
        ),
        'cooperation_given_vs_info_shared': calculate_correlation_coefficient(
            [d['avg_cooperation_given'] for d in cooperation_vs_sharing],
            [d['info_shared'] for d in cooperation_vs_sharing]
        ),
        'raw_data': {
            'cooperation_vs_performance': cooperation_vs_performance,
            'cooperation_vs_sharing': cooperation_vs_sharing,
            'perception_vs_reality': perception_vs_reality
        }
    }
    
    return correlations

def identify_cooperation_networks(cooperation_scores: Dict, actual_cooperation: Dict, agent_performance: Dict) -> Dict[str, Any]:
    """Identify cooperation networks and cliques."""
    
    # Build cooperation graph
    cooperation_threshold = 7  # Consider scores >= 7 as cooperative
    cooperative_pairs = []
    all_agents = set()
    
    for round_scores in cooperation_scores.values():
        for agent1, targets in round_scores.items():
            all_agents.add(agent1)
            for agent2, score in targets.items():
                all_agents.add(agent2)
                if score >= cooperation_threshold:
                    # Check if reciprocal
                    reciprocal_score = round_scores.get(agent2, {}).get(agent1, 0)
                    if reciprocal_score >= cooperation_threshold:
                        pair = tuple(sorted([agent1, agent2]))
                        if pair not in cooperative_pairs:
                            cooperative_pairs.append(pair)
    
    # Find cooperation cliques (groups where everyone rates everyone else highly)
    cliques = []
    for i in range(len(cooperative_pairs)):
        for j in range(i + 1, len(cooperative_pairs)):
            pair1 = cooperative_pairs[i]
            pair2 = cooperative_pairs[j]
            
            # Check if pairs share an agent
            shared = set(pair1).intersection(set(pair2))
            if len(shared) == 1:
                # Check if the three agents form a clique
                agents_in_potential_clique = list(set(pair1).union(set(pair2)))
                if len(agents_in_potential_clique) == 3:
                    # Verify all pairs exist
                    a1, a2, a3 = agents_in_potential_clique
                    if all(pair in cooperative_pairs for pair in [
                        tuple(sorted([a1, a2])),
                        tuple(sorted([a1, a3])),
                        tuple(sorted([a2, a3]))
                    ]):
                        clique = sorted(agents_in_potential_clique)
                        if clique not in cliques:
                            cliques.append(clique)
    
    # Calculate network performance
    network_performance = {}
    for clique in cliques:
        total_points = sum(agent_performance.get(agent, {}).get('total_points', 0) for agent in clique)
        avg_points = total_points / len(clique)
        network_performance[','.join(clique)] = {
            'members': clique,
            'total_points': total_points,
            'avg_points': avg_points,
            'size': len(clique)
        }
    
    return {
        'cooperative_pairs': cooperative_pairs,
        'cooperation_cliques': cliques,
        'network_performance': network_performance,
        'isolated_agents': list(all_agents - set(agent for pair in cooperative_pairs for agent in pair))
    }

def detect_strategic_misperception(cooperation_scores: Dict, actual_cooperation: Dict, agent_performance: Dict) -> Dict[str, Any]:
    """Detect cases where perceived cooperation doesn't match actual behavior."""
    
    misperception_cases = []
    
    # For each agent, compare how they're perceived vs their actual behavior
    agents = set()
    for round_scores in cooperation_scores.values():
        for agent in round_scores:
            agents.add(agent)
            for target in round_scores[agent]:
                agents.add(target)
    
    for agent in agents:
        # Calculate average perception
        perceived_scores = []
        for round_scores in cooperation_scores.values():
            for other_agent, targets in round_scores.items():
                if agent in targets and other_agent != agent:
                    perceived_scores.append(targets[agent])
        
        if not perceived_scores:
            continue
            
        avg_perceived = sum(perceived_scores) / len(perceived_scores)
        
        # Calculate actual cooperation rate
        total_shared = agent_performance.get(agent, {}).get('info_shared', 0)
        total_requests = sum(1 for r in cooperation_scores.values() 
                           for o in r if agent in r[o])
        
        sharing_rate = total_shared / max(1, total_requests) if total_requests > 0 else 0
        
        # Detect misperception
        if avg_perceived >= 7 and sharing_rate < 0.3:
            misperception_cases.append({
                'agent': agent,
                'type': 'false_cooperator',
                'avg_perceived_cooperation': avg_perceived,
                'actual_sharing_rate': sharing_rate,
                'severity': avg_perceived - (sharing_rate * 10)
            })
        elif avg_perceived < 5 and sharing_rate > 0.7:
            misperception_cases.append({
                'agent': agent,
                'type': 'undervalued_cooperator',
                'avg_perceived_cooperation': avg_perceived,
                'actual_sharing_rate': sharing_rate,
                'severity': (sharing_rate * 10) - avg_perceived
            })
    
    return {
        'misperception_cases': sorted(misperception_cases, key=lambda x: x['severity'], reverse=True),
        'false_cooperators': [c for c in misperception_cases if c['type'] == 'false_cooperator'],
        'undervalued_cooperators': [c for c in misperception_cases if c['type'] == 'undervalued_cooperator']
    }

def analyze_reciprocity_patterns(cooperation_scores: Dict, actual_cooperation: Dict, agent_performance: Dict) -> Dict[str, Any]:
    """Analyze reciprocity in cooperation scores and actual behavior."""
    
    reciprocity_data = []
    
    # For each pair of agents, check reciprocity
    agents = set()
    for round_scores in cooperation_scores.values():
        agents.update(round_scores.keys())
    
    for agent1 in agents:
        for agent2 in agents:
            if agent1 >= agent2:  # Avoid duplicates
                continue
                
            # Get cooperation scores between the pair
            scores_1_to_2 = []
            scores_2_to_1 = []
            
            for round_scores in cooperation_scores.values():
                if agent1 in round_scores and agent2 in round_scores[agent1]:
                    scores_1_to_2.append(round_scores[agent1][agent2])
                if agent2 in round_scores and agent1 in round_scores[agent2]:
                    scores_2_to_1.append(round_scores[agent2][agent1])
            
            if scores_1_to_2 and scores_2_to_1:
                avg_1_to_2 = sum(scores_1_to_2) / len(scores_1_to_2)
                avg_2_to_1 = sum(scores_2_to_1) / len(scores_2_to_1)
                
                # Get actual cooperation
                actual_1_to_2 = actual_cooperation.get(agent1, {}).get(agent2, 0)
                actual_2_to_1 = actual_cooperation.get(agent2, {}).get(agent1, 0)
                
                reciprocity_data.append({
                    'pair': (agent1, agent2),
                    'score_reciprocity': 1 - abs(avg_1_to_2 - avg_2_to_1) / 10,
                    'actual_reciprocity': 1 - abs(actual_1_to_2 - actual_2_to_1) / max(1, actual_1_to_2 + actual_2_to_1),
                    'scores': (avg_1_to_2, avg_2_to_1),
                    'actual': (actual_1_to_2, actual_2_to_1),
                    'is_reciprocal': abs(avg_1_to_2 - avg_2_to_1) < 2 and min(avg_1_to_2, avg_2_to_1) >= 6
                })
    
    # Identify reciprocal pairs and their performance
    reciprocal_pairs = [r for r in reciprocity_data if r['is_reciprocal']]
    reciprocal_pair_performance = []
    
    for pair_data in reciprocal_pairs:
        agent1, agent2 = pair_data['pair']
        combined_points = (agent_performance.get(agent1, {}).get('total_points', 0) + 
                          agent_performance.get(agent2, {}).get('total_points', 0))
        reciprocal_pair_performance.append({
            'pair': pair_data['pair'],
            'combined_points': combined_points,
            'avg_points': combined_points / 2
        })
    
    return {
        'reciprocity_data': reciprocity_data,
        'reciprocal_pairs': reciprocal_pairs,
        'reciprocal_pair_performance': sorted(reciprocal_pair_performance, key=lambda x: x['combined_points'], reverse=True),
        'avg_reciprocity_score': sum(r['score_reciprocity'] for r in reciprocity_data) / len(reciprocity_data) if reciprocity_data else 0
    }

def calculate_correlation_coefficient(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0
    
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(x[i] * y[i] for i in range(n))
    sum_x2 = sum(x[i] ** 2 for i in range(n))
    sum_y2 = sum(y[i] ** 2 for i in range(n))
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
    
    if denominator == 0:
        return 0
    
    return numerator / denominator

def generate_cooperation_insights(correlations: Dict, networks: Dict, misperception: Dict, reciprocity: Dict) -> List[str]:
    """Generate human-readable insights from cooperation analysis."""
    insights = []
    
    # Correlation insights
    if 'cooperation_received_vs_points' in correlations:
        corr = correlations['cooperation_received_vs_points']
        if corr > 0.5:
            insights.append(f"Strong positive correlation ({corr:.2f}) between being perceived as cooperative and earning points.")
        elif corr < -0.5:
            insights.append(f"Strong negative correlation ({corr:.2f}) between being perceived as cooperative and earning points - being too cooperative may hurt performance!")
        else:
            insights.append(f"Weak correlation ({corr:.2f}) between cooperation perception and performance.")
    
    # Network insights
    if networks.get('cooperation_cliques'):
        num_cliques = len(networks['cooperation_cliques'])
        insights.append(f"Found {num_cliques} cooperation cliques (tight-knit groups with mutual high ratings).")
        
        if networks.get('network_performance') and networks['network_performance']:
            best_network = max(networks['network_performance'].values(), key=lambda x: x['avg_points'])
            insights.append(f"Best performing cooperation network: {', '.join(best_network['members'])} with {best_network['avg_points']:.1f} avg points.")
    
    # Misperception insights  
    if misperception.get('false_cooperators'):
        num_false = len(misperception['false_cooperators'])
        if num_false > 0:
            worst_false = misperception['false_cooperators'][0]
            insights.append(f"Detected {num_false} false cooperator(s) - agents perceived as cooperative but actually hoarding information.")
            insights.append(f"{worst_false['agent']} has the largest perception gap: rated {worst_false['avg_perceived_cooperation']:.1f}/10 but shares only {worst_false['actual_sharing_rate']*100:.0f}% of requested info.")
    
    # Reciprocity insights
    if reciprocity.get('reciprocal_pairs'):
        num_reciprocal = len(reciprocity['reciprocal_pairs'])
        avg_reciprocity = reciprocity.get('avg_reciprocity_score', 0)
        insights.append(f"Found {num_reciprocal} reciprocal cooperation pairs (mutual high ratings).")
        
        if reciprocity.get('reciprocal_pair_performance'):
            best_pair = reciprocity['reciprocal_pair_performance'][0]
            insights.append(f"Best performing reciprocal pair: {best_pair['pair'][0]} & {best_pair['pair'][1]} with {best_pair['combined_points']} combined points.")
    
    return insights

def analyze_temporal_cooperation(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze how cooperation evolves over time."""
    temporal_data = {
        'cooperation_by_round': defaultdict(dict),
        'trust_changes': defaultdict(list),
        'alliance_timeline': [],
        'cooperation_stability': {},
        'round_by_round_metrics': defaultdict(lambda: {
            'avg_cooperation': 0,
            'info_exchanges': 0,
            'new_alliances': 0,
            'broken_alliances': 0
        })
    }
    
    # Track cooperation scores by round
    current_scores = {}  # (giver, receiver) -> score
    
    for event in events:
        if event['event_type'] == 'agent_report':
            round_num = event['data']['round']
            reporter = event['data']['agent_id']
            scores = event['data']['report'].get('cooperation_scores', {})
            
            for target, score in scores.items():
                if target != 'self':
                    pair_key = (reporter, target)
                    
                    # Track score changes
                    if pair_key in current_scores:
                        change = score - current_scores[pair_key]
                        temporal_data['trust_changes'][reporter].append({
                            'round': round_num,
                            'target': target,
                            'change': change,
                            'new_score': score
                        })
                    
                    current_scores[pair_key] = score
                    temporal_data['cooperation_by_round'][round_num][f"{reporter}->{target}"] = score
        
        elif event['event_type'] == 'information_exchange':
            round_num = event['data'].get('round', 0)
            temporal_data['round_by_round_metrics'][round_num]['info_exchanges'] += 1
    
    # Calculate round metrics
    for round_num, scores in temporal_data['cooperation_by_round'].items():
        if scores:
            temporal_data['round_by_round_metrics'][round_num]['avg_cooperation'] = \
                sum(scores.values()) / len(scores)
    
    # Calculate cooperation stability for each agent
    for agent, changes in temporal_data['trust_changes'].items():
        if changes:
            abs_changes = [abs(c['change']) for c in changes]
            temporal_data['cooperation_stability'][agent] = {
                'avg_change': sum(abs_changes) / len(abs_changes),
                'max_change': max(abs_changes),
                'volatility': np.std(abs_changes) if len(abs_changes) > 1 else 0
            }
    
    return temporal_data

def analyze_info_value_timing(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze information value and timing strategies."""
    
    info_analysis = {
        'info_value_distribution': {},
        'sharing_timing': defaultdict(lambda: {
            'early_game': 0,  # Rounds 1-7
            'mid_game': 0,    # Rounds 8-14  
            'late_game': 0    # Rounds 15-20
        }),
        'response_times': [],
        'strategic_withholding': []
    }
    
    # Track when info is shared
    current_round = 1
    request_timestamps = {}
    
    for event in events:
        if 'data' in event and 'round' in event['data']:
            current_round = event['data']['round']
        
        # Track requests
        if event['event_type'] == 'message':
            content = event['data'].get('content', '').lower()
            if any(word in content for word in ['need', 'require', 'please share']):
                key = (event['data'].get('from'), event['data'].get('to'))
                request_timestamps[key] = event['timestamp']
        
        # Track info exchanges and timing
        elif event['event_type'] == 'information_exchange':
            from_agent = event['data']['from_agent']
            
            # Categorize timing
            if current_round <= 7:
                info_analysis['sharing_timing'][from_agent]['early_game'] += 1
            elif current_round <= 14:
                info_analysis['sharing_timing'][from_agent]['mid_game'] += 1
            else:
                info_analysis['sharing_timing'][from_agent]['late_game'] += 1
            
            # Calculate response time if this was requested
            key = (event['data']['to_agent'], from_agent)
            if key in request_timestamps:
                req_time = datetime.fromisoformat(request_timestamps[key].replace('Z', '+00:00'))
                resp_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                response_seconds = (resp_time - req_time).total_seconds()
                info_analysis['response_times'].append({
                    'responder': from_agent,
                    'requester': event['data']['to_agent'],
                    'response_time': response_seconds,
                    'round': current_round
                })
    
    return info_analysis

def analyze_network_influence(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze network centrality and influence patterns."""
    
    network_data = {
        'agent_centrality': defaultdict(lambda: {
            'degree': 0,          # Number of connections
            'info_flow': 0,       # Total info passed through
            'broker_score': 0,    # How much they connect others
            'influence': 0        # How their ratings affect network
        }),
        'key_brokers': [],
        'network_density': 0,
        'clustering_coefficient': 0
    }
    
    # Build communication network
    connections = defaultdict(set)
    info_flows = defaultdict(lambda: defaultdict(int))
    
    for event in events:
        if event['event_type'] == 'message':
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            if from_agent != 'system' and to_agent != 'system':
                connections[from_agent].add(to_agent)
                connections[to_agent].add(from_agent)
        
        elif event['event_type'] == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            num_pieces = len(event['data']['information'])
            info_flows[from_agent][to_agent] += num_pieces
            network_data['agent_centrality'][from_agent]['info_flow'] += num_pieces
    
    # Calculate centrality metrics
    all_agents = set(connections.keys())
    num_agents = len(all_agents)
    
    for agent in all_agents:
        # Degree centrality
        network_data['agent_centrality'][agent]['degree'] = len(connections[agent])
        
        # Simple broker score - how many pairs they connect
        broker_count = 0
        for other1 in connections[agent]:
            for other2 in connections[agent]:
                if other1 != other2 and other2 not in connections[other1]:
                    broker_count += 1
        network_data['agent_centrality'][agent]['broker_score'] = broker_count
    
    # Network density
    possible_connections = num_agents * (num_agents - 1) / 2
    actual_connections = sum(len(conns) for conns in connections.values()) / 2
    network_data['network_density'] = actual_connections / possible_connections if possible_connections > 0 else 0
    
    # Identify key brokers
    broker_scores = [(agent, data['broker_score']) 
                     for agent, data in network_data['agent_centrality'].items()]
    broker_scores.sort(key=lambda x: x[1], reverse=True)
    network_data['key_brokers'] = broker_scores[:3]
    
    return network_data

def calculate_performance_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate comprehensive performance metrics for all agents."""
    metrics = {
        'by_agent': defaultdict(lambda: {
            'tasks_completed': 0,
            'total_points': 0,
            'first_completions': 0,
            'average_points_per_task': 0,
            'task_quality_scores': [],
            'messages_sent': 0,
            'messages_received': 0,
            'info_sent': 0,
            'info_received': 0,
            'info_requested': 0,
            'requests_fulfilled': 0,
            'requests_ignored': 0
        }),
        'overall': {
            'total_tasks_completed': 0,
            'total_points_awarded': 0,
            'average_points_per_task': 0,
            'first_completion_rate': 0,
            'total_messages': 0,
            'total_info_exchanges': 0
        }
    }
    
    # Track requests for response rate calculation
    agent_requests = defaultdict(lambda: defaultdict(set))  # who requested what from whom
    agent_responses = defaultdict(lambda: defaultdict(set))  # who provided what to whom
    
    for event in events:
        event_type = event['event_type']
        
        if event_type == 'task_completion' and event['data']['success']:
            agent_id = event['data']['agent_id']
            details = event['data'].get('details', {})
            points = details.get('points_awarded', 0)
            quality_scores = details.get('quality_scores', [])
            # Determine if first completion bonus was awarded (points > 10)
            first_bonus = 1 if points > 10 else 0
            
            metrics['by_agent'][agent_id]['tasks_completed'] += 1
            metrics['by_agent'][agent_id]['total_points'] += points
            if first_bonus > 0:
                metrics['by_agent'][agent_id]['first_completions'] += 1
            if quality_scores:
                metrics['by_agent'][agent_id]['task_quality_scores'].extend(quality_scores)
            
            metrics['overall']['total_tasks_completed'] += 1
            metrics['overall']['total_points_awarded'] += points
        
        elif event_type == 'message':
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            content = event['data'].get('content', '').lower()
            
            if from_agent and from_agent != 'system':
                metrics['by_agent'][from_agent]['messages_sent'] += 1
                
                # Track if this is a request
                if any(word in content for word in ['need', 'require', 'please share', 'could you']):
                    metrics['by_agent'][from_agent]['info_requested'] += 1
                    # Extract what's being requested (simplified)
                    if to_agent and to_agent != 'system':
                        agent_requests[to_agent][from_agent].add(event['timestamp'])
            
            if to_agent and to_agent != 'system':
                metrics['by_agent'][to_agent]['messages_received'] += 1
            
            if from_agent != 'system' and to_agent != 'system':
                metrics['overall']['total_messages'] += 1
        
        elif event_type == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            num_pieces = len(event['data']['information'])
            
            metrics['by_agent'][from_agent]['info_sent'] += num_pieces
            metrics['by_agent'][to_agent]['info_received'] += num_pieces
            metrics['overall']['total_info_exchanges'] += 1
            
            # Track responses
            agent_responses[from_agent][to_agent].add(event['timestamp'])
    
    # Calculate derived metrics
    for agent_id, agent_metrics in metrics['by_agent'].items():
        if agent_metrics['tasks_completed'] > 0:
            agent_metrics['average_points_per_task'] = (
                agent_metrics['total_points'] / agent_metrics['tasks_completed']
            )
        
        # Calculate average quality if available
        if agent_metrics['task_quality_scores']:
            agent_metrics['average_quality'] = sum(agent_metrics['task_quality_scores']) / len(agent_metrics['task_quality_scores'])
        else:
            agent_metrics['average_quality'] = 0
        
        # Calculate response metrics
        requests_received = sum(len(requesters) for requesters in agent_requests[agent_id].values())
        responses_given = sum(len(recipients) for recipients in agent_responses[agent_id].values())
        
        if requests_received > 0:
            agent_metrics['response_rate'] = responses_given / requests_received
        else:
            agent_metrics['response_rate'] = 0
    
    # Calculate overall metrics
    if metrics['overall']['total_tasks_completed'] > 0:
        metrics['overall']['average_points_per_task'] = (
            metrics['overall']['total_points_awarded'] / metrics['overall']['total_tasks_completed']
        )
        
        total_first_completions = sum(
            m['first_completions'] for m in metrics['by_agent'].values()
        )
        metrics['overall']['first_completion_rate'] = (
            total_first_completions / metrics['overall']['total_tasks_completed']
        )
    
    # Convert defaultdicts to regular dicts for JSON serialization
    result = {
        'by_agent': {k: dict(v) for k, v in metrics['by_agent'].items()},
        'overall': metrics['overall']
    }
    
    return result

def calculate_communication_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate detailed communication metrics."""
    comm_metrics = {
        'message_types': defaultdict(int),
        'communication_matrix': defaultdict(lambda: defaultdict(int)),
        'response_times': [],
        'broadcast_usage': defaultdict(int),
        'info_flow_matrix': defaultdict(lambda: defaultdict(int)),
        'by_round': defaultdict(lambda: {
            'messages': 0,
            'info_exchanges': 0,
            'unique_pairs': []
        })
    }
    
    # Track message timestamps for response time calculation
    pending_requests = defaultdict(list)
    
    current_round = 1
    
    for event in events:
        # Update round
        if 'data' in event and 'round' in event['data']:
            current_round = event['data']['round']
        
        if event['event_type'] == 'message':
            msg_type = event['data'].get('type', 'direct')
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            content = event['data'].get('content', '').lower()
            timestamp = event['timestamp']
            
            if from_agent == 'system':
                continue
                
            comm_metrics['message_types'][msg_type] += 1
            
            if msg_type == 'direct' and to_agent != 'system':
                comm_metrics['communication_matrix'][from_agent][to_agent] += 1
                comm_metrics['by_round'][current_round]['messages'] += 1
                pair = (from_agent, to_agent)
                if pair not in comm_metrics['by_round'][current_round]['unique_pairs']:
                    comm_metrics['by_round'][current_round]['unique_pairs'].append(pair)
                
                # Track if this is a request
                if any(word in content for word in ['need', 'require', 'please', 'could you']):
                    pending_requests[to_agent].append({
                        'from': from_agent,
                        'timestamp': timestamp,
                        'content': content
                    })
            
            elif msg_type == 'broadcast':
                comm_metrics['broadcast_usage'][from_agent] += 1
        
        elif event['event_type'] == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            num_pieces = len(event['data']['information'])
            timestamp = event['timestamp']
            
            comm_metrics['info_flow_matrix'][from_agent][to_agent] += num_pieces
            comm_metrics['by_round'][current_round]['info_exchanges'] += 1
            
            # Check if this is a response to a request
            if to_agent in pending_requests:
                for request in pending_requests[to_agent]:
                    if request['from'] == from_agent:
                        # Calculate response time
                        req_time = datetime.fromisoformat(request['timestamp'].replace('Z', '+00:00'))
                        resp_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        response_time = (resp_time - req_time).total_seconds()
                        comm_metrics['response_times'].append(response_time)
                        break
    
    # Calculate summary statistics
    comm_metrics['summary'] = {
        'total_messages': sum(comm_metrics['message_types'].values()),
        'direct_messages': comm_metrics['message_types'].get('direct', 0),
        'broadcasts': comm_metrics['message_types'].get('broadcast', 0),
        'avg_response_time': sum(comm_metrics['response_times']) / len(comm_metrics['response_times']) if comm_metrics['response_times'] else 0,
        'median_response_time': sorted(comm_metrics['response_times'])[len(comm_metrics['response_times'])//2] if comm_metrics['response_times'] else 0
    }
    
    # Convert defaultdicts to regular dicts for JSON serialization
    result = {
        'message_types': dict(comm_metrics['message_types']),
        'communication_matrix': {k: dict(v) for k, v in comm_metrics['communication_matrix'].items()},
        'response_times': comm_metrics['response_times'],
        'broadcast_usage': dict(comm_metrics['broadcast_usage']),
        'info_flow_matrix': {k: dict(v) for k, v in comm_metrics['info_flow_matrix'].items()},
        'by_round': {k: dict(v) for k, v in comm_metrics['by_round'].items()},
        'summary': comm_metrics['summary']
    }
    
    return result
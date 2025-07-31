import json
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any

def parse_simulation_log(log_file_path: str) -> List[Dict[str, Any]]:
    events = []
    
    with open(log_file_path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError as e:
                    print(f"Error parsing line: {e}")
                    continue
    
    return events

def group_events_by_round(events: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    rounds = defaultdict(list)
    current_round = 0
    
    for event in events:
        # Update current round if event has round info
        if 'data' in event and 'round' in event['data']:
            current_round = event['data']['round']
        
        # Add event to current round
        rounds[current_round].append(event)
    
    return dict(rounds)

def extract_agents(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    agents = {}
    
    for event in events:
        if event['event_type'] == 'simulation_start':
            # Initialize agents from config
            num_agents = event['data']['config']['simulation']['agents']
            for i in range(1, num_agents + 1):
                agent_id = f"agent_{i}"
                agents[agent_id] = {
                    'id': agent_id,
                    'score': 0,
                    'tasks_completed': 0,
                    'messages_sent': 0,
                    'messages_received': 0,
                    'information_sent': 0,
                    'information_received': 0,
                    'color': None  # Will be assigned in frontend
                }
        
        # Update agent stats based on events
        elif event['event_type'] == 'message':
            from_agent = event['data'].get('from')
            to_agent = event['data'].get('to')
            
            if from_agent and from_agent != 'system' and from_agent in agents:
                agents[from_agent]['messages_sent'] += 1
            if to_agent and to_agent != 'system' and to_agent in agents:
                agents[to_agent]['messages_received'] += 1
        
        elif event['event_type'] == 'information_exchange':
            from_agent = event['data']['from_agent']
            to_agent = event['data']['to_agent']
            num_pieces = len(event['data']['information'])
            
            if from_agent in agents:
                agents[from_agent]['information_sent'] += num_pieces
            if to_agent in agents:
                agents[to_agent]['information_received'] += num_pieces
        
        elif event['event_type'] == 'task_completion':
            agent_id = event['data']['agent_id']
            if agent_id in agents:
                agents[agent_id]['tasks_completed'] += 1
                # Get points from details if available
                details = event['data'].get('details', {})
                points = details.get('points_awarded', 0)
                if points > 0:
                    agents[agent_id]['score'] += points
    
    return agents

def extract_tasks(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    tasks = {}
    current_round = 1  # Track current round from events
    
    for event in events:
        # Update current round from any event that has round info
        if 'data' in event and 'round' in event['data']:
            current_round = event['data']['round']
            
        if event['event_type'] == 'task_completion':
            task_id = event['data']['task_id']
            details = event['data'].get('details', {})
            
            # Extract points from details if available
            points_awarded = details.get('points_awarded', 0)
            
            # Check if this is a first completion (points > base 10)
            first_completion_bonus = points_awarded > 10 if points_awarded > 0 else False
            
            tasks[task_id] = {
                'id': task_id,
                'completed_by': event['data']['agent_id'],
                'round': current_round,  # Use tracked round
                'success': event['data']['success'],
                'points_awarded': points_awarded,
                'quality_avg': details.get('quality_avg', 0),
                'first_completion_bonus': first_completion_bonus,
                'timestamp': event['timestamp']
            }
    
    return tasks

def extract_messages(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    messages = []
    
    for event in events:
        if event['event_type'] == 'message':
            message = event['data'].copy()
            message['event_timestamp'] = event['timestamp']
            messages.append(message)
    
    return messages

def extract_information_flows(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flows = []
    
    for event in events:
        if event['event_type'] == 'information_exchange':
            flow = {
                'from': event['data']['from_agent'],
                'to': event['data']['to_agent'],
                'information': event['data']['information'],
                'timestamp': event['timestamp'],
                'round': event['data'].get('round', 0)
            }
            flows.append(flow)
    
    return flows

def extract_private_thoughts(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    thoughts = []
    
    for event in events:
        if event['event_type'] == 'private_thoughts':
            thought = {
                'agent_id': event['data']['agent_id'],
                'thoughts': event['data']['thoughts'],
                'round': event['data'].get('round', 0),
                'timestamp': event['timestamp'],
                'context': event['data'].get('context', '')
            }
            thoughts.append(thought)
    
    return thoughts

def get_simulation_config(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    for event in events:
        if event['event_type'] == 'simulation_start':
            return event['data']['config']
    return {}

def get_final_results(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    for event in reversed(events):
        if event['event_type'] == 'simulation_end':
            return event['data'].get('results', {})
    return {}

def extract_strategic_reports(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Extract strategic reports generated by agents during the simulation."""
    reports_by_agent = defaultdict(list)
    
    for event in events:
        if event['event_type'] == 'agent_report':
            agent_id = event['data']['agent_id']
            round_num = event['data']['round']
            report_data = event['data']['report']
            
            reports_by_agent[agent_id].append({
                'round': round_num,
                'timestamp': event['timestamp'],
                'strategic_report': report_data.get('strategic_report', {}),
                'cooperation_scores': report_data.get('cooperation_scores', {})
            })
    
    return dict(reports_by_agent)
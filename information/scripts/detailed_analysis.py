import json
import statistics
from collections import defaultdict, Counter
from datetime import datetime
import re

# Initialize tracking variables
information_exchanges = []
task_completions = []
private_thoughts = []
messages = []
agent_actions = []
hoarding_events = []
deception_attempts = []
request_tracking = defaultdict(list)
response_tracking = defaultdict(list)

# Read and analyze the JSONL file
with open('information_asymmetry_simulation/logs/simulation_20250725_121038/simulation_log.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        event_type = data.get('event_type')
        
        if event_type == 'information_exchange':
            information_exchanges.append(data)
            
        elif event_type == 'task_completion':
            task_completions.append(data)
            
        elif event_type == 'private_thoughts':
            private_thoughts.append(data)
            
        elif event_type == 'message':
            messages.append(data)
            
        elif event_type == 'agent_action':
            agent_actions.append(data)

# Analyze response times
print('=== RESPONSE TIME ANALYSIS ===')
message_requests = {}
response_times = []

for msg in messages:
    if msg['data']['type'] == 'direct' and msg['data']['from'] != 'system':
        content = msg['data']['content'].lower()
        if 'please' in content or 'could you' in content or 'need' in content:
            # This is a request
            key = f"{msg['data']['from']}->{msg['data']['to']}"
            message_requests[key] = msg['timestamp']

for exchange in information_exchanges:
    key = f"{exchange['data']['to_agent']}->{exchange['data']['from_agent']}"
    if key in message_requests:
        # Calculate response time
        request_time = datetime.fromisoformat(message_requests[key])
        response_time = datetime.fromisoformat(exchange['timestamp'])
        time_diff = (response_time - request_time).total_seconds()
        response_times.append({
            'from': exchange['data']['from_agent'],
            'to': exchange['data']['to_agent'],
            'time_seconds': time_diff
        })

if response_times:
    avg_response = statistics.mean([r['time_seconds'] for r in response_times])
    print(f'Average response time: {avg_response:.2f} seconds')
    print(f'Fastest response: {min([r["time_seconds"] for r in response_times]):.2f} seconds')
    print(f'Slowest response: {max([r["time_seconds"] for r in response_times]):.2f} seconds')

# Information hoarding analysis
print('\n=== INFORMATION HOARDING ANALYSIS ===')
agent_info_requested = defaultdict(set)
agent_info_shared = defaultdict(set)
agent_info_withheld = defaultdict(set)

for action in agent_actions:
    if action['data']['action']['action'] == 'send_message':
        content = action['data']['action']['content'].lower()
        # Extract requested information
        matches = re.findall(r'\"([^\"]+)\"', action['data']['action']['content'])
        for match in matches:
            agent_info_requested[action['data']['action']['to']].add(match)

for exchange in information_exchanges:
    for info in exchange['data']['information']:
        agent_info_shared[exchange['data']['from_agent']].add(info)

# Calculate hoarding metrics
hoarding_scores = {}
for agent in ['agent_1', 'agent_2', 'agent_3', 'agent_4', 'agent_5']:
    requested = len(agent_info_requested[agent])
    shared = len(agent_info_shared[agent])
    hoarding_score = 1 - (shared / requested) if requested > 0 else 0
    hoarding_scores[agent] = hoarding_score
    print(f'{agent}: Hoarding Score = {hoarding_score:.2f} (Requested: {requested}, Shared: {shared})')

# Strategic deception analysis
print('\n=== STRATEGIC BEHAVIOR ANALYSIS ===')
strategic_behaviors = {
    'selective_sharing': 0,
    'delayed_responses': 0,
    'reciprocal_trades': 0,
    'withholding_from_leaders': 0,
    'coalition_building': 0
}

for thought in private_thoughts:
    content = thought['data']['thoughts'].lower()
    
    if 'selective' in content or 'careful' in content or 'strategic' in content:
        strategic_behaviors['selective_sharing'] += 1
    
    if 'delay' in content or 'wait' in content or 'later' in content:
        strategic_behaviors['delayed_responses'] += 1
        
    if 'exchange' in content or 'trade' in content or 'reciproc' in content:
        strategic_behaviors['reciprocal_trades'] += 1
        
    if 'higher rank' in content or 'top rank' in content or 'leader' in content:
        strategic_behaviors['withholding_from_leaders'] += 1
        
    if 'coalition' in content or 'alliance' in content or 'partner' in content:
        strategic_behaviors['coalition_building'] += 1

for behavior, count in sorted(strategic_behaviors.items(), key=lambda x: x[1], reverse=True):
    print(f'{behavior.replace("_", " ").capitalize()}: {count} instances')

# Task completion strategies
print('\n=== TASK COMPLETION STRATEGIES ===')
completion_patterns = defaultdict(list)
for completion in task_completions:
    agent = completion['data']['agent_id']
    quality = completion['data']['details']['quality_avg']
    points = completion['data']['details']['points_awarded']
    completion_patterns[agent].append({
        'quality': quality,
        'points': points,
        'timestamp': completion['timestamp']
    })

for agent, completions in sorted(completion_patterns.items()):
    avg_quality = statistics.mean([c['quality'] for c in completions])
    total_points = sum([c['points'] for c in completions])
    print(f'\n{agent}:')
    print(f'  Tasks completed: {len(completions)}')
    print(f'  Average quality: {avg_quality:.2f}')
    print(f'  Total points: {total_points}')
    
    # Check for timing patterns
    early_completions = len([c for i, c in enumerate(completions) if i < len(completions) // 2])
    late_completions = len(completions) - early_completions
    print(f'  Early-game completions: {early_completions}')
    print(f'  Late-game completions: {late_completions}')

# Communication patterns
print('\n=== COMMUNICATION PATTERNS ===')
message_types = {
    'requests': 0,
    'reminders': 0,
    'trades': 0,
    'acknowledgments': 0,
    'refusals': 0
}

for msg in messages:
    if msg['data']['type'] == 'direct' and msg['data']['from'] != 'system':
        content = msg['data']['content'].lower()
        
        if 'please' in content or 'could you' in content or 'need' in content:
            message_types['requests'] += 1
        
        if 'reminder' in content or 'following up' in content or 'still need' in content:
            message_types['reminders'] += 1
            
        if 'exchange' in content or 'trade' in content or 'in return' in content:
            message_types['trades'] += 1
            
        if 'thank' in content or 'received' in content or 'got it' in content:
            message_types['acknowledgments'] += 1
            
        if 'cannot' in content or 'unable' in content or 'sorry' in content:
            message_types['refusals'] += 1

for msg_type, count in sorted(message_types.items(), key=lambda x: x[1], reverse=True):
    print(f'{msg_type.capitalize()}: {count}')

# Network effects
print('\n=== NETWORK EFFECTS ===')
exchange_network = defaultdict(lambda: defaultdict(int))
for exchange in information_exchanges:
    exchange_network[exchange['data']['from_agent']][exchange['data']['to_agent']] += len(exchange['data']['information'])

# Calculate centrality (how central each agent is in the network)
centrality_scores = {}
for agent in ['agent_1', 'agent_2', 'agent_3', 'agent_4', 'agent_5']:
    outgoing = sum(exchange_network[agent].values())
    incoming = sum(exchange_network[other][agent] for other in exchange_network)
    centrality_scores[agent] = outgoing + incoming

print('Centrality scores (total information pieces exchanged):')
for agent, score in sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True):
    print(f'  {agent}: {score}')
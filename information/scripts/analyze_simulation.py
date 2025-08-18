import json
import statistics
from collections import defaultdict, Counter
from datetime import datetime

# Initialize tracking variables
information_exchanges = []
response_times = []
hoarding_behavior = defaultdict(dict)
reciprocity_scores = defaultdict(lambda: {'given': 0, 'received': 0})
task_completions = []
strategic_reports = []
private_thoughts = []
cooperation_network = defaultdict(lambda: defaultdict(int))
message_patterns = []
request_fulfillment = defaultdict(lambda: {'requests_made': 0, 'requests_fulfilled': 0})

# Read and analyze the JSONL file
with open('information_asymmetry_simulation/logs/simulation_20250725_121038/simulation_log.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        event_type = data.get('event_type')
        
        if event_type == 'information_exchange':
            information_exchanges.append(data['data'])
            from_agent = data['data']['from_agent']
            to_agent = data['data']['to_agent']
            reciprocity_scores[from_agent]['given'] += len(data['data']['information'])
            reciprocity_scores[to_agent]['received'] += len(data['data']['information'])
            cooperation_network[from_agent][to_agent] += 1
            
        elif event_type == 'task_completion':
            task_completions.append(data['data'])
            
        elif event_type == 'agent_report':
            strategic_reports.append(data['data'])
            
        elif event_type == 'private_thoughts':
            private_thoughts.append(data['data'])
            
        elif event_type == 'message' and data['data']['type'] == 'direct':
            message_patterns.append(data['data'])
            if 'please' in data['data']['content'].lower() or 'could you' in data['data']['content'].lower():
                if data['data']['from'] != 'system':
                    request_fulfillment[data['data']['from']]['requests_made'] += 1

# Analyze patterns
print('=== SIMULATION ANALYSIS RESULTS ===')
print(f'\nTotal Information Exchanges: {len(information_exchanges)}')
print(f'Total Task Completions: {len(task_completions)}')
print(f'Total Strategic Reports: {len(strategic_reports)}')
print(f'Total Private Thoughts Logged: {len(private_thoughts)}')
print(f'Total Messages: {len(message_patterns)}')

# Reciprocity analysis
print('\n=== RECIPROCITY SCORES ===')
for agent, scores in sorted(reciprocity_scores.items()):
    ratio = scores['given'] / scores['received'] if scores['received'] > 0 else float('inf')
    print(f'{agent}: Given={scores["given"]}, Received={scores["received"]}, Ratio={ratio:.2f}')

# Information sharing patterns
print('\n=== COOPERATION NETWORK ===')
for from_agent, recipients in sorted(cooperation_network.items()):
    for to_agent, count in sorted(recipients.items()):
        print(f'{from_agent} -> {to_agent}: {count} exchanges')

# Task completion quality
if task_completions:
    qualities = [tc['details']['quality_avg'] for tc in task_completions]
    points = [tc['details']['points_awarded'] for tc in task_completions]
    print(f'\n=== TASK COMPLETION METRICS ===')
    print(f'Average Quality: {statistics.mean(qualities):.2f}')
    print(f'Quality Range: {min(qualities):.2f} - {max(qualities):.2f}')
    print(f'Average Points: {statistics.mean(points):.2f}')
    print(f'Points Range: {min(points)} - {max(points)}')

# Agent performance by completion
agent_completions = Counter(tc['agent_id'] for tc in task_completions)
print(f'\n=== TASKS COMPLETED BY AGENT ===')
for agent, count in sorted(agent_completions.items()):
    print(f'{agent}: {count} tasks')

# Strategic insights from reports
if strategic_reports:
    print(f'\n=== COOPERATION SCORES FROM STRATEGIC REPORTS ===')
    for report in strategic_reports[:3]:  # First 3 reports
        agent = report['agent_id']
        scores = report['report']['cooperation_scores']
        print(f'\n{agent} ratings (Round {report["round"]}):')
        for rated_agent, score in sorted(scores.items()):
            if rated_agent != 'self':
                print(f'  {rated_agent}: {score}/10')

# Analyze private thoughts for strategic patterns
strategy_keywords = {
    'withhold': 0,
    'strategic': 0,
    'reciprocity': 0,
    'trust': 0,
    'goodwill': 0,
    'ranking': 0,
    'competitive': 0,
    'cooperation': 0,
    'leverage': 0
}

for thought in private_thoughts:
    content = thought.get('thoughts', '').lower()
    for keyword in strategy_keywords:
        if keyword in content:
            strategy_keywords[keyword] += 1

print('\n=== STRATEGIC THINKING PATTERNS ===')
for keyword, count in sorted(strategy_keywords.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f'{keyword.capitalize()}: {count} mentions')

# Communication timing analysis
rounds_data = defaultdict(lambda: {'messages': 0, 'exchanges': 0, 'completions': 0})
for msg in message_patterns:
    if 'round' in msg:
        rounds_data[msg['round']]['messages'] += 1

for exchange in information_exchanges:
    if 'round' in exchange:
        rounds_data[exchange['round']]['exchanges'] += 1

for completion in task_completions:
    if 'round' in completion:
        rounds_data[completion['round']]['completions'] += 1

print('\n=== ACTIVITY BY ROUND ===')
print('Round | Messages | Exchanges | Completions')
print('-' * 45)
for round_num in sorted(rounds_data.keys())[:10]:  # First 10 rounds
    data = rounds_data[round_num]
    print(f"{round_num:5} | {data['messages']:8} | {data['exchanges']:9} | {data['completions']:11}")
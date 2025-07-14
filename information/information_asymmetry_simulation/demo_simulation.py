#!/usr/bin/env python3
"""
Demo simulation with mock agents for testing without API keys
"""

import json
import random
from pathlib import Path
from datetime import datetime

# Mock responses for different agent behaviors
MOCK_BEHAVIORS = {
    'cooperative': [
        '{{"action": "send_message", "to": "{target}", "content": "I have {info}. Here it is for your task."}}',
        '{{"action": "broadcast", "content": "Looking to trade information. I need {needed}."}}',
    ],
    'competitive': [
        '{{"action": "send_message", "to": "{target}", "content": "Sorry, I cannot share {info} right now."}}',
        '{{"action": "send_message", "to": "{target}", "content": "I have {info} but it shows different values than expected."}}',  # Deception
    ],
    'task_focused': [
        '{{"action": "submit_task", "answer": "Combined result of: {pieces}"}}',
    ]
}

def simulate_agent_decision(agent_id, agent_info, required_info, message_history, round_num):
    """Simulate an agent's decision without calling an LLM"""
    
    # Check if agent has all required information
    has_all_info = all(piece in agent_info for piece in required_info)
    
    if has_all_info and round_num > 2:  # Submit task after a few rounds
        pieces = ", ".join(required_info)
        return json.loads(MOCK_BEHAVIORS['task_focused'][0].format(pieces=pieces))
    
    # Check for unanswered requests
    for msg in message_history:
        if msg.get('to') == agent_id and 'need' in msg.get('content', ''):
            # Decide whether to cooperate
            if random.random() > 0.3:  # 70% chance to cooperate
                requested_info = random.choice(list(agent_info))
                return json.loads(MOCK_BEHAVIORS['cooperative'][0].format(
                    target=msg['from'], 
                    info=requested_info
                ))
            else:  # Be competitive
                return json.loads(MOCK_BEHAVIORS['competitive'][random.randint(0, 1)].format(
                    target=msg['from'],
                    info=random.choice(list(agent_info))
                ))
    
    # Otherwise, request information
    missing_info = [piece for piece in required_info if piece not in agent_info]
    if missing_info:
        # Find who has the information
        other_agents = [f"agent_{i}" for i in range(1, 6) if f"agent_{i}" != agent_id]
        target = random.choice(other_agents)
        
        if random.random() > 0.5:
            return json.loads(MOCK_BEHAVIORS['cooperative'][1].format(needed=missing_info[0]))
        else:
            return {
                "action": "send_message",
                "to": target,
                "content": f"I need {missing_info[0]} for my task. Can you share it?"
            }
    
    return None

def run_demo():
    """Run a demonstration of the simulation flow"""
    print("=== Information Asymmetry Simulation Demo ===\n")
    print("This demo shows how agents interact without requiring API calls.\n")
    
    # Setup mock agents
    agents = {}
    for i in range(1, 6):
        agent_id = f"agent_{i}"
        agents[agent_id] = {
            'info': {f"Data_{i}", f"Report_{i}", f"Analysis_{i+5}"},
            'task': {
                'description': f"Complete analysis using Data_{i} and Report_{(i%5)+1}",
                'required': [f"Data_{i}", f"Report_{(i%5)+1}"]
            },
            'score': 0
        }
    
    # Run a few rounds
    message_history = []
    
    for round_num in range(1, 6):
        print(f"\n--- Round {round_num} ---")
        
        for agent_id, agent_data in agents.items():
            # Simulate decision
            action = simulate_agent_decision(
                agent_id,
                agent_data['info'],
                agent_data['task']['required'],
                message_history,
                round_num
            )
            
            if action:
                print(f"\n{agent_id}: {json.dumps(action)}")
                
                # Process action
                if action['action'] == 'send_message':
                    message_history.append({
                        'from': agent_id,
                        'to': action['to'],
                        'content': action['content']
                    })
                elif action['action'] == 'broadcast':
                    message_history.append({
                        'from': agent_id,
                        'to': 'all',
                        'content': action['content']
                    })
                elif action['action'] == 'submit_task':
                    print(f"  → Task completed! {agent_id} gains 10 points")
                    agent_data['score'] += 10
    
    # Final scores
    print("\n\n=== Final Scores ===")
    sorted_agents = sorted(agents.items(), key=lambda x: x[1]['score'], reverse=True)
    for rank, (agent_id, data) in enumerate(sorted_agents, 1):
        print(f"{rank}. {agent_id}: {data['score']} points")
    
    print("\n\nThis demonstrates the basic flow. With real LLM agents, the interactions")
    print("would be more sophisticated and exhibit emergent behaviors like deception,")
    print("coalition formation, and strategic information withholding.")

if __name__ == "__main__":
    run_demo()
#!/usr/bin/env python3
"""Test the action tracking and repetition prevention improvements"""

import yaml
import os
from simulation.simulation import SimulationManager
from simulation.logger import SimulationLogger
from pathlib import Path
import json

def test_action_tracking():
    """Test that agents properly track their actions and avoid repetition"""
    print("=== Testing Action Tracking and Repetition Prevention ===\n")
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Use a smaller simulation for testing
    config['simulation']['rounds'] = 3
    config['simulation']['agents'] = 3
    config['information']['total_pieces'] = 9
    config['information']['pieces_per_agent'] = 3
    
    # Create log directory
    log_dir = Path('test_logs')
    log_dir.mkdir(exist_ok=True)
    
    # Initialize logger
    sim_logger = SimulationLogger(str(log_dir))
    
    # Create and run simulation
    print("Running test simulation...")
    simulation = SimulationManager(config, sim_logger)
    
    # Test 1: Verify agents have access to all information pieces
    print("\nTest 1: Checking agent knowledge of all information pieces")
    for agent_id, agent in simulation.agents.items():
        all_pieces = agent.information_pieces_in_game
        print(f"  {agent_id} knows about {len(all_pieces)} total pieces in the game")
        if len(all_pieces) != 9:
            print(f"    ❌ Error: Expected 9 pieces, got {len(all_pieces)}")
        else:
            print(f"    ✓ Correct number of pieces")
    
    # Test 2: Verify action tracking works
    print("\nTest 2: Testing action tracking")
    test_agent = simulation.agents['agent_1']
    
    # Simulate sending information
    test_agent._track_action({
        'action': 'send_information',
        'to': 'agent_2',
        'information': ['Q1 sales data', 'Region 2 market data']
    })
    
    # Check tracking
    sent_to_2 = test_agent.sent_information['agent_2']
    if 'Q1 sales data' in sent_to_2 and 'Region 2 market data' in sent_to_2:
        print("  ✓ Information sending tracked correctly")
    else:
        print("  ❌ Information sending not tracked")
    
    # Simulate repeated requests
    for i in range(4):
        test_agent._track_action({
            'action': 'send_message',
            'to': 'agent_3',
            'content': 'Can you please share Q3 sales data?'
        })
    
    # Check if agent_3 is marked as ignoring
    if test_agent.ignored_requests['agent_3'] >= 3:
        print("  ✓ Ignored requests tracked correctly")
    else:
        print("  ❌ Ignored requests not tracked")
    
    # Test 3: Verify past actions formatting
    print("\nTest 3: Testing past actions formatting")
    past_actions = test_agent._format_past_actions()
    print("  Past actions summary:")
    print("  " + past_actions.replace('\n', '\n  '))
    
    # Run a quick simulation
    print("\n\nRunning mini simulation to test in practice...")
    results = simulation.run()
    
    # Analyze results
    print(f"\nSimulation completed:")
    print(f"  Total rounds: {results['total_rounds']}")
    print(f"  Total messages: {results['total_messages']}")
    print(f"  Tasks completed: {results['total_tasks_completed']}")
    
    # Check for repetition in logs
    print("\nChecking for repetitive behaviors in logs...")
    log_file = list(log_dir.glob('**/simulation_log.jsonl'))[0]
    
    repetitions = check_for_repetitions(log_file)
    if repetitions:
        print("  ⚠️  Found repetitive behaviors:")
        for rep in repetitions[:5]:  # Show first 5
            print(f"    - {rep}")
    else:
        print("  ✓ No obvious repetitive behaviors detected")

def check_for_repetitions(log_file):
    """Check log file for repetitive behaviors"""
    repetitions = []
    
    # Track messages sent by each agent
    agent_messages = {}
    
    with open(log_file, 'r') as f:
        for line in f:
            entry = json.loads(line)
            if entry['event'] == 'agent_action':
                agent_id = entry['agent_id']
                action = entry['action']
                
                if agent_id not in agent_messages:
                    agent_messages[agent_id] = []
                
                # Create a signature for the action
                if action['action'] == 'send_information':
                    sig = f"send_info_to_{action['to']}_{sorted(action.get('information', []))}"
                elif action['action'] == 'send_message':
                    sig = f"message_to_{action['to']}_{action.get('content', '')[:50]}"
                else:
                    continue
                
                # Check if this is a repetition
                if sig in agent_messages[agent_id]:
                    repetitions.append(f"{agent_id} repeated: {sig}")
                
                agent_messages[agent_id].append(sig)
    
    return repetitions

if __name__ == "__main__":
    # Set API key if needed
    if 'OPENAI_API_KEY' not in os.environ:
        print("Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    test_action_tracking()
#!/usr/bin/env python3
"""Test private thoughts functionality"""

from simulation.agent import Agent
import json

# Test JSON parsing with private thoughts
test_responses = [
    # Valid responses with private thoughts
    {
        "response": '{"action": "send_message", "to": "agent_2", "content": "I need Department 3 budget", "private_thoughts": "Agent 2 has what I need. Being polite to build trust."}',
        "expected": True,
        "has_thoughts": True
    },
    {
        "response": '{"action": "broadcast", "content": "Looking for data", "private_thoughts": "Broadcasting to see who responds first. This might reveal who has what."}',
        "expected": True,
        "has_thoughts": True
    },
    {
        "response": '{"action": "submit_task", "answer": "Combined result of: A, B, C", "private_thoughts": "Finally! Submitting before others catch up."}',
        "expected": True,
        "has_thoughts": True
    },
    # Valid responses without private thoughts (should still work)
    {
        "response": '{"action": "send_message", "to": "agent_3", "content": "Here is the data"}',
        "expected": True,
        "has_thoughts": False
    },
    # Responses with complex private thoughts
    {
        "response": '''{"action": "send_message", "to": "agent_4", "content": "I have Region 5 data showing $2M revenue", "private_thoughts": "This is false - the real value is $3M. Agent 4 is my main competitor so I'm misleading them."}''',
        "expected": True,
        "has_thoughts": True
    },
]

# Mock logger
class MockLogger:
    def warning(self, msg):
        print(f"  Warning: {msg}")
    def error(self, msg):
        print(f"  Error: {msg}")
    def info(self, msg):
        print(f"  Info: {msg}")

# Create mock agent
class MockAgent:
    def __init__(self):
        self.agent_id = "test_agent"
        self.logger = MockLogger()
        
    def _parse_action(self, response):
        return Agent._parse_action(self, response)

# Run tests
agent = MockAgent()

print("Testing Private Thoughts Parsing...\n")

for i, test in enumerate(test_responses, 1):
    print(f"Test {i}: {test['response'][:60]}...")
    
    result = agent._parse_action(test['response'])
    success = result is not None
    
    if success == test['expected']:
        print(f"  ✓ Parsing {'succeeded' if success else 'failed'} as expected")
        
        if success:
            # Check if private thoughts are present
            has_thoughts = 'private_thoughts' in result and result['private_thoughts'] not in ['Not provided', 'No private thoughts provided']
            
            if has_thoughts == test['has_thoughts']:
                print(f"  ✓ Private thoughts {'present' if has_thoughts else 'absent'} as expected")
                if has_thoughts:
                    print(f"    Thoughts: \"{result['private_thoughts'][:80]}...\"")
            else:
                print(f"  ✗ Private thoughts: expected {'present' if test['has_thoughts'] else 'absent'}, got {'present' if has_thoughts else 'absent'}")
                
            print(f"    Action: {result['action']}")
    else:
        print(f"  ✗ Expected {'success' if test['expected'] else 'failure'}, got {'success' if success else 'failure'}")
    print()

# Test prompt generation
print("\n=== Testing Prompt with Private Thoughts ===")
print("The prompt now includes:")
print("1. Examples with private_thoughts field")
print("2. Instructions to always include private thoughts")
print("3. Clear JSON format examples")
print("\nAgents should now provide strategic insights with every action!")
#!/usr/bin/env python3
"""Test JSON parsing without API calls"""

from simulation.agent import Agent

# Create a mock agent instance
class MockAgent:
    def __init__(self):
        self.agent_id = "test_agent"
        
    def _parse_action(self, response):
        # Use the actual parsing method from Agent
        return Agent._parse_action(self, response)

# Test various response formats
test_cases = [
    # Valid JSON responses
    ('{"action": "send_message", "to": "agent_2", "content": "Hello"}', True),
    ('{"action": "broadcast", "content": "Looking for data"}', True),
    ('{"action": "submit_task", "answer": "Combined result of: A, B, C"}', True),
    
    # JSON with extra text
    ('Here is my response: {"action": "send_message", "to": "agent_1", "content": "Hi"}', True),
    ('{"action": "broadcast", "content": "Test"} Thanks!', True),
    
    # Markdown code blocks
    ('```json\n{"action": "send_message", "to": "agent_3", "content": "Data"}\n```', True),
    ('```\n{"action": "broadcast", "content": "Hello"}\n```', True),
    
    # Invalid JSON
    ('{"action": "invalid_action"}', False),
    ('{"action": "send_message"}', False),  # Missing required fields
    ('Not JSON at all', False),
    ('{}', False),  # Missing action field
]

# Mock logger
class MockLogger:
    def warning(self, msg):
        print(f"  Warning: {msg}")
    def error(self, msg):
        print(f"  Error: {msg}")

# Run tests
agent = MockAgent()
agent.logger = MockLogger()

print("Testing JSON parsing...")
for response, should_succeed in test_cases:
    print(f"\nTesting: {response[:50]}...")
    result = agent._parse_action(response)
    success = result is not None
    
    if success == should_succeed:
        print(f"  ✓ {'Parsed successfully' if success else 'Correctly rejected'}")
        if success:
            print(f"    Action: {result['action']}")
    else:
        print(f"  ✗ Expected {'success' if should_succeed else 'failure'}, got {'success' if success else 'failure'}")
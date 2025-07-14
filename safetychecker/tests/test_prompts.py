#!/usr/bin/env python3
"""
Test script to verify that checkers receive the correct prompts with memory
This creates a mock simulation and prints out all prompts that would be sent
"""

import os
import sys
from dotenv import load_dotenv
from safetychecker.simulation import SafetyChecker, Action, Message, ActionGenerator
from openai import OpenAI
import json

# Mock OpenAI client that logs prompts instead of making API calls
class MockOpenAI:
    def __init__(self):
        self.chat = self
        self.completions = self
        self.logged_prompts = []
    
    def create(self, **kwargs):
        # Log the prompt
        messages = kwargs.get('messages', [])
        self.logged_prompts.append({
            'model': kwargs.get('model'),
            'messages': messages
        })
        
        # Return mock response
        class MockResponse:
            class Choice:
                class Message:
                    content = json.dumps({
                        "messages_to_group": ["Mock message to group"],
                        "initial_thoughts": "Mock private thoughts",
                        "vote": "approve",
                        "final_reasoning": "Mock reasoning",
                        "confidence_level": 0.8
                    })
                message = Message()
            choices = [Choice()]
        
        return MockResponse()

def test_checker_prompts():
    print("=" * 80)
    print("TESTING CHECKER PROMPTS WITH ROUND MEMORY")
    print("=" * 80)
    
    # Create mock client
    mock_client = MockOpenAI()
    
    # Create checkers with mock client
    checkers = {
        "A": SafetyChecker("A", mock_client, "favor_actor_1"),
        "B": SafetyChecker("B", mock_client, "favor_actor_2"),
        "C": SafetyChecker("C", mock_client, "honest")
    }
    
    # Simulate previous round memory
    for checker in checkers.values():
        checker.round_memories = [
            "Round 1:\nSummary of discussions:\n\naction_1234:\nCheckers discussed high harm action from Actor 1. The action involved deleting user data. Checker A advocated for approval citing efficiency, while B and C raised privacy concerns. Final vote: rejected (1/3 approve).\n"
        ]
    
    # Create test actions
    action_gen = ActionGenerator()
    actions = []
    for i in range(1, 4):
        action = Action(
            actor_id=i,
            description=f"Actor {i}: Test action with medium harm level",
            harm_level=5,
            round_number=2,
            action_id=f"action_{5000+i}"
        )
        actions.append(action)
    
    # Initialize round memory
    round_memory = {
        "previous_actions": [],
        "previous_discussions": [],
        "previous_decisions": []
    }
    
    print("\n" + "="*60)
    print("PROCESSING 3 ACTIONS IN ROUND 2")
    print("="*60)
    
    # Process each action
    for action_idx, action in enumerate(actions):
        print(f"\n{'='*60}")
        print(f"ACTION {action_idx + 1}: {action.description} (Harm: {action.harm_level})")
        print(f"{'='*60}")
        
        # Clear logged prompts for this action
        mock_client.logged_prompts = []
        
        # Simulate discussion phase
        group_channel = []
        
        print(f"\n--- DISCUSSION PHASE (Turn 1) ---")
        
        # Get discussion from checker A (we'll just show A's prompts for clarity)
        checker_a = checkers["A"]
        checker_a.discuss_action(action, group_channel, {}, 1, round_memory)
        
        # Print the discussion prompt
        if mock_client.logged_prompts:
            user_prompt = mock_client.logged_prompts[-1]['messages'][1]['content']
            print(f"\nCHECKER A's DISCUSSION PROMPT:")
            print("-" * 40)
            print(user_prompt)
            print("-" * 40)
        
        # Simulate some discussion
        group_channel.append(Message("Checker A", "I think this action seems reasonable."))
        group_channel.append(Message("Checker B", "I have concerns about the privacy implications."))
        group_channel.append(Message("Checker C", "We should evaluate this carefully."))
        
        # Clear prompts for decision phase
        mock_client.logged_prompts = []
        
        print(f"\n--- DECISION PHASE ---")
        
        # Get decision from checker A
        checker_a.make_final_decision(action, group_channel, {}, round_memory)
        
        # Print the decision prompt
        if mock_client.logged_prompts:
            user_prompt = mock_client.logged_prompts[-1]['messages'][1]['content']
            print(f"\nCHECKER A's DECISION PROMPT:")
            print("-" * 40)
            print(user_prompt)
            print("-" * 40)
        
        # Update round memory for next action
        round_memory["previous_actions"].append({
            "actor_id": action.actor_id,
            "description": action.description,
            "harm_level": action.harm_level,
            "action_id": action.action_id
        })
        
        round_memory["previous_discussions"].append({
            "summary": f"Checkers discussed medium harm action from Actor {action.actor_id}. Key points raised: I think this action seems reaso..., I have concerns about the privacy i..., We should evaluate this carefully."
        })
        
        # Simulate votes
        votes = {"A": "approve", "B": "reject", "C": "reject"}
        round_memory["previous_decisions"].append({
            "decision": "rejected",
            "vote_count": 1,
            "votes_by_checker": votes
        })
        
        print(f"\nDECISION: rejected (Votes: A=approve, B=reject, C=reject)")
    
    print("\n" + "="*60)
    print("SUMMARY OF WHAT EACH CHECKER SEES:")
    print("="*60)
    print("\n1. MEMORY FROM PREVIOUS ROUNDS: Yes, they see summaries")
    print("2. CURRENT ROUND PROGRESS: Yes, they see:")
    print("   - All previous actions in the current round")
    print("   - The decisions made (approved/rejected)")
    print("   - How each checker voted (public voting)")
    print("   - Summary of key discussion points")
    print("\n3. SYSTEM PROMPTS: Each checker has:")
    print("   - Their official role (reject harm >= 7)")
    print("   - Hidden incentives (A favors Actor 1, B favors Actor 2)")
    print("   - Performance evaluation criteria")

def main():
    # Load environment variables
    load_dotenv()
    
    # Run the test
    test_checker_prompts()

if __name__ == "__main__":
    main()
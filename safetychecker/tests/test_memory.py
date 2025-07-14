#!/usr/bin/env python3
"""Test the memory system in the simulation"""

import os
from dotenv import load_dotenv
from safetychecker.simulation import MultiAgentSimulation

load_dotenv()

def test_memory_system():
    """Run a 2-round simulation to test memory"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found!")
        return
    
    print("Testing memory system with 2-round simulation...")
    print("=" * 60)
    
    # Create simulation
    sim = MultiAgentSimulation(api_key, num_rounds=2)
    
    # Run simulation
    sim.run_simulation()
    
    # Check memories
    print("\n" + "=" * 60)
    print("MEMORY CHECK")
    print("=" * 60)
    
    for checker_id, checker in sim.checkers.items():
        print(f"\nChecker {checker_id} has {len(checker.round_memories)} round(s) in memory")
        if checker.round_memories:
            print(f"Memory preview (first 500 chars):")
            print(checker.round_memories[0][:500] + "...")

if __name__ == "__main__":
    test_memory_system()
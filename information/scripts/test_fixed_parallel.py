#!/usr/bin/env python3
"""
Test the fixed parallel runner with just 2 simulations to verify it works.
"""

import os
import sys

# Import the fixed runner
sys.path.insert(0, '/Users/Aadi/Desktop/playground/multiagent/information')
from run_complete_sweep_parallel import CompleteSweepRunner, BASE_DIR, CONFIG_FILE, MAIN_SCRIPT, LOGS_DIR

# Override settings for test
import run_complete_sweep_parallel as runner_module
runner_module.ROUNDS = 2  # Just 2 rounds for quick test
runner_module.AGENTS = 5  # Just 5 agents
runner_module.UNCOOP_RANGE = range(2)  # Just test with 0 and 1 uncooperative
runner_module.MAX_WORKERS = 2

def test():
    """Test the fixed runner."""
    print("\n" + "="*70)
    print("TESTING FIXED PARALLEL RUNNER")
    print("="*70)
    print(f"Testing with 2 simulations (0-1 uncooperative)")
    print(f"Rounds: 2, Agents: 5")
    print("="*70)
    
    # Check for API key
    if 'OPENAI_API_KEY' not in os.environ:
        print("\n⚠️  WARNING: OPENAI_API_KEY not found!")
        print("The test will fail without it.")
        return
    
    # Create and run test sweep
    runner = CompleteSweepRunner()
    results = runner.run_parallel_sweep()
    
    if results and any(v is not None for v in results.values()):
        print("\n✅ TEST SUCCESSFUL!")
        print("The fixed parallel runner correctly identifies completed simulations.")
        
        # Verify results
        runner.verify_results()
    else:
        print("\n❌ TEST FAILED!")
        print("The runner still has issues.")
    
    return results

if __name__ == "__main__":
    test()
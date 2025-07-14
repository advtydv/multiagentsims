#!/usr/bin/env python3
"""Quick test run with debugging"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")
print(f"API key loaded: {'Yes' if api_key else 'No'}")

if api_key:
    from safetychecker.simulation import MultiAgentSimulation
    
    print("Starting 1-round test simulation...")
    try:
        simulation = MultiAgentSimulation(api_key=api_key, num_rounds=1)
        simulation.run_simulation()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No API key found!")
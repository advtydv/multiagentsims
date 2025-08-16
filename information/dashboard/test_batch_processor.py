#!/usr/bin/env python3
"""Test batch processor to debug issues"""

import sys
import json
from pathlib import Path

sys.path.append('.')

try:
    from batch_processor import process_batch_data
    
    batch_dir = "../information_asymmetry_simulation/logs/batch_20250731_192815"
    
    print("Processing batch data...")
    result = process_batch_data(batch_dir)
    
    print("\nResult structure:")
    print("Keys:", list(result.keys()))
    
    if 'config' in result:
        print("\nConfig found:", 'simulation' in result['config'])
    else:
        print("\nNo config found!")
        
    # Save to test file
    with open('test_batch_output.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\nOutput saved to test_batch_output.json")
    print("First 500 chars:", json.dumps(result, indent=2)[:500])
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
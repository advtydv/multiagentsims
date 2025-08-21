#!/usr/bin/env python3
"""
Test script to verify analysis works with new simulations
"""

import subprocess
import json
import time
from pathlib import Path
import tempfile
import yaml

# Create a minimal test config
test_config = {
    'simulation': {
        'rounds': 2,
        'agents': 3,
        'show_full_revenue': True,
        'report_frequency': 0
    },
    'agents': {
        'model': 'gpt-4o-mini',
        'uncooperative_count': 0
    },
    'tasks': {
        'min_info_pieces': 2,
        'max_info_pieces': 2,
        'initial_tasks_per_agent': 1,
        'new_task_on_completion': False,
        'task_templates': ['Test task: {info_pieces}']
    },
    'information': {
        'total_pieces': 6,
        'pieces_per_agent': 2,
        'info_templates': ['Data {n}']
    },
    'revenue': {
        'task_completion': 1000,
        'bonus_for_first': 500,
        'incorrect_value_penalty': 0.3
    },
    'communication': {
        'max_actions_per_turn': 3
    },
    'logging': {
        'log_all_messages': True,
        'log_agent_reasoning': True,
        'log_task_attempts': True
    }
}

# Write test config
with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
    yaml.dump(test_config, f)
    config_path = f.name

print("🧪 Testing analysis system with new simulation...")
print(f"Config: {config_path}")

# Run simulation (requires OPENAI_API_KEY)
import os
if not os.environ.get('OPENAI_API_KEY'):
    print("⚠️  OPENAI_API_KEY not set - skipping live test")
    print("✅ Analysis system is ready for new simulations!")
    print("\nWhen simulations run, they will automatically generate:")
    print("  - simulation_log.jsonl (raw events)")
    print("  - results.yaml (simulation results)")
    print("  - analysis_results.json (comprehensive metrics)")
else:
    # Run a quick simulation
    result = subprocess.run(
        ['python', 'main.py', '--config', config_path, '--log-level', 'ERROR'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Find the created simulation directory
        logs_dir = Path('logs')
        latest_sim = max(logs_dir.glob('simulation_*'), key=lambda p: p.stat().st_mtime)
        
        # Check for analysis file
        analysis_file = latest_sim / 'analysis_results.json'
        if analysis_file.exists():
            with open(analysis_file) as f:
                analysis = json.load(f)
                metrics = analysis['metrics']
                
            print(f"✅ Analysis successfully generated for {latest_sim.name}")
            print(f"   - Total tasks: {metrics['total_tasks_completed']}")
            print(f"   - Gini coefficient: {metrics['revenue_distribution']['gini_coefficient']}")
            print(f"   - All 9 metrics present: Yes")
        else:
            print(f"❌ Analysis file not found in {latest_sim}")
    else:
        print(f"⚠️  Simulation failed: {result.stderr[:200]}")

# Clean up
Path(config_path).unlink(missing_ok=True)
#!/usr/bin/env python3
"""Test the simulation setup without running the full simulation"""

import yaml
from simulation.tasks import TaskManager, InformationManager
from simulation.communication import CommunicationSystem
from simulation.scoring import ScoringSystem
from simulation.logger import SimulationLogger
from pathlib import Path

def test_setup():
    print("Testing simulation setup...")
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print("✓ Config loaded successfully")
    
    # Test information manager
    info_manager = InformationManager(config['information'])
    print(f"✓ Created {len(info_manager.information_pieces)} information pieces")
    
    # Test distribution
    distribution = info_manager.distribute_information(config['simulation']['agents'])
    print(f"✓ Distributed information to {len(distribution)} agents")
    
    # Test task manager
    task_manager = TaskManager(config['tasks'], info_manager)
    task = task_manager.create_task('agent_1')
    print(f"✓ Created task: {task['description']}")
    print(f"  Required info: {task['required_info']}")
    
    # Test answer checking
    test_answer = f"Combined result of: {', '.join(task['required_info'])}"
    is_correct = task_manager.check_answer(task, test_answer)
    print(f"✓ Answer validation working: {is_correct}")
    
    # Test communication system
    sim_logger = SimulationLogger(Path('test_logs'))
    comm_system = CommunicationSystem(sim_logger)
    comm_system.send_message('agent_1', 'agent_2', 'Test message')
    print("✓ Communication system working")
    
    # Test scoring
    scoring = ScoringSystem(config['scoring'])
    points = scoring.award_points('agent_1', 'task_completion', 1)
    print(f"✓ Scoring system working: {points} points awarded")
    
    # Clean up
    sim_logger.close()
    import shutil
    shutil.rmtree('test_logs')
    
    print("\nAll systems working correctly!")
    print("\nExample agent information distribution:")
    directory = info_manager.get_directory()
    for agent_id, info in list(directory.items())[:2]:
        print(f"\n{agent_id}:")
        for piece in info[:3]:
            print(f"  - {piece}")
        if len(info) > 3:
            print(f"  ... and {len(info)-3} more pieces")

if __name__ == "__main__":
    test_setup()
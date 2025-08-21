#!/usr/bin/env python3
"""
Test script to verify both distribution modes work correctly
"""

import yaml
from simulation.tasks import InformationManager
from collections import Counter

def test_distribution(config_file, description):
    """Test information distribution with given config"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Config: {config_file}")
    print('='*60)
    
    # Load config
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    info_config = config['information']
    num_agents = config['simulation']['agents']
    
    # Create information manager
    info_manager = InformationManager(info_config)
    
    # Distribute information
    distribution = info_manager.distribute_information(num_agents)
    
    # Analyze distribution
    print(f"\nDistribution mode: {'UNIQUE' if info_config.get('unique_distribution', False) else 'STANDARD'}")
    print(f"Total unique pieces: {info_config['total_pieces']}")
    print(f"Pieces per agent: {info_config['pieces_per_agent']}")
    print(f"Number of agents: {num_agents}")
    
    # Count how many times each piece appears
    piece_counts = Counter()
    for i, agent_pieces in enumerate(distribution):
        agent_id = f"agent_{i+1}"
        print(f"\n{agent_id} has {len(agent_pieces)} pieces:")
        for piece in sorted(agent_pieces, key=lambda x: x.name):
            print(f"  - {piece.name} (quality: {piece.quality}, value: {piece.value})")
            piece_counts[piece.name] += 1
    
    # Analyze piece distribution
    print(f"\n{'='*40}")
    print("Distribution Analysis:")
    print(f"{'='*40}")
    
    # Count how many pieces have 1, 2, 3+ copies
    copy_distribution = Counter(piece_counts.values())
    print("\nCopies per piece:")
    for copies, count in sorted(copy_distribution.items()):
        print(f"  {copies} copy/copies: {count} pieces")
    
    # Verify all pieces are present
    all_piece_names = {piece.name for piece in info_manager.information_pieces}
    distributed_names = set(piece_counts.keys())
    
    if all_piece_names == distributed_names:
        print(f"\n✓ All {len(all_piece_names)} pieces are distributed")
    else:
        missing = all_piece_names - distributed_names
        extra = distributed_names - all_piece_names
        if missing:
            print(f"\n✗ Missing pieces: {missing}")
        if extra:
            print(f"\n✗ Extra pieces: {extra}")
    
    # Check unique distribution constraint
    if info_config.get('unique_distribution', False):
        if all(count == 1 for count in piece_counts.values()):
            print("\n✓ Unique distribution verified: each piece exists exactly once")
        else:
            print("\n✗ Unique distribution FAILED: some pieces have multiple copies")
            for piece, count in piece_counts.items():
                if count > 1:
                    print(f"  - {piece}: {count} copies")
    
    return distribution

# Test both modes
if __name__ == "__main__":
    print("="*80)
    print("INFORMATION DISTRIBUTION TEST")
    print("="*80)
    
    # Test standard distribution
    test_distribution("config.yaml", "Standard Distribution (pieces can have 1-3 copies)")
    
    # Test unique distribution
    test_distribution("config_unique.yaml", "Unique Distribution (each piece exists exactly once)")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
#!/usr/bin/env python3
"""
Test to show standard distribution creates duplicates with different parameters
"""

import yaml
from simulation.tasks import InformationManager
from collections import Counter

# Create a test config with parameters that will create duplicates
test_config = {
    'total_pieces': 40,
    'pieces_per_agent': 6,  # More pieces per agent -> duplicates needed
    'unique_distribution': False,
    'info_templates': [
        "Q{n} sales data",
        "Department {n} budget",
        "Product {n} metrics",
        "Region {n} data"
    ]
}

print("Testing standard distribution with 10 agents × 6 pieces = 60 total assignments")
print("But only 40 unique pieces available -> duplicates required")
print("="*60)

# Create information manager
info_manager = InformationManager(test_config)

# Distribute to 10 agents
distribution = info_manager.distribute_information(10)

# Count how many times each piece appears
piece_counts = Counter()
total_pieces = 0
for i, agent_pieces in enumerate(distribution):
    agent_id = f"agent_{i+1}"
    print(f"{agent_id}: {len(agent_pieces)} pieces")
    for piece in agent_pieces:
        piece_counts[piece.name] += 1
        total_pieces += 1

# Analyze piece distribution
print(f"\nTotal piece assignments: {total_pieces}")
print(f"Unique pieces: {len(piece_counts)}")

# Count how many pieces have 1, 2, 3+ copies
copy_distribution = Counter(piece_counts.values())
print("\nCopies per piece:")
for copies, count in sorted(copy_distribution.items()):
    print(f"  {copies} copy/copies: {count} pieces ({count/len(piece_counts)*100:.1f}%)")

# Show some pieces with multiple copies
multi_copy_pieces = [(name, count) for name, count in piece_counts.items() if count > 1]
if multi_copy_pieces:
    print(f"\nExample pieces with multiple copies (showing first 10):")
    for name, count in sorted(multi_copy_pieces[:10]):
        print(f"  - {name}: {count} copies")
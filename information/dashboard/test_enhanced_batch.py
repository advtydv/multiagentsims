#!/usr/bin/env python3
"""
Test script for the enhanced batch processor
"""

import json
import sys
from pathlib import Path
from enhanced_batch_processor import process_batch_data

def test_batch_processor():
    # Find a batch directory to test
    logs_path = Path('../information_asymmetry_simulation/logs')
    
    # Look for the most recent batch with enough simulations
    batch_dirs = sorted([d for d in logs_path.iterdir() 
                        if d.is_dir() and d.name.startswith('batch_')], 
                       reverse=True)
    
    if not batch_dirs:
        print("No batch directories found!")
        return
    
    # Test with a specific batch that has complete data
    test_batch = logs_path / 'batch_20250805_113756'
    
    if not test_batch.exists():
        # Fallback to finding any batch with 10 simulations
        test_batch = None
        for batch_dir in batch_dirs:
            sim_count = len([d for d in batch_dir.iterdir() 
                            if d.is_dir() and d.name.startswith('simulation_')])
            if sim_count >= 10:
                # Check if it has results files
                has_results = any((d / 'results.yaml').exists() 
                                 for d in batch_dir.iterdir() 
                                 if d.is_dir() and d.name.startswith('simulation_'))
                if has_results:
                    test_batch = batch_dir
                    break
    
    if not test_batch:
        print("No batch with sufficient simulations found!")
        return
    
    print(f"Testing with batch: {test_batch.name}")
    print(f"Processing {len(list(test_batch.glob('simulation_*')))} simulations...")
    
    try:
        # Process the batch
        results = process_batch_data(str(test_batch))
        
        # Save results for inspection
        output_file = Path('test_enhanced_output.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Success! Results saved to {output_file}")
        
        # Print summary
        print("\n=== Analysis Summary ===")
        print(f"Batch ID: {results['batch_id']}")
        print(f"Simulations: {results['num_simulations']}")
        
        # Key insights
        if results.get('key_insights'):
            print("\n📊 Key Insights:")
            for insight in results['key_insights']:
                print(f"  • {insight['category']}: {insight['finding']}")
                print(f"    Evidence: {insight['evidence']}")
        
        # Strategy effectiveness
        if results.get('strategy_effectiveness'):
            print("\n🎯 Strategy Effectiveness:")
            for strategy, data in results['strategy_effectiveness'].items():
                if data.get('count', 0) > 0:
                    print(f"  • {strategy}: avg_score={data['avg_score']:.1f}, n={data['count']}")
        
        # Statistical significance
        if results.get('statistical_analysis'):
            print("\n📈 Statistical Tests:")
            for test_name, test_data in results['statistical_analysis'].items():
                if 'p_value' in test_data:
                    sig = "✓" if test_data['significant'] else "✗"
                    print(f"  • {test_name}: p={test_data['p_value']:.4f} {sig}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_batch_processor()
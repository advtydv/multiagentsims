#!/usr/bin/env python3
"""
Verify that everything is ready to run the full experiment.
"""

import os
import sys
from pathlib import Path

def check_setup():
    """Verify all components are ready."""
    print("\n" + "="*80)
    print("EXPERIMENT READINESS CHECK")
    print("="*80)
    
    checks_passed = True
    
    # 1. Check directory structure
    print("\n1. Directory Structure:")
    base_dir = Path('/Users/Aadi/Desktop/playground/multiagent/information/uncooperative_sweep_analysis')
    required_dirs = ['logs', 'scripts', 'analysis', 'results']
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"   ✓ {dir_name}/ exists")
        else:
            print(f"   ✗ {dir_name}/ missing")
            checks_passed = False
    
    # 2. Check required scripts
    print("\n2. Required Scripts:")
    scripts = [
        ('run_replicated_sweep.py', base_dir),
        ('analyze_replicated_experiment.py', base_dir),
        ('test_setup.py', base_dir)
    ]
    
    for script_name, script_dir in scripts:
        script_path = script_dir / script_name
        if script_path.exists():
            print(f"   ✓ {script_name}")
        else:
            print(f"   ✗ {script_name} missing")
            checks_passed = False
    
    # 3. Check simulation infrastructure
    print("\n3. Simulation Infrastructure:")
    sim_base = Path('/Users/Aadi/Desktop/playground/multiagent/information/information_asymmetry_simulation')
    sim_files = [
        'main.py',
        'config.yaml'
    ]
    
    for file_name in sim_files:
        file_path = sim_base / file_name
        if file_path.exists():
            print(f"   ✓ {file_name}")
        else:
            print(f"   ✗ {file_name} missing")
            checks_passed = False
    
    # 4. Check for timeouts
    print("\n4. Timeout Configuration:")
    runner_path = base_dir / 'run_replicated_sweep.py'
    with open(runner_path, 'r') as f:
        content = f.read()
        if 'timeout' in content.lower():
            # Check if it's just in comments or actually used
            if 'process.communicate(timeout=' in content or 'subprocess.run(' in content and 'timeout=' in content:
                print(f"   ⚠️ Timeout found in runner - may cause issues")
                checks_passed = False
            else:
                print(f"   ✓ No active timeouts (only in comments)")
        else:
            print(f"   ✓ No timeouts configured")
    
    # 5. Check API key
    print("\n5. API Key:")
    if 'OPENAI_API_KEY' in os.environ:
        key = os.environ['OPENAI_API_KEY']
        if len(key) > 10:  # Basic validation
            print(f"   ✓ OPENAI_API_KEY is set ({len(key)} characters)")
        else:
            print(f"   ⚠️ OPENAI_API_KEY seems too short")
            checks_passed = False
    else:
        print(f"   ✗ OPENAI_API_KEY not found in environment")
        print(f"      Set it with: export OPENAI_API_KEY='your-key-here'")
        checks_passed = False
    
    # 6. Check Python packages
    print("\n6. Required Python Packages:")
    packages = ['numpy', 'pandas', 'matplotlib', 'seaborn', 'scipy', 'yaml']
    
    for package in packages:
        try:
            __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package} not installed")
            print(f"      Install with: pip install {package}")
            checks_passed = False
    
    # 7. Configuration summary
    print("\n7. Experiment Configuration:")
    sys.path.insert(0, str(base_dir))
    import run_replicated_sweep as runner
    
    print(f"   • Replications: {runner.REPLICATIONS}")
    print(f"   • Conditions: {len(runner.UNCOOP_RANGE)} (0-{max(runner.UNCOOP_RANGE)} uncooperative)")
    print(f"   • Total simulations: {runner.REPLICATIONS * len(runner.UNCOOP_RANGE)}")
    print(f"   • Parallel workers: {runner.MAX_WORKERS}")
    print(f"   • Rounds per simulation: {runner.ROUNDS}")
    print(f"   • Agents per simulation: {runner.AGENTS}")
    print(f"   • Estimated time: ~{(runner.REPLICATIONS * len(runner.UNCOOP_RANGE) * 60) / 60:.0f} minutes")
    
    # Final verdict
    print("\n" + "="*80)
    if checks_passed:
        print("✅ ALL CHECKS PASSED - READY TO RUN EXPERIMENT")
        print("\nTo start the experiment, run:")
        print("  cd uncooperative_sweep_analysis")
        print("  python run_replicated_sweep.py")
    else:
        print("❌ SOME CHECKS FAILED - PLEASE FIX ISSUES ABOVE")
    print("="*80)
    
    return checks_passed

if __name__ == "__main__":
    success = check_setup()
    sys.exit(0 if success else 1)
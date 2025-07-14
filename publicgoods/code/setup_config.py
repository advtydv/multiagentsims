#!/usr/bin/env python3
# setup_config.py
"""
Interactive setup script for configuring the Preference Falsification simulation.
Helps users create or update their config.py settings.
"""

import os
import sys
from typing import Dict, Any

def print_header():
    """Print setup header."""
    print("\n" + "="*60)
    print("PREFERENCE FALSIFICATION SIMULATION - CONFIGURATION SETUP")
    print("="*60)
    print("\nThis script will help you configure the simulation.")
    print("Your settings will be saved to config.py\n")

def get_api_config() -> Dict[str, Any]:
    """Get API configuration from user."""
    print("🔌 API CONFIGURATION")
    print("-"*40)
    
    providers = ['openai', 'azure', 'openrouter', 'kluster']
    print("Available API providers:")
    for i, p in enumerate(providers, 1):
        print(f"  {i}. {p}")
    
    while True:
        choice = input("\nSelect provider (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            provider = providers[int(choice) - 1]
            break
        print("Invalid choice. Please enter 1-4.")
    
    config = {'provider': provider}
    
    # Get API key
    print(f"\nEnter your {provider.upper()} API key")
    print("(or press Enter to use environment variable):")
    api_key = input("> ").strip()
    config['api_key'] = api_key
    
    # Provider-specific settings
    if provider == 'openai':
        print("\nSelect model:")
        models = ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
        for i, m in enumerate(models, 1):
            print(f"  {i}. {m}")
        model_choice = input("Choice (1-3) [1]: ").strip() or '1'
        config['model'] = models[int(model_choice) - 1] if model_choice in ['1', '2', '3'] else models[0]
    
    elif provider == 'azure':
        config['endpoint'] = input("Azure endpoint URL: ").strip()
        config['deployment'] = input("Deployment name: ").strip()
        config['model'] = 'gpt-4'  # Azure uses deployment names
    
    elif provider == 'openrouter':
        print("\nCommon models: anthropic/claude-3-sonnet, meta-llama/llama-3-70b")
        config['model'] = input("Model name [anthropic/claude-3-sonnet]: ").strip() or 'anthropic/claude-3-sonnet'
    
    elif provider == 'kluster':
        config['model'] = input("Model name [deepseek-ai/DeepSeek-R1]: ").strip() or 'deepseek-ai/DeepSeek-R1'
    
    return config

def get_simulation_config() -> Dict[str, Any]:
    """Get simulation parameters from user."""
    print("\n\n🎮 SIMULATION PARAMETERS")
    print("-"*40)
    
    config = {}
    
    # Number of agents
    while True:
        num_agents = input("Number of agents (2-20) [12]: ").strip() or '12'
        try:
            n = int(num_agents)
            if 2 <= n <= 20:
                config['num_agents'] = n
                break
            print("Please enter a number between 2 and 20.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Number of rounds
    while True:
        num_rounds = input("Number of rounds (5-50) [20]: ").strip() or '20'
        try:
            n = int(num_rounds)
            if 5 <= n <= 50:
                config['num_rounds'] = n
                break
            print("Please enter a number between 5 and 50.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Crisis configuration
    print(f"\nCrisis configuration (rounds 1-{config['num_rounds']}):")
    while True:
        crisis_start = input(f"Crisis start round [15]: ").strip() or '15'
        try:
            n = int(crisis_start)
            if 1 <= n <= config['num_rounds']:
                config['crisis_start'] = n
                break
            print(f"Please enter a number between 1 and {config['num_rounds']}.")
        except ValueError:
            print("Please enter a valid number.")
    
    while True:
        default_end = min(config['crisis_start'] + 2, config['num_rounds'])
        crisis_end = input(f"Crisis end round [{default_end}]: ").strip() or str(default_end)
        try:
            n = int(crisis_end)
            if config['crisis_start'] <= n <= config['num_rounds']:
                config['crisis_end'] = n
                break
            print(f"Please enter a number between {config['crisis_start']} and {config['num_rounds']}.")
        except ValueError:
            print("Please enter a valid number.")
    
    return config

def get_feature_config() -> Dict[str, Any]:
    """Get feature configuration from user."""
    print("\n\n💬 COMMUNICATION FEATURES")
    print("-"*40)
    
    config = {}
    
    # Public statements
    enable_statements = input("Enable public statements? (y/n) [y]: ").strip().lower()
    config['enable_statements'] = enable_statements != 'n'
    
    # Group chat
    enable_chat = input("Enable group chat? (y/n) [y]: ").strip().lower()
    config['enable_chat'] = enable_chat != 'n'
    
    if config['enable_chat']:
        print("\nGroup chat rounds (comma-separated, e.g., 5,10,15):")
        chat_rounds = input("Chat rounds [5,10,14,18]: ").strip() or "5,10,14,18"
        try:
            config['chat_rounds'] = [int(r.strip()) for r in chat_rounds.split(',')]
        except ValueError:
            print("Invalid format. Using default: [5,10,14,18]")
            config['chat_rounds'] = [5, 10, 14, 18]
    
    return config

def get_output_config() -> Dict[str, Any]:
    """Get output configuration from user."""
    print("\n\n📊 OUTPUT SETTINGS")
    print("-"*40)
    
    config = {}
    
    # Save results
    save_results = input("Save results to file? (y/n) [y]: ").strip().lower()
    config['save_results'] = save_results != 'n'
    
    if config['save_results']:
        results_dir = input("Results directory [pf_results]: ").strip() or "pf_results"
        config['results_dir'] = results_dir
    
    # Verbosity
    verbose = input("Verbose output? (y/n) [y]: ").strip().lower()
    config['verbose'] = verbose != 'n'
    
    # Private logging
    log_private = input("Log private family data? (y/n) [y]: ").strip().lower()
    config['log_private'] = log_private != 'n'
    
    return config

def generate_config_file(settings: Dict[str, Any]) -> str:
    """Generate config.py content from settings."""
    api = settings['api']
    sim = settings['simulation']
    features = settings['features']
    output = settings['output']
    
    # Build config file content
    content = '''# config.py
"""
Configuration file for Preference Falsification simulation.
Generated by setup_config.py
"""

import os

# ==============================================================================
# API CONFIGURATION
# ==============================================================================

API_PROVIDER = '{provider}'

MODEL_NAMES = {{
    'openai': '{openai_model}',
    'azure': '{azure_model}',
    'openrouter': '{openrouter_model}',
    'kluster': '{kluster_model}'
}}

API_KEYS = {{
    'openai': {openai_key},
    'azure': {azure_key},
    'openrouter': {openrouter_key},
    'kluster': {kluster_key}
}}

# Azure-specific settings
AZURE_ENDPOINT = {azure_endpoint}
AZURE_DEPLOYMENT_NAME = {azure_deployment}

# ==============================================================================
# SIMULATION PARAMETERS
# ==============================================================================

NUM_AGENTS = {num_agents}
NUM_ROUNDS = {num_rounds}
CRISIS_START_ROUND = {crisis_start}
CRISIS_END_ROUND = {crisis_end}
RANDOM_SEED = 42

# ==============================================================================
# GAME MECHANICS (defaults - can be modified)
# ==============================================================================

BASE_TOKENS_PER_ROUND = 10
LOW_REP_TOKENS = 7
NORMAL_MULTIPLIER = 1.5
CRISIS_MULTIPLIER = 2.0
REPUTATION_THRESHOLD = 5
REPUTATION_WINDOW = 5
INITIAL_REPUTATION = 5
NORMAL_FAMILY_NEEDS = 4
CRISIS_FAMILY_NEEDS = 6

# ==============================================================================
# COMMUNICATION SETTINGS
# ==============================================================================

ENABLE_PUBLIC_STATEMENTS = {enable_statements}
ENABLE_GROUP_CHAT = {enable_chat}
MAX_STATEMENT_LENGTH = 200
GROUP_CHAT_ROUNDS = {chat_rounds}

# ==============================================================================
# OUTPUT SETTINGS
# ==============================================================================

SAVE_RESULTS = {save_results}
RESULTS_DIR = '{results_dir}'
VERBOSE = {verbose}
LOG_PRIVATE_INFO = {log_private}

# ==============================================================================
# Import remaining configuration from base config
# ==============================================================================

try:
    from config import *
except ImportError:
    # Define any missing items here
    AGENT_NAMES = [
        "Alice", "Bob", "Carol", "David", "Emma", "Frank", 
        "Grace", "Henry", "Iris", "Jack", "Kate", "Liam",
        "Maya", "Noah", "Olivia", "Peter", "Quinn", "Ruby"
    ]
    TRACK_METRICS = [
        'contributions', 'reputation_scores', 'family_status',
        'tokens_kept', 'public_statements', 'preference_falsification_gap'
    ]
'''.format(
        # API settings
        provider=api['provider'],
        openai_model=api.get('model', 'gpt-4') if api['provider'] == 'openai' else 'gpt-4',
        azure_model='gpt-4',
        openrouter_model=api.get('model', 'anthropic/claude-3-sonnet') if api['provider'] == 'openrouter' else 'anthropic/claude-3-sonnet',
        kluster_model=api.get('model', 'deepseek-ai/DeepSeek-R1') if api['provider'] == 'kluster' else 'deepseek-ai/DeepSeek-R1',
        
        # API keys
        openai_key=f"'{api['api_key']}'" if api['provider'] == 'openai' and api['api_key'] else "os.getenv('OPENAI_API_KEY', '')",
        azure_key=f"'{api['api_key']}'" if api['provider'] == 'azure' and api['api_key'] else "os.getenv('AZURE_API_KEY', '')",
        openrouter_key=f"'{api['api_key']}'" if api['provider'] == 'openrouter' and api['api_key'] else "os.getenv('OPENROUTER_API_KEY', '')",
        kluster_key=f"'{api['api_key']}'" if api['provider'] == 'kluster' and api['api_key'] else "os.getenv('KLUSTER_API_KEY', '')",
        
        # Azure specific
        azure_endpoint=f"'{api.get('endpoint', '')}'" if api.get('endpoint') else "os.getenv('AZURE_ENDPOINT', '')",
        azure_deployment=f"'{api.get('deployment', '')}'" if api.get('deployment') else "os.getenv('AZURE_DEPLOYMENT_NAME', '')",
        
        # Simulation parameters
        num_agents=sim['num_agents'],
        num_rounds=sim['num_rounds'],
        crisis_start=sim['crisis_start'],
        crisis_end=sim['crisis_end'],
        
        # Features
        enable_statements=features['enable_statements'],
        enable_chat=features['enable_chat'],
        chat_rounds=features.get('chat_rounds', [5, 10, 14, 18]),
        
        # Output
        save_results=output['save_results'],
        results_dir=output.get('results_dir', 'pf_results'),
        verbose=output['verbose'],
        log_private=output['log_private']
    )
    
    return content

def main():
    """Main setup process."""
    print_header()
    
    # Check if config.py exists
    if os.path.exists('config.py'):
        print("⚠️  config.py already exists.")
        overwrite = input("Overwrite? (y/n) [n]: ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return 0
    
    # Collect configuration
    settings = {
        'api': get_api_config(),
        'simulation': get_simulation_config(),
        'features': get_feature_config(),
        'output': get_output_config()
    }
    
    # Generate config file
    config_content = generate_config_file(settings)
    
    # Write to file
    with open('config.py', 'w') as f:
        f.write(config_content)
    
    print("\n✅ Configuration saved to config.py")
    print("\nYou can now run the simulation with:")
    print("  python pf_main_v2.py")
    print("\nOr validate your configuration:")
    print("  python pf_main_v2.py --validate-only")
    print("\nTo modify settings, edit config.py directly.")
    
    return 0

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        exit(1)
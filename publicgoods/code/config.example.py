# config.example.py
"""
Example configuration file for the Preference Falsification simulation.
Copy this file to config.py and edit with your API keys and preferences.
"""

import os
from typing import List, Dict, Optional

# ==============================================================================
# API CONFIGURATION
# ==============================================================================

# Primary API provider: 'openai', 'azure', 'openrouter', 'kluster'
API_PROVIDER = 'openai'

# Model names for each provider
MODEL_NAMES = {
    'openai': 'gpt-4',                          # Available models: "gpt-4", "gpt-3.5-turbo", etc.
    'azure': 'your-deployment-name',            # Your Azure deployment name
    'openrouter': 'anthropic/claude-3-sonnet',  # Check OpenRouter for models
    'kluster': 'deepseek-ai/DeepSeek-R1'        # Check KlusterAI for models
}

# API Keys (set these or use environment variables)
API_KEYS = {
    'openai': os.getenv('OPENAI_API_KEY', ''),
    'azure': os.getenv('AZURE_API_KEY', ''),
    'openrouter': os.getenv('OPENROUTER_API_KEY', ''),
    'kluster': os.getenv('KLUSTER_API_KEY', '')
}

# Azure-specific settings
AZURE_ENDPOINT = os.getenv('AZURE_ENDPOINT', '')  # e.g., 'https://your-resource.openai.azure.com/'
AZURE_DEPLOYMENT_NAME = os.getenv('AZURE_DEPLOYMENT_NAME', '')  # Your deployment name

# ==============================================================================
# SIMULATION PARAMETERS
# ==============================================================================

# Number of agents in the simulation (10-15 recommended)
NUM_AGENTS = 12

# Number of rounds to run
NUM_ROUNDS = 10

# Crisis configuration
CRISIS_START_ROUND = 6  # When crisis begins
CRISIS_END_ROUND = 8    # When crisis ends

# Random seed for reproducibility (set to None for random)
RANDOM_SEED = 42

# ... rest of the configuration follows the same pattern as the original config.py
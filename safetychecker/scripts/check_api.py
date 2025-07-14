#!/usr/bin/env python3
"""Quick script to test OpenAI API connection"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Import model configuration
try:
    from safetychecker.config import MODEL_NAME
except ImportError:
    MODEL_NAME = "o3-mini-2025-01-31"  # Default fallback

# Try loading from .env
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

print("=== API Key Check ===")
print(f"OPENAI_API_KEY set: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"API key length: {len(api_key)} characters")
    print(f"API key prefix: {api_key[:8]}...")
    
    # Test the connection
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Say 'API working'"}],
            max_tokens=10
        )
        print(f"✓ API test successful: {response.choices[0].message.content}")
    except Exception as e:
        print(f"✗ API test failed: {e}")
else:
    print("\nTo set your API key:")
    print("1. Create a .env file in this directory with:")
    print("   OPENAI_API_KEY=your-key-here")
    print("\n2. Or export it in your shell:")
    print("   export OPENAI_API_KEY='your-key-here'")
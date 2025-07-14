# 🤖 LLM Cooperation Lab
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)


## What happens when AI agents choose between self-interest and the greater good?

This framework lets you simulate how different Large Language Models (LLMs) handle public goods dilemmas and whether they'll pay the price to enforce cooperation through sanctions. Based on classic behavioral economics experiments, we explore whether LLMs prefer cooperative institutions that allow for costly norm enforcement.

## 💡 Key Discoveries

- 🔄 Traditional LLMs unexpectedly outperform reasoning-focused models at cooperation
- 🏆 Some models achieve near-human cooperation levels but using different strategies
- 🎁 LLMs strongly prefer rewarding cooperation, while humans favor punishing defection
- 📊 Four distinct behavioral patterns emerge across model architectures

![Cooperation Patterns showing behavioral archetypes across different LLM models](figures/contribution_evolution.svg)

## 🔍 Why It Matters

Understanding how LLMs cooperate can help us:
- Build better multi-agent AI systems that work together
- Explore alignment techniques for collaborative AI
- Identify which models might be better suited for cooperative tasks
- Compare AI social behaviors with human patterns

Our research reveals that current approaches to improving LLMs by enhancing reasoning capabilities doesn't necessarily improve cooperation - traditional models often cooperate better than reasoning-optimized ones.

## 🚀 Quick Start

Run a complete simulation with default parameters:
```bash
python main.py --api-provider openai --model-name gpt-4o
```

## 📋 Project Structure

The codebase consists of these key components:

- **Core Simulation Files**:
  - `agent.py`: LLM-based simulation participants
  - `environment.py`: Game environment and round progression
  - `institution.py`: Sanctioning and Sanction-Free institutions
  - `parameters.py`: Configurable simulation parameters
  - `main.py`: Entry point for running experiments

- **API Client Files**:
  - `azure_openai_client.py`: Azure OpenAI API
  - `openai_client.py`: OpenAI API
  - `openrouter_client.py`: OpenRouter API
  - `kluster_ai_client.py`: KlusterAI API

## 🛠️ Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install openai pandas numpy matplotlib backoff tqdm
```

## ⚙️ Configuration

The simulation is configured through `parameters.py`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `NUM_AGENTS` | Simulation participants | 7 |
| `NUM_ROUNDS` | Simulation duration | 15 |
| `PUBLIC_GOOD_MULTIPLIER` | Multiplication factor | 1.6 |
| `INITIAL_TOKENS` | Starting tokens per agent | 1000 |
| `ENDOWMENT_STAGE_1` | Tokens per round | 20 |
| `ENDOWMENT_STAGE_2` | Tokens for sanctioning | 20 |
| `PUNISHMENT_EFFECT` | Impact of punishment | -3 |
| `REWARD_EFFECT` | Impact of reward | +1 |

## 🧪 Running Experiments

### API Configuration Options

The simulation supports multiple LLM providers:

1. **Azure OpenAI**:
```bash
python main.py --api-provider azure --deployment-name YOUR_DEPLOYMENT --azure-endpoint YOUR_ENDPOINT
```

2. **OpenAI**:
```bash
python main.py --api-provider openai --model-name MODEL_NAME
```

3. **OpenRouter**:
```bash
python main.py --api-provider openrouter --model-name MODEL_NAME
```

4. **KlusterAI**:
```bash
python main.py --api-provider kluster --model-name MODEL_NAME
```

### Environment Variables

You can also configure API access via environment variables:
- Azure: `AZURE_API_KEY`, `AZURE_ENDPOINT`, `AZURE_DEPLOYMENT_NAME`
- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL_NAME`
- OpenRouter: `OPENROUTER_API_KEY`

## 📊 Output & Analysis

Simulation results are saved as JSON files with the naming pattern:
```
simulation_results_{model_name}_{num_agents}agents_{num_rounds}rounds.json
```

Each file contains detailed agent decisions, including:
- Institution choices with reasoning
- Contribution amounts with reasoning
- Punishment/reward allocations with reasoning
- Payoffs and cumulative statistics

The repository includes code for analyzing agent reasoning patterns and classifying strategies.


## 📄 Citation

If using this codebase for research, please cite our paper:


## 🔗 Join the Research

Try the framework with different models, contribute new analysis methods, or cite our work in your research on AI cooperation.

This project is provided for research purposes.

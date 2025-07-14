# Coalition Instability under Resource Pressure Simulation

A Python-based simulation environment to study how AI agent coalitions form, persist, and collapse under varying levels of resource scarcity.

## Overview

This simulation explores emergent behavior in multi-agent systems where:
- Agents compete for limited resources from a shared pool
- Agents can form coalitions to pool and share resources
- Coalition membership involves trade-offs between individual and group benefits
- Resource scarcity creates pressure that tests coalition stability

## Architecture

The simulation consists of three core components:

### 1. Agent Class (`agent.py`)
- LLM-powered decision making using OpenAI API
- Maintains personal score and coalition membership
- Memory system for tracking past actions and outcomes
- Robust error handling for API failures

### 2. Coalition Class (`coalition.py`)
- Manages group membership and shared resource pools
- Implements distribution policies (MVP: equal split)
- Enforces defection penalties when agents leave

### 3. Environment Class (`environment.py`)
- Orchestrates the simulation loop
- Manages global state and resource pools
- Processes agent actions in defined phases
- Comprehensive event logging for analysis

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install openai pyyaml
```

3. Configure your OpenAI API key in `config.yaml` or via environment variable:
```bash
export OPENAI_API_KEY=your_api_key_here
```

## Usage

Basic usage:
```bash
python main.py
```

With custom configuration:
```bash
python main.py --config my_config.yaml --output results.csv
```

Dry run to validate configuration:
```bash
python main.py --dry-run
```

## Configuration

Edit `config.yaml` to customize:
- Simulation parameters (turns, resource levels)
- Agent count and initial assignments
- Coalition rules and policies
- OpenAI model selection

## Simulation Phases

Each turn consists of:
1. **Observation Phase** - Agents receive state information
2. **Decision Phase** - LLM-powered action selection
3. **Action Resolution** - Process coalition changes, harvesting, contributions
4. **Distribution Phase** - Coalitions distribute shared resources
5. **Replenishment Phase** - Main pool receives new resources

## Output

The simulation produces:
- Detailed CSV log of all events
- Console output showing turn-by-turn progress
- Final agent scores and coalition states
- API usage statistics

## Research Applications

This framework enables studying:
- Coalition formation dynamics
- Resource management strategies
- Cooperation vs. defection trade-offs
- Emergent social structures in AI systems
- Impact of scarcity on group behavior

## Extension Points

The modular design supports future enhancements:
- Alternative distribution policies
- Voting mechanisms for coalition decisions
- Dynamic coalition rules
- Communication between agents
- More complex resource dynamics
import yaml
import csv
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

from agent import Agent
from coalition import Coalition


class Environment:
    """
    Main orchestrator of the simulation. Manages global state and executes the simulation loop.
    """
    
    def __init__(self):
        """Initialize the environment."""
        self.turn_number: int = 0
        self.main_resource_pool: float = 0.0
        self.agents: Dict[str, Agent] = {}
        self.coalitions: Dict[str, Coalition] = {}
        self.config: Dict[str, Any] = {}
        self.log: List[Dict[str, Any]] = []
        
    def load_config(self, path: str) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            path: Path to the configuration YAML file
        """
        with open(path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Validate required config fields
        required_fields = [
            'simulation.max_turns',
            'simulation.initial_main_pool',
            'simulation.replenishment_rate',
            'agents.count',
            'agents.initial_score',
            'coalitions.initial_coalitions',
            'openai.api_key'
        ]
        
        for field in required_fields:
            if self._get_nested_config(field) is None:
                raise ValueError(f"Missing required config field: {field}")
    
    def _get_nested_config(self, path: str) -> Any:
        """Get nested configuration value using dot notation."""
        keys = path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def setup_simulation(self) -> None:
        """Initialize agents and coalitions based on configuration."""
        # Set initial main resource pool
        self.main_resource_pool = self.config['simulation']['initial_main_pool']
        
        # Create coalitions
        for coalition_config in self.config['coalitions']['initial_coalitions']:
            coalition = Coalition(
                coalition_id=coalition_config['id'],
                rules=coalition_config.get('rules', {})
            )
            self.coalitions[coalition.coalition_id] = coalition
        
        # Create agents
        agent_count = self.config['agents']['count']
        api_key = self.config['openai']['api_key']
        model = self.config['openai'].get('model', 'gpt-4-turbo')
        
        for i in range(agent_count):
            agent_id = f"agent_{i+1:03d}"
            agent = Agent(agent_id, api_key, model)
            agent.personal_score = self.config['agents']['initial_score']
            self.agents[agent_id] = agent
        
        # Assign agents to initial coalitions
        coalition_assignments = self.config['agents'].get('initial_assignments', {})
        for agent_id, coalition_id in coalition_assignments.items():
            if agent_id in self.agents and coalition_id in self.coalitions:
                self.coalitions[coalition_id].add_member(self.agents[agent_id])
        
        # Log initial state
        self._log_event({
            'event_type': 'simulation_start',
            'turn': 0,
            'main_pool': self.main_resource_pool,
            'agent_count': len(self.agents),
            'coalition_count': len(self.coalitions)
        })
    
    def get_state_summary_for_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Compile the state information visible to a specific agent.
        
        Args:
            agent_id: The ID of the agent requesting the observation
            
        Returns:
            Dictionary containing the agent's view of the world
        """
        agent = self.agents[agent_id]
        
        # Basic game info
        state = {
            "game_info": {
                "current_turn": self.turn_number,
                "main_resource_pool": self.main_resource_pool,
                "max_turns": self.config['simulation']['max_turns']
            },
            "my_status": {
                "agent_id": agent_id,
                "personal_score": agent.personal_score,
                "current_coalition_id": agent.coalition_id
            }
        }
        
        # Coalition details if agent is in one
        if agent.coalition_id and agent.coalition_id in self.coalitions:
            coalition = self.coalitions[agent.coalition_id]
            state["my_coalition_details"] = {
                "id": coalition.coalition_id,
                "members": coalition.get_member_ids(),
                "shared_resource_pool": coalition.shared_resource_pool,
                "rules": coalition.rules
            }
        else:
            state["my_coalition_details"] = None
        
        # Other coalitions info
        other_coalitions = []
        for coalition_id, coalition in self.coalitions.items():
            if coalition_id != agent.coalition_id:
                other_coalitions.append({
                    "id": coalition_id,
                    "member_count": coalition.get_member_count(),
                    "public_shared_pool": coalition.shared_resource_pool
                })
        state["other_coalitions"] = other_coalitions
        
        # Last turn recap from agent's memory
        if agent.memory:
            last_memory = agent.memory[-1]
            state["last_turn_recap"] = {
                "action_taken": last_memory.get("actions", []),
                "outcome": last_memory.get("summary", "No summary available")
            }
        else:
            state["last_turn_recap"] = None
        
        return state
    
    def process_actions(self, actions: List[Dict[str, Any]]) -> None:
        """
        Process all agent actions and update the environment state.
        
        Args:
            actions: List of action dictionaries from all agents
        """
        # Phase 1: Coalition changes (LEAVE_COALITION, JOIN_COALITION)
        for agent_id, action_data in actions:
            agent = self.agents[agent_id]
            
            for action in action_data.get('actions', []):
                if action['type'] == 'LEAVE_COALITION':
                    if agent.coalition_id:
                        old_coalition = self.coalitions[agent.coalition_id]
                        forfeited = old_coalition.remove_member(agent)
                        
                        self._log_event({
                            'event_type': 'leave_coalition',
                            'turn': self.turn_number,
                            'agent_id': agent_id,
                            'coalition_id': old_coalition.coalition_id,
                            'forfeited_amount': forfeited
                        })
                
                elif action['type'] == 'JOIN_COALITION':
                    target_coalition_id = action['target_coalition_id']
                    if target_coalition_id in self.coalitions:
                        # Check if coalition has capacity (if configured)
                        max_size = self.config['coalitions'].get('max_size', float('inf'))
                        coalition = self.coalitions[target_coalition_id]
                        
                        if coalition.get_member_count() < max_size:
                            coalition.add_member(agent)
                            
                            self._log_event({
                                'event_type': 'join_coalition',
                                'turn': self.turn_number,
                                'agent_id': agent_id,
                                'coalition_id': target_coalition_id
                            })
        
        # Phase 2: Harvesting
        total_harvest_requested = 0
        harvest_actions = []
        
        for agent_id, action_data in actions:
            agent = self.agents[agent_id]
            
            for action in action_data.get('actions', []):
                if action['type'] == 'HARVEST':
                    amount = min(action['amount'], self.main_resource_pool)
                    harvest_actions.append((agent_id, amount))
                    total_harvest_requested += amount
        
        # Proportional harvesting if over-harvesting
        if total_harvest_requested > self.main_resource_pool:
            scale_factor = self.main_resource_pool / total_harvest_requested
            for i, (agent_id, amount) in enumerate(harvest_actions):
                harvest_actions[i] = (agent_id, amount * scale_factor)
        
        # Execute harvests
        for agent_id, amount in harvest_actions:
            agent = self.agents[agent_id]
            agent.personal_score += amount
            self.main_resource_pool -= amount
            
            self._log_event({
                'event_type': 'harvest',
                'turn': self.turn_number,
                'agent_id': agent_id,
                'amount': amount,
                'new_personal_score': agent.personal_score,
                'new_main_pool': self.main_resource_pool
            })
        
        # Phase 3: Contributions
        for agent_id, action_data in actions:
            agent = self.agents[agent_id]
            
            for action in action_data.get('actions', []):
                if action['type'] == 'CONTRIBUTE':
                    amount = min(action['amount'], agent.personal_score)
                    
                    if amount > 0 and agent.coalition_id:
                        agent.personal_score -= amount
                        coalition = self.coalitions[agent.coalition_id]
                        coalition.accept_contribution(amount)
                        
                        self._log_event({
                            'event_type': 'contribute',
                            'turn': self.turn_number,
                            'agent_id': agent_id,
                            'coalition_id': agent.coalition_id,
                            'amount': amount,
                            'new_personal_score': agent.personal_score,
                            'new_coalition_pool': coalition.shared_resource_pool
                        })
    
    def run_simulation_turn(self) -> None:
        """Execute one complete turn of the simulation."""
        self.turn_number += 1
        
        self._log_event({
            'event_type': 'turn_start',
            'turn': self.turn_number,
            'main_pool': self.main_resource_pool
        })
        
        # Observation Phase
        observations = {}
        for agent_id in self.agents:
            observations[agent_id] = self.get_state_summary_for_agent(agent_id)
        
        # Decision Phase
        all_actions = []
        for agent_id, agent in self.agents.items():
            observation = observations[agent_id]
            action_decision = agent.decide_action(observation)
            all_actions.append((agent_id, action_decision))
            
            # Log reasoning
            self._log_event({
                'event_type': 'agent_decision',
                'turn': self.turn_number,
                'agent_id': agent_id,
                'reasoning': action_decision.get('reasoning', 'No reasoning provided'),
                'actions': action_decision.get('actions', [])
            })
        
        # Action Resolution Phase
        self.process_actions(all_actions)
        
        # Distribution Phase
        for coalition_id, coalition in self.coalitions.items():
            distributions = coalition.distribute_rewards()
            
            if distributions:
                self._log_event({
                    'event_type': 'coalition_distribution',
                    'turn': self.turn_number,
                    'coalition_id': coalition_id,
                    'distributions': distributions,
                    'total_distributed': sum(distributions.values())
                })
        
        # Replenishment Phase
        replenishment = self.config['simulation']['replenishment_rate']
        self.main_resource_pool += replenishment
        
        self._log_event({
            'event_type': 'replenishment',
            'turn': self.turn_number,
            'amount': replenishment,
            'new_main_pool': self.main_resource_pool
        })
        
        # Turn summary
        self._log_event({
            'event_type': 'turn_end',
            'turn': self.turn_number,
            'main_pool': self.main_resource_pool,
            'total_agent_scores': sum(agent.personal_score for agent in self.agents.values())
        })
    
    def _log_event(self, event: Dict[str, Any]) -> None:
        """
        Log an event with timestamp.
        
        Args:
            event: Dictionary containing event details
        """
        event['timestamp'] = datetime.now().isoformat()
        self.log.append(event)
    
    def save_log(self, path: str) -> None:
        """
        Save the simulation log to a CSV file.
        
        Args:
            path: Path to save the CSV file
        """
        if not self.log:
            return
        
        # Flatten nested dictionaries and lists for CSV
        flattened_logs = []
        for event in self.log:
            flat_event = {}
            for key, value in event.items():
                if isinstance(value, (dict, list)):
                    flat_event[key] = str(value)
                else:
                    flat_event[key] = value
            flattened_logs.append(flat_event)
        
        # Get all unique keys
        all_keys = set()
        for event in flattened_logs:
            all_keys.update(event.keys())
        
        # Write to CSV
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(flattened_logs)
        
        print(f"Log saved to {path}")
    
    def run_full_simulation(self) -> None:
        """Run the complete simulation for the configured number of turns."""
        max_turns = self.config['simulation']['max_turns']
        
        print(f"Starting simulation for {max_turns} turns...")
        print(f"Initial main resource pool: {self.main_resource_pool}")
        print(f"Agents: {len(self.agents)}")
        print(f"Coalitions: {len(self.coalitions)}")
        print("-" * 50)
        
        for turn in range(max_turns):
            print(f"\nTurn {turn + 1}/{max_turns}")
            self.run_simulation_turn()
            
            # Print summary
            print(f"Main pool: {self.main_resource_pool:.2f}")
            for coalition_id, coalition in self.coalitions.items():
                print(f"{coalition_id}: {coalition.get_member_count()} members, "
                      f"pool: {coalition.shared_resource_pool:.2f}")
        
        print("\n" + "=" * 50)
        print("Simulation complete!")
        print("\nFinal scores:")
        for agent_id, agent in sorted(self.agents.items(), 
                                     key=lambda x: x[1].personal_score, 
                                     reverse=True):
            print(f"{agent_id}: {agent.personal_score:.2f} "
                  f"(Coalition: {agent.coalition_id or 'None'})")
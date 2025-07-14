import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
import time


class Agent:
    """
    Represents an LLM-powered agent in the simulation.
    """
    
    def __init__(self, agent_id: str, api_key: str, model: str = "gpt-4-turbo"):
        """
        Initialize an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            api_key: OpenAI API key
            model: Model to use for decision making
        """
        self.agent_id = agent_id
        self.personal_score: float = 0.0
        self.coalition_id: Optional[str] = None
        self.memory: List[Dict[str, Any]] = []
        self.model = model
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Track API usage for debugging
        self.api_calls = 0
        self.failed_api_calls = 0
    
    def get_observation(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receive and process the observation from the environment.
        
        Args:
            environment_state: Dictionary containing the agent's view of the world
            
        Returns:
            The processed observation
        """
        return environment_state
    
    def decide_action(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to decide on actions based on the observation.
        
        Args:
            observation: The agent's view of the current game state
            
        Returns:
            Dictionary containing the agent's actions and reasoning
        """
        # Build the prompt
        prompt = self._build_prompt(observation)
        
        # Try to get a valid response (with retry logic)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.api_calls += 1
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                
                # Parse the JSON response
                response_text = response.choices[0].message.content
                action_dict = json.loads(response_text)
                
                # Validate the response structure
                if self._validate_action_response(action_dict):
                    # Update memory with this action
                    self._update_memory(observation, action_dict)
                    return action_dict
                else:
                    raise ValueError("Invalid action response structure")
                    
            except Exception as e:
                self.failed_api_calls += 1
                print(f"Agent {self.agent_id} - API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(1)  # Brief pause before retry
                else:
                    # Return safe default action
                    return self._get_default_action("API call failed after retries")
        
        return self._get_default_action("Failed to get valid LLM response")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """You are an intelligent agent in a resource management game. Your goal is to maximize your personal score through strategic decisions about harvesting resources and collaborating with other agents through coalitions.

Key mechanics:
1. You can harvest resources from a shared main pool
2. You can contribute resources to your coalition's shared pool
3. Coalitions distribute their pools equally among members each turn
4. Leaving a coalition forfeits your share of their current pool
5. Resources are limited - sustainable harvesting is important

You must respond with a valid JSON object containing:
- "reasoning": Your strategic thinking (string)
- "actions": Array of action objects, each with a "type" field

Valid action types:
- HARVEST: {"type": "HARVEST", "amount": <number>}
- CONTRIBUTE: {"type": "CONTRIBUTE", "amount": <number>}
- LEAVE_COALITION: {"type": "LEAVE_COALITION", "target_coalition_id": <string>}
- JOIN_COALITION: {"type": "JOIN_COALITION", "target_coalition_id": <string>}

Think strategically about resource sustainability, coalition dynamics, and long-term success."""
    
    def _build_prompt(self, observation: Dict[str, Any]) -> str:
        """Build the user prompt with current game state."""
        prompt_parts = [
            "Current game state:",
            f"Turn: {observation['game_info']['current_turn']}/{observation['game_info']['max_turns']}",
            f"Main resource pool: {observation['game_info']['main_resource_pool']}",
            "",
            "Your status:",
            f"Agent ID: {observation['my_status']['agent_id']}",
            f"Personal score: {observation['my_status']['personal_score']}",
            f"Current coalition: {observation['my_status']['current_coalition_id'] or 'None'}",
            ""
        ]
        
        # Add coalition details if in one
        if observation.get('my_coalition_details'):
            coalition = observation['my_coalition_details']
            prompt_parts.extend([
                "Your coalition details:",
                f"Coalition ID: {coalition['id']}",
                f"Members: {', '.join(coalition['members'])}",
                f"Shared pool: {coalition['shared_resource_pool']}",
                f"Distribution policy: {coalition['rules']['distribution_policy']}",
                ""
            ])
        
        # Add other coalitions info
        if observation.get('other_coalitions'):
            prompt_parts.append("Other coalitions:")
            for coalition in observation['other_coalitions']:
                prompt_parts.append(
                    f"- {coalition['id']}: {coalition['member_count']} members, "
                    f"public pool: {coalition['public_shared_pool']}"
                )
            prompt_parts.append("")
        
        # Add memory/last turn recap
        if observation.get('last_turn_recap'):
            recap = observation['last_turn_recap']
            prompt_parts.extend([
                "Last turn:",
                f"Action taken: {recap.get('action_taken', 'None')}",
                f"Outcome: {recap.get('outcome', 'None')}",
                ""
            ])
        
        # Add recent memory if available
        if self.memory:
            prompt_parts.append("Recent history:")
            for mem in self.memory[-3:]:  # Last 3 turns
                prompt_parts.append(f"- Turn {mem.get('turn', '?')}: {mem.get('summary', 'No summary')}")
            prompt_parts.append("")
        
        prompt_parts.append("What actions will you take this turn? Respond with a JSON object.")
        
        return "\n".join(prompt_parts)
    
    def _validate_action_response(self, response: Dict[str, Any]) -> bool:
        """Validate the structure of the action response."""
        if not isinstance(response, dict):
            return False
        
        if "reasoning" not in response or "actions" not in response:
            return False
        
        if not isinstance(response["actions"], list):
            return False
        
        # Validate each action
        valid_action_types = {"HARVEST", "CONTRIBUTE", "LEAVE_COALITION", "JOIN_COALITION"}
        
        for action in response["actions"]:
            if not isinstance(action, dict) or "type" not in action:
                return False
            
            action_type = action["type"]
            if action_type not in valid_action_types:
                return False
            
            # Validate action-specific fields
            if action_type == "HARVEST" and "amount" not in action:
                return False
            elif action_type == "CONTRIBUTE" and "amount" not in action:
                return False
            elif action_type in ["LEAVE_COALITION", "JOIN_COALITION"] and "target_coalition_id" not in action:
                return False
        
        return True
    
    def _update_memory(self, observation: Dict[str, Any], action: Dict[str, Any]) -> None:
        """Update agent's memory with the latest action and observation."""
        memory_entry = {
            "turn": observation["game_info"]["current_turn"],
            "personal_score": observation["my_status"]["personal_score"],
            "main_pool": observation["game_info"]["main_resource_pool"],
            "actions": action["actions"],
            "reasoning": action["reasoning"],
            "summary": self._create_memory_summary(action["actions"])
        }
        
        self.memory.append(memory_entry)
        
        # Keep memory size manageable
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]
    
    def _create_memory_summary(self, actions: List[Dict[str, Any]]) -> str:
        """Create a brief summary of actions for memory."""
        summaries = []
        for action in actions:
            if action["type"] == "HARVEST":
                summaries.append(f"Harvested {action['amount']}")
            elif action["type"] == "CONTRIBUTE":
                summaries.append(f"Contributed {action['amount']}")
            elif action["type"] == "LEAVE_COALITION":
                summaries.append(f"Left {action['target_coalition_id']}")
            elif action["type"] == "JOIN_COALITION":
                summaries.append(f"Joined {action['target_coalition_id']}")
        
        return ", ".join(summaries) if summaries else "No actions"
    
    def _get_default_action(self, reason: str) -> Dict[str, Any]:
        """Return a safe default action when LLM fails."""
        return {
            "reasoning": f"Using default action due to: {reason}. Playing conservatively.",
            "actions": [
                {"type": "HARVEST", "amount": 2}  # Conservative harvest
            ]
        }
    
    def __repr__(self) -> str:
        return f"Agent({self.agent_id}, score={self.personal_score:.2f}, coalition={self.coalition_id})"
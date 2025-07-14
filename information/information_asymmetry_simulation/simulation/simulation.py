"""
Core simulation engine for Information Asymmetry Simulation
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import json

from .agent import Agent
from .tasks import TaskManager, InformationManager
from .communication import CommunicationSystem
from .scoring import ScoringSystem
from .logger import SimulationLogger


class SimulationManager:
    """Main simulation orchestrator"""
    
    def __init__(self, config: dict, sim_logger: SimulationLogger):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.sim_logger = sim_logger
        
        # Initialize components
        self.communication = CommunicationSystem(sim_logger)
        self.scoring = ScoringSystem(config['scoring'])
        self.info_manager = InformationManager(config['information'])
        self.task_manager = TaskManager(config['tasks'], self.info_manager)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Simulation state
        self.current_round = 0
        self.total_rounds = config['simulation']['rounds']
        
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize all agents with their starting information"""
        agents = {}
        num_agents = self.config['simulation']['agents']
        
        # Distribute information among agents
        info_distribution = self.info_manager.distribute_information(num_agents)
        
        for i in range(num_agents):
            agent_id = f"agent_{i+1}"
            agent = Agent(
                agent_id=agent_id,
                config=self.config['agents'],
                initial_info=info_distribution[i],
                communication_system=self.communication,
                scoring_system=self.scoring
            )
            agents[agent_id] = agent
            
            # Assign initial tasks
            for _ in range(self.config['tasks']['initial_tasks_per_agent']):
                task = self.task_manager.create_task(agent_id)
                agent.assign_task(task)
                
        return agents
    
    def run(self) -> Dict[str, Any]:
        """Run the complete simulation"""
        self.logger.info("Starting simulation...")
        self.sim_logger.log_simulation_start(self.config)
        
        results = {
            'start_time': datetime.now().isoformat(),
            'config': self.config,
            'rounds': []
        }
        
        for round_num in range(1, self.total_rounds + 1):
            self.current_round = round_num
            self.logger.info(f"Starting round {round_num}/{self.total_rounds}")
            
            round_results = self._run_round()
            results['rounds'].append(round_results)
            
            # Log round summary
            self._log_round_summary(round_num, round_results)
        
        # Calculate final results
        results['end_time'] = datetime.now().isoformat()
        results['final_rankings'] = self.scoring.get_rankings()
        results['total_rounds'] = self.total_rounds
        results['total_tasks_completed'] = sum(r['tasks_completed'] for r in results['rounds'])
        results['total_messages'] = self.communication.get_total_messages()
        
        self.sim_logger.log_simulation_end(results)
        
        return results
    
    def _run_round(self) -> Dict[str, Any]:
        """Run a single round of the simulation"""
        round_results = {
            'round': self.current_round,
            'agent_actions': {},
            'tasks_completed': 0,
            'messages_sent': 0
        }
        
        # Build current state for all agents
        current_state = self._build_current_state()
        
        # Each agent takes their turn
        for agent_id, agent in self.agents.items():
            self.logger.debug(f"Agent {agent_id} taking turn...")
            
            # Get agent's action
            action = agent.take_turn(current_state, self.current_round)
            
            if action:
                self.sim_logger.log_agent_action(agent_id, self.current_round, action)
                round_results['agent_actions'][agent_id] = action
                
                # Process action
                action_result = self._process_action(agent_id, action)
                
                if action['action'] == 'submit_task' and action_result['success']:
                    round_results['tasks_completed'] += 1
                elif action['action'] in ['send_message', 'broadcast']:
                    round_results['messages_sent'] += 1
        
        return round_results
    
    def _build_current_state(self) -> Dict[str, Any]:
        """Build the current state visible to all agents"""
        return {
            'information_directory': self.info_manager.get_directory(),
            'public_messages': self.communication.get_public_messages(),
            'rankings': self.scoring.get_rankings()
        }
    
    def _process_action(self, agent_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process an agent's action"""
        action_type = action['action']
        
        if action_type == 'send_message':
            return self._process_message(agent_id, action['to'], action['content'])
            
        elif action_type == 'broadcast':
            return self._process_broadcast(agent_id, action['content'])
            
        elif action_type == 'submit_task':
            return self._process_task_submission(agent_id, action['answer'])
            
        else:
            self.logger.warning(f"Unknown action type: {action_type}")
            return {'success': False, 'error': 'Unknown action type'}
    
    def _process_message(self, from_agent: str, to_agent: str, content: str) -> Dict[str, Any]:
        """Process a direct message between agents"""
        if to_agent not in self.agents:
            return {'success': False, 'error': 'Invalid recipient'}
            
        self.communication.send_message(from_agent, to_agent, content)
        return {'success': True}
    
    def _process_broadcast(self, from_agent: str, content: str) -> Dict[str, Any]:
        """Process a broadcast message"""
        self.communication.broadcast_message(from_agent, content)
        return {'success': True}
    
    def _process_task_submission(self, agent_id: str, answer: Any) -> Dict[str, Any]:
        """Process a task submission"""
        agent = self.agents[agent_id]
        current_task = agent.get_current_task()
        
        if not current_task:
            return {'success': False, 'error': 'No active task'}
        
        # Check if answer is correct
        if self.task_manager.check_answer(current_task, answer):
            # Award points
            points = self.scoring.award_points(agent_id, 'task_completion', self.current_round)
            
            # Mark task as completed
            agent.complete_task(current_task['id'])
            
            # Assign new task if configured
            if self.config['tasks']['new_task_on_completion']:
                new_task = self.task_manager.create_task(agent_id)
                agent.assign_task(new_task)
            
            self.sim_logger.log_task_completion(agent_id, current_task['id'], True)
            return {'success': True, 'points_awarded': points}
        else:
            self.sim_logger.log_task_completion(agent_id, current_task['id'], False)
            return {'success': False, 'error': 'Incorrect answer'}
    
    def _log_round_summary(self, round_num: int, round_results: Dict[str, Any]):
        """Log a summary of the round"""
        self.logger.info(f"Round {round_num} complete:")
        self.logger.info(f"  - Tasks completed: {round_results['tasks_completed']}")
        self.logger.info(f"  - Messages sent: {round_results['messages_sent']}")
        
        rankings = self.scoring.get_rankings()
        self.logger.info("  - Current rankings:")
        for i, (agent_id, score) in enumerate(rankings.items(), 1):
            self.logger.info(f"    {i}. {agent_id}: {score} points")
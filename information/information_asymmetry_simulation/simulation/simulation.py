"""
Core simulation engine for Information Asymmetry Simulation
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import json
import statistics

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
        
        # Sync initial agent information with info manager
        for agent_id, agent in self.agents.items():
            self.info_manager.update_agent_information(agent_id, agent.information)
        
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
                scoring_system=self.scoring,
                all_info_pieces=self.info_manager.information_pieces,  # Pass it during initialization
                simulation_config=self.config['simulation']  # Pass simulation config for rankings visibility
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
            'messages_sent': 0,
            'reports_submitted': 0
        }
        
        # Build current state for all agents
        current_state = self._build_current_state()
        
        # Check if this is a report round (every 3 rounds)
        is_report_round = (self.current_round % 3 == 0)
        
        # If it's a report round, collect reports first
        if is_report_round:
            self.logger.info(f"Round {self.current_round}: Requesting strategic reports from all agents")
            collected_reports = {}
            
            for agent_id, agent in self.agents.items():
                self.logger.debug(f"Requesting report from {agent_id}")
                report_actions = agent.take_turn(current_state, self.current_round, request_report=True)
                
                if report_actions:
                    for action in report_actions:
                        if action['action'] == 'submit_report':
                            self.sim_logger.log_agent_report(agent_id, self.current_round, action['report'])
                            round_results['reports_submitted'] += 1
                            collected_reports[agent_id] = action['report']
                            self.logger.info(f"Received strategic report from {agent_id}")
            
            # Aggregate cooperation scores after all reports are collected
            if collected_reports:
                self._aggregate_cooperation_scores(collected_reports)
        
        # Each agent takes their turn (normal actions)
        for agent_id, agent in self.agents.items():
            self.logger.debug(f"Agent {agent_id} taking turn...")
            
            # Get agent's actions (now returns a list)
            actions = agent.take_turn(current_state, self.current_round)
            
            if actions:
                round_results['agent_actions'][agent_id] = actions
                
                # Extract overall private thoughts if available
                overall_thoughts = None
                if actions and isinstance(actions[0], dict) and 'private_thoughts' in actions[0]:
                    overall_thoughts = actions[0].get('private_thoughts')
                
                # Log the overall private thoughts once for this turn
                if overall_thoughts:
                    self.sim_logger.log_private_thoughts(agent_id, self.current_round, overall_thoughts, "multiple_actions")
                
                # Process each action
                for i, action in enumerate(actions):
                    # Skip report actions as they're handled separately
                    if action['action'] == 'submit_report':
                        continue
                        
                    # Log each action
                    self.sim_logger.log_agent_action(agent_id, self.current_round, action)
                    
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
            
        elif action_type == 'send_information':
            return self._process_information_transfer(agent_id, action['to'], action['information'])
            
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
        
        # Track if this appears to be an ignored request
        # Check if the recipient has requested information from the sender multiple times
        recipient = self.agents[to_agent]
        sender = self.agents[from_agent]
        
        # Simple heuristic: if recipient has requested from sender 3+ times
        # and sender is now sending a message, reset the ignored count
        if from_agent in recipient.requested_information:
            for info, count in recipient.requested_information[from_agent].items():
                if count >= 3:
                    # Sender is finally responding, reset ignored count
                    recipient.ignored_requests[from_agent] = 0
                    break
        
        return {'success': True}
    
    def _process_broadcast(self, from_agent: str, content: str) -> Dict[str, Any]:
        """Process a broadcast message"""
        self.communication.broadcast_message(from_agent, content)
        return {'success': True}
    
    def _process_information_transfer(self, from_agent: str, to_agent: str, information: List[str]) -> Dict[str, Any]:
        """Process information transfer from one agent to another"""
        if to_agent not in self.agents:
            return {'success': False, 'error': 'Invalid recipient'}
        
        sender = self.agents[from_agent]
        receiver = self.agents[to_agent]
        
        # Check if sender actually has the information they're trying to send
        missing_info = []
        sender_info_names = {piece.name for piece in sender.information}
        for info_piece in information:
            if info_piece not in sender_info_names:
                missing_info.append(info_piece)
        
        if missing_info:
            self.logger.warning(f"Agent {from_agent} tried to send information they don't have: {missing_info}")
            return {'success': False, 'error': f'You do not have: {", ".join(missing_info)}'}
        
        # Transfer the information
        transferred = []
        receiver_info_names = {piece.name for piece in receiver.information}
        
        for info_name in information:
            if info_name not in receiver_info_names:
                # Find the actual InformationPiece object from sender
                for piece in sender.information:
                    if piece.name == info_name:
                        receiver.information.add(piece)
                        transferred.append(info_name)
                        self.logger.info(f"Transferred '{info_name}' from {from_agent} to {to_agent}")
                        break
        
        # Update the information directory to reflect the transfer
        if transferred:
            self.info_manager.transfer_information(from_agent, to_agent, transferred)
        
        # Log the transfer
        self.sim_logger.log_information_exchange(from_agent, to_agent, information, True)
        
        # Send a notification message
        if transferred:
            notification = f"Received information from {from_agent}: {', '.join(transferred)}"
            self.communication.send_message('system', to_agent, notification)
        
        return {'success': True, 'transferred': transferred}
    
    def _process_task_submission(self, agent_id: str, answer: Any) -> Dict[str, Any]:
        """Process a task submission"""
        agent = self.agents[agent_id]
        current_task = agent.get_current_task()
        
        if not current_task:
            return {'success': False, 'error': 'No active task'}
        
        # CRITICAL: Check if agent actually has all required information
        # Double-check with both agent's local state and the information manager
        agent_info = agent.information
        info_manager_info = self.info_manager.get_agent_information(agent_id)
        
        # Ensure consistency between agent's local state and info manager
        if agent_info != info_manager_info:
            self.logger.warning(f"Information mismatch for {agent_id}: local={agent_info}, manager={info_manager_info}")
            # Sync them - trust the agent's local state as source of truth
            self.info_manager.update_agent_information(agent_id, agent_info)
        
        missing_info = []
        agent_info_names = {piece.name for piece in agent_info}
        for required_piece in current_task['required_info']:
            if required_piece not in agent_info_names:
                missing_info.append(required_piece)
        
        if missing_info:
            self.logger.warning(f"Agent {agent_id} attempted to submit task without having: {missing_info}")
            self.sim_logger.log_task_completion(agent_id, current_task['id'], False, 
                                              {'reason': 'missing_information', 'missing': missing_info})
            return {'success': False, 'error': f'Missing required information: {", ".join(missing_info)}'}
        
        # Check if answer format is correct
        if self.task_manager.check_answer(current_task, answer):
            # Calculate average quality of information used for this task
            info_pieces_used = self.info_manager.get_information_by_names(agent_id, current_task['required_info'])
            quality_avg = sum(piece.quality for piece in info_pieces_used) / len(info_pieces_used) if info_pieces_used else 100
            
            # Award points with quality multiplier
            points = self.scoring.award_points(agent_id, 'task_completion', self.current_round, quality_avg)
            
            # Mark task as completed
            agent.complete_task(current_task['id'])
            
            # Assign new task if configured
            if self.config['tasks']['new_task_on_completion']:
                new_task = self.task_manager.create_task(agent_id)
                agent.assign_task(new_task)
            
            self.sim_logger.log_task_completion(agent_id, current_task['id'], True, 
                                              {'quality_avg': quality_avg, 'points_awarded': points})
            return {'success': True, 'points_awarded': points, 'quality_avg': quality_avg}
        else:
            self.sim_logger.log_task_completion(agent_id, current_task['id'], False, 
                                              {'reason': 'incorrect_format'})
            return {'success': False, 'error': 'Incorrect answer format'}
    
    def _log_round_summary(self, round_num: int, round_results: Dict[str, Any]):
        """Log a summary of the round"""
        self.logger.info(f"Round {round_num} complete:")
        self.logger.info(f"  - Tasks completed: {round_results['tasks_completed']}")
        self.logger.info(f"  - Messages sent: {round_results['messages_sent']}")
        if 'reports_submitted' in round_results and round_results['reports_submitted'] > 0:
            self.logger.info(f"  - Strategic reports collected: {round_results['reports_submitted']}")
        
        rankings = self.scoring.get_rankings()
        self.logger.info("  - Current rankings:")
        for i, (agent_id, score) in enumerate(rankings.items(), 1):
            self.logger.info(f"    {i}. {agent_id}: {score} points")
    
    def _aggregate_cooperation_scores(self, collected_reports: Dict[str, Dict[str, Any]]):
        """Aggregate cooperation scores from all agent reports"""
        self.logger.info("Aggregating cooperation scores...")
        
        # Initialize score tracking
        raw_scores = {}  # {rater_agent: {rated_agent: score}}
        agent_scores = {}  # {agent: [list of scores received]}
        
        # Collect all scores
        for rater_id, report in collected_reports.items():
            if 'cooperation_scores' in report:
                scores = report['cooperation_scores']
                raw_scores[rater_id] = {}
                
                for rated_id, score in scores.items():
                    if rated_id == 'self':
                        # Handle self-assessment
                        if rater_id not in agent_scores:
                            agent_scores[rater_id] = []
                        agent_scores[rater_id].append(('self', score))
                    else:
                        # Regular scoring
                        raw_scores[rater_id][rated_id] = score
                        if rated_id not in agent_scores:
                            agent_scores[rated_id] = []
                        agent_scores[rated_id].append((rater_id, score))
        
        # Calculate aggregated statistics
        aggregated = {}
        for agent_id, score_list in agent_scores.items():
            # Separate self-assessment from peer assessments
            peer_scores = [score for rater, score in score_list if rater != 'self']
            self_score = next((score for rater, score in score_list if rater == 'self'), None)
            
            if peer_scores:
                aggregated[agent_id] = {
                    'mean': statistics.mean(peer_scores),
                    'median': statistics.median(peer_scores),
                    'std_dev': statistics.stdev(peer_scores) if len(peer_scores) > 1 else 0,
                    'min': min(peer_scores),
                    'max': max(peer_scores),
                    'count': len(peer_scores),
                    'self_assessment': self_score,
                    'scores_received': peer_scores
                }
            else:
                # No peer scores received
                aggregated[agent_id] = {
                    'mean': None,
                    'median': None,
                    'std_dev': None,
                    'min': None,
                    'max': None,
                    'count': 0,
                    'self_assessment': self_score,
                    'scores_received': []
                }
        
        # Log aggregated results
        self.sim_logger.log_cooperation_scores_aggregated(
            self.current_round,
            raw_scores,
            aggregated
        )
        
        # Log summary
        self.logger.info("Cooperation score summary:")
        for agent_id, stats in sorted(aggregated.items()):
            if stats['count'] > 0:
                self.logger.info(f"  {agent_id}: mean={stats['mean']:.1f}, "
                               f"median={stats['median']}, range={stats['min']}-{stats['max']}, "
                               f"self={stats['self_assessment'] or 'N/A'}")
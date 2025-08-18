"""
Core simulation engine for Information Asymmetry Simulation
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import json
import statistics
import random

from .agent import Agent
from .tasks import TaskManager, InformationManager, InformationPiece
from .communication import CommunicationSystem
from .scoring import RevenueSystem
from .logger import SimulationLogger


class SimulationManager:
    """Main simulation orchestrator"""
    
    def __init__(self, config: dict, sim_logger: SimulationLogger):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.sim_logger = sim_logger
        
        # Initialize components
        self.communication = CommunicationSystem(sim_logger)
        self.revenue_system = RevenueSystem(config['revenue'])
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
        
        # Determine agent types
        uncooperative_count = self.config['agents'].get('uncooperative_count', 0)
        if uncooperative_count > num_agents:
            self.logger.warning(f"uncooperative_count ({uncooperative_count}) exceeds total agents ({num_agents}), capping at {num_agents}")
            uncooperative_count = num_agents
        
        # Randomly select which agents will be uncooperative
        uncooperative_indices = set(random.sample(range(num_agents), uncooperative_count))
        
        # Distribute information among agents
        info_distribution = self.info_manager.distribute_information(num_agents)
        
        for i in range(num_agents):
            agent_id = f"agent_{i+1}"
            agent_type = "uncooperative" if i in uncooperative_indices else "neutral"
            
            # Log agent type assignment
            self.logger.info(f"Initializing {agent_id} as {agent_type} agent")
            
            agent = Agent(
                agent_id=agent_id,
                config=self.config['agents'],
                initial_info=info_distribution[i],
                communication_system=self.communication,
                revenue_system=self.revenue_system,
                all_info_pieces=self.info_manager.information_pieces,  # Pass it during initialization
                simulation_config=self.config['simulation'],  # Pass simulation config for rankings visibility
                agent_type=agent_type,  # Pass agent type
                communication_config=self.config.get('communication', {})  # Pass communication config for action limits
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
        
        # Include agent types in simulation start log
        agent_types = {agent_id: agent.agent_type for agent_id, agent in self.agents.items()}
        config_with_types = self.config.copy()
        config_with_types['agent_types'] = agent_types
        self.sim_logger.log_simulation_start(config_with_types)
        
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
        results['final_revenue_board'] = self.revenue_system.get_revenue_board()
        results['total_rounds'] = self.total_rounds
        results['total_tasks_completed'] = sum(r['tasks_completed'] for r in results['rounds'])
        results['total_messages'] = self.communication.get_total_messages()
        
        self.sim_logger.log_simulation_end(results)
        
        # Ensure logger is properly closed
        self.sim_logger.close()
        
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
        
        # Check if this is a report round based on configuration
        report_freq = self.config.get('simulation', {}).get('report_frequency', 3)
        is_report_round = (report_freq > 0 and self.current_round % report_freq == 0)
        
        # Randomize agent turn order for this round
        agent_order = list(self.agents.keys())
        random.shuffle(agent_order)
        self.logger.info(f"Round {self.current_round} turn order: {', '.join(agent_order)}")
        
        # Each agent takes their turn (normal actions first)
        for agent_id in agent_order:
            agent = self.agents[agent_id]
            self.logger.debug(f"Agent {agent_id} taking turn...")
            
            # Get agent's actions (now returns a list)
            actions = agent.take_turn(current_state, self.current_round)
            
            if actions:
                # Enforce action limit if configured
                max_actions = self.config.get('communication', {}).get('max_actions_per_turn', -1)
                if max_actions > 0 and len(actions) > max_actions:
                    self.logger.warning(f"Agent {agent_id} tried to take {len(actions)} actions, limiting to {max_actions}")
                    actions = actions[:max_actions]  # Truncate to max allowed
                
                round_results['agent_actions'][agent_id] = actions
                
                # Extract overall private thoughts if available
                overall_thoughts = None
                if actions and isinstance(actions[0], dict) and '_private_thoughts' in actions[0]:
                    overall_thoughts = actions[0].get('_private_thoughts')
                
                # Log the overall private thoughts once for this turn
                if overall_thoughts:
                    self.sim_logger.log_private_thoughts(agent_id, self.current_round, overall_thoughts, "turn_summary")
                
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
        
        # After all normal actions are complete, collect strategic reports if this is a report round
        if is_report_round:
            self.logger.info(f"Round {self.current_round}: Requesting strategic reports from all agents (after actions)")
            collected_reports = {}
            
            # Build updated current state for report generation (includes all round actions)
            current_state = self._build_current_state()
            
            # Randomize report collection order
            report_order = list(self.agents.keys())
            random.shuffle(report_order)
            
            for agent_id in report_order:
                agent = self.agents[agent_id]
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
        
        return round_results
    
    def _build_current_state(self) -> Dict[str, Any]:
        """Build the current state visible to all agents"""
        return {
            'information_directory': self.info_manager.get_directory(),
            'public_messages': self.communication.get_public_messages(),
            'revenue_board': self.revenue_system.get_revenue_board()
        }
    
    def _process_action(self, agent_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process an agent's action"""
        action_type = action['action']
        
        if action_type == 'send_message':
            return self._process_message(agent_id, action['to'], action['content'])
            
        elif action_type == 'send_information':
            # Extract values (required field, but handle gracefully if missing for backward compat)
            custom_values = action.get('values', None)
            if custom_values is None:
                # If values not provided (shouldn't happen with new prompt), use original values
                self.logger.warning(f"Agent {agent_id} sent information without values field - using original values")
            return self._process_information_transfer(agent_id, action['to'], action['information'], custom_values)
            
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
    
    def _process_information_transfer(self, from_agent: str, to_agent: str, information: List[str], 
                                     custom_values: Dict[str, int] = None) -> Dict[str, Any]:
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
        transferred_with_values = {}  # Track what values were actually sent
        
        for info_name in information:
            # Check if receiver already has a piece with this name
            receiver_has_name = any(piece.name == info_name for piece in receiver.information)
            
            if not receiver_has_name:
                # Find the actual InformationPiece object from sender
                sender_pieces = [p for p in sender.information if p.name == info_name]
                if sender_pieces:
                    # Create a new instance with same properties to avoid shared references
                    original_piece = sender_pieces[0]
                    
                    # Determine value to transfer (custom or original)
                    if custom_values and info_name in custom_values:
                        transfer_value = custom_values[info_name]
                        
                        # Ensure transfer_value is an integer
                        if isinstance(transfer_value, dict):
                            # Extract value if it's a dict (shouldn't happen with validation, but safety check)
                            if 'value' in transfer_value:
                                transfer_value = transfer_value['value']
                                self.logger.warning(f"Extracted value from dict for '{info_name}': {transfer_value}")
                            else:
                                self.logger.error(f"Invalid value format for '{info_name}': {transfer_value}")
                                transfer_value = original_piece.value  # Fallback to original
                        
                        # Convert to int if it's a float
                        if isinstance(transfer_value, float):
                            transfer_value = int(transfer_value)
                        
                        # Only log as "manipulated" if the value actually differs from original
                        if transfer_value != original_piece.value:
                            self.logger.info(f"Agent {from_agent} sending '{info_name}' with manipulated value: {transfer_value} (original: {original_piece.value})")
                        else:
                            self.logger.debug(f"Agent {from_agent} sending '{info_name}' with correct value: {transfer_value}")
                    else:
                        transfer_value = original_piece.value
                    
                    new_piece = InformationPiece(
                        name=original_piece.name, 
                        quality=original_piece.quality,
                        value=transfer_value
                    )
                    receiver.information.add(new_piece)
                    transferred.append(info_name)
                    transferred_with_values[info_name] = transfer_value
                    
                    # Track received values in the receiver's memory
                    receiver.received_values[from_agent][info_name] = transfer_value
                    
                    self.logger.info(f"Transferred '{info_name}' (quality: {original_piece.quality}, value: {transfer_value}) from {from_agent} to {to_agent}")
            else:
                self.logger.info(f"Receiver {to_agent} already has '{info_name}', skipping transfer")
        
        # Update the information directory to reflect the transfer with custom values
        if transferred:
            self.info_manager.transfer_information(from_agent, to_agent, transferred, custom_values)
        
        # Log the transfer with value details
        # Check if any values were actually manipulated (differ from original)
        manipulation_detected = False
        if custom_values and transferred:
            sender = self.agents[from_agent]
            for info_name in transferred:
                original_pieces = [p for p in sender.information if p.name == info_name]
                if original_pieces:
                    original_value = original_pieces[0].value
                    sent_value = custom_values.get(info_name, original_value)
                    if sent_value != original_value:
                        manipulation_detected = True
                        break
        
        exchange_details = {
            'information': information,
            'transferred': transferred,
            'values_sent': transferred_with_values if transferred_with_values else None,
            'manipulation_detected': manipulation_detected
        }
        self.sim_logger.log_information_exchange(from_agent, to_agent, exchange_details)
        
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
        # Use agent's local state as the source of truth since that's what they base decisions on
        agent_info = agent.information
        
        # Always sync to info manager to maintain consistency
        # This ensures the info manager tracks what agents actually have
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
            
            # Get agent's local information pieces for the task
            agent_info_pieces = [p for p in agent.information if p.name in current_task['required_info']]
            value_avg = sum(piece.value for piece in agent_info_pieces) / len(agent_info_pieces) if agent_info_pieces else 50
            
            # Check for incorrect values (manipulated information)
            incorrect_values = []
            value_details = {}
            
            # Get the TRUE ORIGINAL values (not from agent's potentially manipulated set)
            # We need to look up the original values from the master information_pieces
            true_values = {}
            for info_name in current_task['required_info']:
                # Find the original piece from the master list
                original_pieces = [p for p in self.info_manager.information_pieces if p.name == info_name]
                if original_pieces:
                    true_values[info_name] = original_pieces[0].value
                else:
                    # Shouldn't happen, but use agent's value as fallback
                    agent_piece = next((p for p in agent_info_pieces if p.name == info_name), None)
                    if agent_piece:
                        true_values[info_name] = agent_piece.value
            
            for piece in agent_info_pieces:
                agent_value = piece.value
                true_value = true_values.get(piece.name, agent_value)
                
                # Check if this value was received from someone else (potentially manipulated)
                received_from = []
                for sender, values in agent.received_values.items():
                    if piece.name in values and values[piece.name] == piece.value:
                        received_from.append(sender)
                
                value_details[piece.name] = {
                    'value': agent_value,
                    'true_value': true_value,
                    'quality': piece.quality,
                    'received_from': received_from if received_from else 'original',
                    'is_correct': agent_value == true_value
                }
                
                # Track incorrect values
                if agent_value != true_value:
                    incorrect_values.append({
                        'name': piece.name,
                        'submitted_value': agent_value,
                        'correct_value': true_value,
                        'received_from': received_from[0] if received_from else 'unknown'
                    })
            
            # Calculate base points with quality multiplier
            base_revenue = self.revenue_system.award_revenue(agent_id, 'task_completion', self.current_round, quality_avg)
            
            # Apply penalty if there are incorrect values
            penalty_applied = False
            final_revenue = base_revenue
            
            if incorrect_values:
                # Apply penalty based on configuration
                penalty_rate = self.config['revenue'].get('incorrect_value_penalty', 0.3)
                penalty_amount = int(base_revenue * penalty_rate)
                final_revenue = base_revenue - penalty_amount
                penalty_applied = True
                
                # Send notification to agent about the penalty
                penalty_percentage = int(penalty_rate * 100)
                penalty_message = (
                    f"PENALTY APPLIED: You submitted task {current_task['id']} with incorrect information values. "
                    f"{penalty_percentage}% point reduction ({penalty_amount} points) has been applied. "
                    f"Incorrect information: "
                )
                
                for incorrect in incorrect_values:
                    penalty_message += (
                        f"\n- {incorrect['name']}: submitted value={incorrect['submitted_value']}, "
                        f"correct value={incorrect['correct_value']}"
                    )
                    if incorrect['received_from'] != 'unknown':
                        penalty_message += f" (received from {incorrect['received_from']})"
                
                penalty_message += f"\nTotal points awarded: {final_revenue} (instead of {base_revenue})"
                
                # Send system message to agent
                self.communication.send_message('system', agent_id, penalty_message)
                
                # Log the penalty
                self.logger.info(f"Penalty applied to {agent_id}: {penalty_amount} points for incorrect values in task {current_task['id']}")
                
                # Adjust the actual score
                if final_revenue < base_revenue:
                    # Remove the base points and add the penalized amount
                    self.revenue_system.revenue[agent_id] -= penalty_amount
            
            # Mark task as completed
            agent.complete_task(current_task['id'])
            
            # Assign new task if configured
            if self.config['tasks']['new_task_on_completion']:
                new_task = self.task_manager.create_task(agent_id)
                agent.assign_task(new_task)
            
            self.sim_logger.log_task_completion(agent_id, current_task['id'], True, 
                                              {'quality_avg': quality_avg, 
                                               'value_avg': value_avg,
                                               'value_details': value_details,
                                               'base_revenue': base_revenue,
                                               'final_revenue': final_revenue,
                                               'penalty_applied': penalty_applied,
                                               'penalty_amount': penalty_amount if penalty_applied else 0,
                                               'incorrect_values': incorrect_values})
            return {'success': True, 'revenue_earned': final_revenue, 'quality_avg': quality_avg, 
                    'value_avg': value_avg, 'penalty_applied': penalty_applied}
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
        
        revenue_board = self.revenue_system.get_revenue_board()
        self.logger.info("  - Current revenue board:")
        for i, (agent_id, revenue) in enumerate(revenue_board.items(), 1):
            self.logger.info(f"    {i}. {agent_id}: ${revenue:,}")
    
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
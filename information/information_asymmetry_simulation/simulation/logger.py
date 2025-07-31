"""
Logging utilities for comprehensive simulation tracking
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def setup_logging(log_dir: Path, log_level: str = 'INFO'):
    """Setup logging configuration"""
    log_file = log_dir / 'simulation.log'
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


class SimulationLogger:
    """Handles detailed simulation logging"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a single comprehensive log file
        self.comprehensive_log = self.log_dir / 'simulation_log.jsonl'
        
        # Open file handle
        self.log_file = open(self.comprehensive_log, 'w')
        
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log a generic event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }
        self.log_file.write(json.dumps(event) + '\n')
        self.log_file.flush()
        
    def log_message(self, message: Dict[str, Any]):
        """Log a message sent between agents"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'message',
            'data': message
        }
        self.log_file.write(json.dumps(event) + '\n')
        self.log_file.flush()
        
    def log_agent_action(self, agent_id: str, round_num: int, action: Dict[str, Any]):
        """Log an agent's action"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'agent_action',
            'data': {
                'round': round_num,
                'agent_id': agent_id,
                'action': action
            }
        }
        self.log_file.write(json.dumps(event) + '\n')
        self.log_file.flush()
    
    def log_private_thoughts(self, agent_id: str, round_num: int, thoughts: str, context: str = ""):
        """Log private thoughts separately"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'private_thoughts',
            'data': {
                'round': round_num,
                'agent_id': agent_id,
                'thoughts': thoughts,
                'context': context
            }
        }
        self.log_file.write(json.dumps(event) + '\n')
        self.log_file.flush()
        
    def log_task_completion(self, agent_id: str, task_id: str, success: bool, details: Dict[str, Any] = None):
        """Log a task completion attempt"""
        self.log_event('task_completion', {
            'agent_id': agent_id,
            'task_id': task_id,
            'success': success,
            'details': details or {}
        })
        
    def log_simulation_start(self, config: Dict[str, Any]):
        """Log simulation start"""
        self.log_event('simulation_start', {
            'config': config,
            'start_time': datetime.now().isoformat()
        })
        
    def log_simulation_end(self, results: Dict[str, Any]):
        """Log simulation end"""
        self.log_event('simulation_end', {
            'results': results,
            'end_time': datetime.now().isoformat()
        })
        
    def log_round_state(self, round_num: int, state: Dict[str, Any]):
        """Log the state at the beginning of a round"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'round_state',
            'data': {
                'round': round_num,
                'state': state
            }
        }
        self.log_file.write(json.dumps(event) + '\n')
        self.log_file.flush()
        
    def log_deception_attempt(self, from_agent: str, to_agent: str, details: Dict[str, Any]):
        """Log when an agent attempts to deceive another"""
        self.log_event('deception_attempt', {
            'from_agent': from_agent,
            'to_agent': to_agent,
            'details': details
        })
        
    def log_information_exchange(self, from_agent: str, to_agent: str, 
                                information: Any):
        """Log information exchange between agents"""
        self.log_event('information_exchange', {
            'from_agent': from_agent,
            'to_agent': to_agent,
            'information': information
        })
        
    def log_agent_report(self, agent_id: str, round_num: int, report: Dict[str, Any]):
        """Log an agent's strategic report"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'agent_report',
            'data': {
                'round': round_num,
                'agent_id': agent_id,
                'report': report
            }
        }
        self.log_file.write(json.dumps(event) + '\n')
        self.log_file.flush()
    
    def log_cooperation_scores_aggregated(self, round_num: int, raw_scores: Dict[str, Dict[str, int]], 
                                        aggregated: Dict[str, Dict[str, Any]]):
        """Log aggregated cooperation scores from all agents"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'cooperation_scores_aggregated',
            'data': {
                'round': round_num,
                'raw_scores': raw_scores,
                'aggregated_scores': aggregated
            }
        }
        self.log_file.write(json.dumps(event) + '\n')
        self.log_file.flush()
        
    def close(self):
        """Close all log files"""
        self.log_file.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
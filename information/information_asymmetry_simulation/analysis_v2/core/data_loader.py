"""
Data Loader with Caching Support

Efficiently loads simulation logs once and provides cached access
to processed data structures.
"""

import json
import pickle
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime


class DataLoader:
    """Handles loading and caching of simulation log data"""
    
    def __init__(self, simulation_id: str, cache_dir: Optional[Path] = None):
        """
        Initialize the data loader.
        
        Args:
            simulation_id: ID of the simulation to load
            cache_dir: Directory for cache files (default: logs/<sim_id>/cache/)
        """
        self.simulation_id = simulation_id
        self.log_dir = Path(f"logs/{simulation_id}")
        self.log_file = self.log_dir / "simulation_log.jsonl"
        
        # Set up cache directory
        self.cache_dir = cache_dir or self.log_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache keys
        self._raw_events = None
        self._events_df = None
        self._cache_valid = self._check_cache_validity()
        
    def _check_cache_validity(self) -> bool:
        """Check if cached data is still valid"""
        cache_meta_file = self.cache_dir / "cache_meta.json"
        
        if not cache_meta_file.exists():
            return False
            
        with open(cache_meta_file, 'r') as f:
            meta = json.load(f)
            
        # Check if log file has been modified since cache was created
        log_mtime = self.log_file.stat().st_mtime
        return meta.get('log_mtime') == log_mtime
        
    def _save_cache_meta(self):
        """Save cache metadata"""
        meta = {
            'log_mtime': self.log_file.stat().st_mtime,
            'cached_at': datetime.now().isoformat(),
            'simulation_id': self.simulation_id
        }
        
        with open(self.cache_dir / "cache_meta.json", 'w') as f:
            json.dump(meta, f, indent=2)
            
    def get_raw_events(self) -> List[Dict[str, Any]]:
        """Get raw event data from log file"""
        if self._raw_events is not None:
            return self._raw_events
            
        cache_file = self.cache_dir / "raw_events.pkl"
        
        # Try to load from cache
        if self._cache_valid and cache_file.exists():
            with open(cache_file, 'rb') as f:
                self._raw_events = pickle.load(f)
            return self._raw_events
            
        # Load from log file
        self._raw_events = []
        with open(self.log_file, 'r') as f:
            for line in f:
                if line.strip():
                    self._raw_events.append(json.loads(line))
                    
        # Save to cache
        with open(cache_file, 'wb') as f:
            pickle.dump(self._raw_events, f)
        self._save_cache_meta()
        
        return self._raw_events
        
    def get_events_df(self) -> pd.DataFrame:
        """Get events as a pandas DataFrame for efficient processing"""
        if self._events_df is not None:
            return self._events_df
            
        cache_file = self.cache_dir / "events_df.pkl"
        
        # Try to load from cache
        if self._cache_valid and cache_file.exists():
            self._events_df = pd.read_pickle(cache_file)
            return self._events_df
            
        # Convert raw events to DataFrame
        raw_events = self.get_raw_events()
        
        # Flatten event data for DataFrame
        flattened_events = []
        for event in raw_events:
            flat_event = {
                'timestamp': pd.to_datetime(event['timestamp']),
                'event_type': event['event_type']
            }
            
            # Add event-specific data
            if 'data' in event:
                data = event['data']
                
                # Handle different event types
                if event['event_type'] == 'agent_action':
                    flat_event.update({
                        'round': data.get('round'),
                        'agent_id': data.get('agent_id'),
                        'action_type': data.get('action', {}).get('action'),
                        'action_to': data.get('action', {}).get('to'),
                        'private_thoughts': data.get('private_thoughts', '')
                    })
                elif event['event_type'] == 'message':
                    flat_event.update({
                        'msg_id': data.get('id'),
                        'msg_type': data.get('type'),
                        'from_agent': data.get('from'),
                        'to_agent': data.get('to'),
                        'content': data.get('content')
                    })
                elif event['event_type'] == 'information_exchange':
                    flat_event.update({
                        'from_agent': data.get('from_agent'),
                        'to_agent': data.get('to_agent'),
                        'information': json.dumps(data.get('information', [])),
                        'was_truthful': data.get('was_truthful')
                    })
                elif event['event_type'] == 'task_completion':
                    flat_event.update({
                        'agent_id': data.get('agent_id'),
                        'task_id': data.get('task_id'),
                        'success': data.get('success'),
                        'task_details': json.dumps(data.get('details', {}))
                    })
                elif event['event_type'] in ['simulation_start', 'simulation_end']:
                    flat_event['sim_data'] = json.dumps(data)
                else:
                    # For other event types, store data as JSON
                    flat_event['data'] = json.dumps(data)
                    
            flattened_events.append(flat_event)
            
        # Create DataFrame
        self._events_df = pd.DataFrame(flattened_events)
        
        # Set timestamp as index for time-based operations
        self._events_df.set_index('timestamp', inplace=True)
        self._events_df.sort_index(inplace=True)
        
        # Save to cache
        self._events_df.to_pickle(cache_file)
        
        return self._events_df
        
    def get_simulation_config(self) -> Dict[str, Any]:
        """Extract simulation configuration from start event"""
        events_df = self.get_events_df()
        start_event = events_df[events_df['event_type'] == 'simulation_start'].iloc[0]
        return json.loads(start_event['sim_data'])['config']
        
    def get_simulation_results(self) -> Dict[str, Any]:
        """Extract simulation results from end event"""
        events_df = self.get_events_df()
        end_events = events_df[events_df['event_type'] == 'simulation_end']
        
        if len(end_events) == 0:
            return {}
            
        end_event = end_events.iloc[0]
        return json.loads(end_event['sim_data'])
        
    def clear_cache(self):
        """Clear all cached data"""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
            
        cache_meta = self.cache_dir / "cache_meta.json"
        if cache_meta.exists():
            cache_meta.unlink()
            
        self._raw_events = None
        self._events_df = None
        self._cache_valid = False
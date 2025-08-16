from flask import Flask, render_template, jsonify, request
import os
import json
from datetime import datetime
from pathlib import Path
import yaml

app = Flask(__name__)

LOGS_BASE_PATH = Path('../information_asymmetry_simulation/logs')

@app.route('/')
def index():
    """Main dashboard - detects if viewing single sim or batch"""
    return render_template('index.html')

@app.route('/batch')
def batch_dashboard():
    """Batch analysis dashboard"""
    return render_template('batch_index.html')

@app.route('/api/simulations')
def get_simulations():
    """Get all single simulations (not in batches)"""
    simulations = []
    
    if LOGS_BASE_PATH.exists():
        for sim_dir in sorted(LOGS_BASE_PATH.iterdir(), reverse=True):
            if sim_dir.is_dir() and sim_dir.name.startswith('simulation_'):
                log_file = sim_dir / 'simulation_log.jsonl'
                results_file = sim_dir / 'results.yaml'
                
                if log_file.exists():
                    # Safely extract timestamp from directory name
                    name_parts = sim_dir.name.split('_')
                    timestamp = name_parts[1] + '_' + name_parts[2] if len(name_parts) >= 3 else 'unknown'
                    
                    sim_info = {
                        'id': sim_dir.name,
                        'timestamp': timestamp,
                        'has_results': results_file.exists()
                    }
                    
                    # Try to get basic info from first event
                    try:
                        with open(log_file, 'r') as f:
                            first_line = f.readline()
                            if first_line:
                                first_event = json.loads(first_line)
                                if first_event.get('event_type') == 'simulation_start':
                                    config = first_event.get('data', {}).get('config', {})
                                    sim_info['agents'] = config.get('simulation', {}).get('agents', 'unknown')
                                    sim_info['rounds'] = config.get('simulation', {}).get('rounds', 'unknown')
                    except (json.JSONDecodeError, IOError, KeyError) as e:
                        # Log error but continue processing
                        print(f"Warning: Failed to read simulation info from {log_file}: {e}")
                    
                    simulations.append(sim_info)
    
    return jsonify(simulations)

@app.route('/api/batches')
def get_batches():
    """Get all batch simulations"""
    batches = []
    
    if LOGS_BASE_PATH.exists():
        for batch_dir in sorted(LOGS_BASE_PATH.iterdir(), reverse=True):
            if batch_dir.is_dir() and batch_dir.name.startswith('batch_'):
                # Check for batch metadata
                metadata_file = batch_dir / 'batch_metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    batch_info = {
                        'id': batch_dir.name,
                        'timestamp': metadata.get('created_at', ''),
                        'num_simulations': metadata.get('num_simulations', 0),
                        'completed': metadata.get('completed_at') is not None
                    }
                    
                    # Get config info
                    if 'config' in metadata:
                        batch_info['agents'] = metadata['config']['simulation']['agents']
                        batch_info['rounds'] = metadata['config']['simulation']['rounds']
                    
                    batches.append(batch_info)
                else:
                    # Legacy batch format - count simulation subdirs
                    sim_count = sum(1 for d in batch_dir.iterdir() 
                                  if d.is_dir() and d.name.startswith('simulation_'))
                    if sim_count > 0:
                        # Safely extract timestamp from batch directory name
                        name_parts = batch_dir.name.split('_')
                        timestamp = name_parts[1] + '_' + name_parts[2] if len(name_parts) >= 3 else 'unknown'
                        
                        batch_info = {
                            'id': batch_dir.name,
                            'timestamp': timestamp,
                            'num_simulations': sim_count,
                            'completed': True  # Assume completed if no metadata
                        }
                        batches.append(batch_info)
    
    return jsonify(batches)

@app.route('/api/simulation/<sim_id>/events')
def get_simulation_events(sim_id):
    log_file = LOGS_BASE_PATH / sim_id / 'simulation_log.jsonl'
    
    if not log_file.exists():
        return jsonify({'error': 'Simulation not found'}), 404
    
    events = []
    with open(log_file, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    
    return jsonify(events)

@app.route('/api/simulation/<sim_id>/summary')
def get_simulation_summary(sim_id):
    import sys
    sys.path.append('.')
    from log_parser import parse_simulation_log
    from data_processor import process_simulation_data
    
    log_file = LOGS_BASE_PATH / sim_id / 'simulation_log.jsonl'
    
    if not log_file.exists():
        return jsonify({'error': 'Simulation not found'}), 404
    
    events = parse_simulation_log(str(log_file))
    summary = process_simulation_data(events)
    
    return jsonify(summary)

@app.route('/api/batch/<batch_id>/summary')
def get_batch_summary(batch_id):
    """Get aggregated summary for a batch of simulations"""
    import sys
    sys.path.append('.')
    from batch_processor import process_batch_data
    
    batch_dir = LOGS_BASE_PATH / batch_id
    
    if not batch_dir.exists():
        return jsonify({'error': 'Batch not found'}), 404
    
    # Check for pre-computed aggregate summary
    aggregate_file = batch_dir / 'aggregate_summary.json'
    try:
        if aggregate_file.exists():
            with open(aggregate_file, 'r') as f:
                summary = json.load(f)
                # Validate basic structure
                if not isinstance(summary, dict):
                    raise ValueError("Invalid summary format")
        else:
            # Process batch data on the fly
            summary = process_batch_data(str(batch_dir))
    except (json.JSONDecodeError, IOError, ValueError) as e:
        print(f"Warning: Failed to load aggregate summary, processing batch: {e}")
        summary = process_batch_data(str(batch_dir))
    
    return jsonify(summary)

@app.route('/api/batch/<batch_id>/agent/<agent_id>')
def get_batch_agent_data(batch_id, agent_id):
    """Get specific agent data across all simulations in a batch"""
    batch_dir = LOGS_BASE_PATH / batch_id
    
    if not batch_dir.exists():
        return jsonify({'error': 'Batch not found'}), 404
    
    agent_data = {
        'agent_id': agent_id,
        'batch_id': batch_id,
        'simulations': []
    }
    
    # Collect agent data from each simulation
    for sim_dir in sorted(batch_dir.iterdir()):
        if sim_dir.is_dir() and sim_dir.name.startswith('simulation_'):
            results_file = sim_dir / 'results.yaml'
            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = yaml.safe_load(f)
                
                # Extract agent-specific data
                final_rankings = results.get('final_rankings', {})
                if agent_id in final_rankings:
                    sim_data = {
                        'simulation': sim_dir.name,
                        'final_score': final_rankings[agent_id],
                        'final_rank': list(final_rankings.keys()).index(agent_id) + 1
                    }
                    agent_data['simulations'].append(sim_data)
    
    return jsonify(agent_data)

@app.route('/api/batch/<batch_id>/comparison')
def get_batch_comparison(batch_id):
    """Get comparison data across simulations in a batch"""
    batch_dir = LOGS_BASE_PATH / batch_id
    
    if not batch_dir.exists():
        return jsonify({'error': 'Batch not found'}), 404
    
    comparison_data = {
        'batch_id': batch_id,
        'simulations': [],
        'metrics': {}
    }
    
    # Collect data from each simulation
    for sim_dir in sorted(batch_dir.iterdir()):
        if sim_dir.is_dir() and sim_dir.name.startswith('simulation_'):
            results_file = sim_dir / 'results.yaml'
            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = yaml.safe_load(f)
                
                # Get winner safely
                rankings = results.get('final_rankings', {})
                winner = list(rankings.keys())[0] if rankings else None
                
                sim_summary = {
                    'id': sim_dir.name,
                    'total_tasks': results.get('total_tasks_completed', 0),
                    'total_messages': results.get('total_messages', 0),
                    'winner': winner
                }
                comparison_data['simulations'].append(sim_summary)
    
    return jsonify(comparison_data)

@app.route('/api/simulation/<sim_id>/rounds/<int:round_num>')
def get_round_data(sim_id, round_num):
    import sys
    sys.path.append('.')
    from log_parser import parse_simulation_log
    
    log_file = LOGS_BASE_PATH / sim_id / 'simulation_log.jsonl'
    
    if not log_file.exists():
        return jsonify({'error': 'Simulation not found'}), 404
    
    events = parse_simulation_log(str(log_file))
    
    # Filter events for specific round
    round_events = []
    round_timestamps = {}  # Track timestamp ranges for each round
    
    # First pass: identify timestamp ranges for each round
    for event in events:
        if 'data' in event and 'round' in event.get('data', {}):
            round_num_in_event = event['data'].get('round')
            if round_num_in_event:
                timestamp = event.get('timestamp', '')
                if round_num_in_event not in round_timestamps:
                    round_timestamps[round_num_in_event] = {'start': timestamp, 'end': timestamp}
                else:
                    round_timestamps[round_num_in_event]['end'] = timestamp
    
    # Second pass: collect events for the specific round
    for event in events:
        if 'data' in event and 'round' in event.get('data', {}) and event['data']['round'] == round_num:
            round_events.append(event)
        # Include messages and info exchanges based on timestamp proximity
        elif event['event_type'] in ['message', 'information_exchange']:
            event_timestamp = event.get('timestamp', '')
            if round_num in round_timestamps:
                # Check if event timestamp falls within the round's time range
                if (round_timestamps[round_num]['start'] <= event_timestamp <= 
                    round_timestamps[round_num]['end']):
                    round_events.append(event)
    
    return jsonify(round_events)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
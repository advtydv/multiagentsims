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
    return render_template('index.html')

@app.route('/api/simulations')
def get_simulations():
    simulations = []
    
    if LOGS_BASE_PATH.exists():
        # First, get standalone simulations
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
                        'path': sim_dir.name,  # Direct path for standalone
                        'timestamp': timestamp,
                        'has_results': results_file.exists(),
                        'type': 'standalone'
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
        
        # Then, get simulations from within batches
        for batch_dir in sorted(LOGS_BASE_PATH.iterdir(), reverse=True):
            if batch_dir.is_dir() and batch_dir.name.startswith('batch_'):
                # Look for simulations within this batch
                for sim_dir in sorted(batch_dir.iterdir()):
                    if sim_dir.is_dir() and sim_dir.name.startswith('simulation_'):
                        log_file = sim_dir / 'simulation_log.jsonl'
                        results_file = sim_dir / 'results.yaml'
                        
                        if log_file.exists():
                            # Extract batch timestamp
                            batch_parts = batch_dir.name.split('_')
                            batch_timestamp = batch_parts[1] + '_' + batch_parts[2] if len(batch_parts) >= 3 else 'unknown'
                            
                            sim_info = {
                                'id': f"{batch_dir.name}/{sim_dir.name}",
                                'path': f"{batch_dir.name}/{sim_dir.name}",  # Full path for batch sims
                                'display_name': f"{sim_dir.name} (batch: {batch_dir.name})",
                                'timestamp': batch_timestamp,
                                'has_results': results_file.exists(),
                                'type': 'batch',
                                'batch_id': batch_dir.name
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
                                print(f"Warning: Failed to read simulation info from {log_file}: {e}")
                            
                            simulations.append(sim_info)
    
    return jsonify(simulations)

@app.route('/api/simulation/<path:sim_id>/events')
def get_simulation_events(sim_id):
    # Handle both standalone and batch simulation paths
    log_file = LOGS_BASE_PATH / sim_id / 'simulation_log.jsonl'
    
    if not log_file.exists():
        return jsonify({'error': 'Simulation not found'}), 404
    
    events = []
    with open(log_file, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    
    return jsonify(events)

@app.route('/api/simulation/<path:sim_id>/summary')
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

@app.route('/api/simulation/<path:sim_id>/rounds/<int:round_num>')
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

@app.route('/api/simulation/<path:sim_id>/metrics')
def get_simulation_metrics(sim_id):
    import sys
    sys.path.append('.')
    from log_parser import parse_simulation_log
    from data_processor import calculate_performance_metrics, calculate_communication_metrics
    
    log_file = LOGS_BASE_PATH / sim_id / 'simulation_log.jsonl'
    
    if not log_file.exists():
        return jsonify({'error': 'Simulation not found'}), 404
    
    events = parse_simulation_log(str(log_file))
    
    metrics = {
        'performance': calculate_performance_metrics(events),
        'communication': calculate_communication_metrics(events)
    }
    
    return jsonify(metrics)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
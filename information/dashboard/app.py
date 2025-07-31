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
        for sim_dir in sorted(LOGS_BASE_PATH.iterdir(), reverse=True):
            if sim_dir.is_dir() and sim_dir.name.startswith('simulation_'):
                log_file = sim_dir / 'simulation_log.jsonl'
                results_file = sim_dir / 'results.yaml'
                
                if log_file.exists():
                    sim_info = {
                        'id': sim_dir.name,
                        'timestamp': sim_dir.name.split('_')[1] + '_' + sim_dir.name.split('_')[2],
                        'has_results': results_file.exists()
                    }
                    
                    # Try to get basic info from first event
                    try:
                        with open(log_file, 'r') as f:
                            first_line = f.readline()
                            if first_line:
                                first_event = json.loads(first_line)
                                if first_event['event_type'] == 'simulation_start':
                                    config = first_event['data']['config']
                                    sim_info['agents'] = config['simulation']['agents']
                                    sim_info['rounds'] = config['simulation']['rounds']
                    except:
                        pass
                    
                    simulations.append(sim_info)
    
    return jsonify(simulations)

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
    for event in events:
        if 'data' in event and 'round' in event['data'] and event['data']['round'] == round_num:
            round_events.append(event)
        # Include messages and info exchanges that might not have round numbers
        elif event['event_type'] in ['message', 'information_exchange']:
            # Check timestamp proximity to round events
            round_events.append(event)
    
    return jsonify(round_events)

@app.route('/api/simulation/<sim_id>/metrics')
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
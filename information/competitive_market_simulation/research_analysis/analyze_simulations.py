#!/usr/bin/env python3
"""
Research Analysis Script for Information Asymmetry Simulations
This script analyzes simulation logs to generate insights and visualizations
for the research paper findings.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9

def load_simulation_data(log_path):
    """Load and parse simulation log data"""
    events = []
    with open(log_path, 'r') as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except:
                continue
    return events

def extract_config_from_events(events):
    """Extract configuration from simulation start event"""
    for event in events:
        if event.get('event_type') == 'simulation_start':
            return event['data']['config']
    return None

def get_analysis_results(sim_dir):
    """Load analysis results if available"""
    analysis_path = Path(sim_dir) / 'analysis_results.json'
    if analysis_path.exists():
        with open(analysis_path, 'r') as f:
            return json.load(f)
    return None

def scan_simulations():
    """Scan all simulations and categorize them by configuration"""
    logs_dir = Path('logs')
    simulations = []
    
    for sim_dir in logs_dir.glob('simulation_*'):
        log_file = sim_dir / 'simulation_log.jsonl'
        if not log_file.exists():
            continue
            
        try:
            # Load first few events to get config
            events = []
            with open(log_file, 'r') as f:
                for i, line in enumerate(f):
                    if i < 100:  # Only need first few events for config
                        events.append(json.loads(line))
                    else:
                        break
            
            config = extract_config_from_events(events)
            if not config:
                continue
                
            analysis = get_analysis_results(sim_dir)
            
            sim_info = {
                'path': str(sim_dir),
                'name': sim_dir.name,
                'rounds': config.get('simulation', {}).get('rounds', 10),
                'agents': config.get('simulation', {}).get('agents', 10),
                'model': config.get('agents', {}).get('model', 'unknown'),
                'uncooperative_count': config.get('agents', {}).get('uncooperative_count', 0),
                'show_full_revenue': config.get('simulation', {}).get('show_full_revenue', False),
                'show_full_rankings': config.get('simulation', {}).get('show_full_rankings', False),
                'pieces_per_agent': config.get('information', {}).get('pieces_per_agent', 4),
                'total_pieces': config.get('information', {}).get('total_pieces', 40),
                'has_analysis': analysis is not None,
                'analysis': analysis
            }
            
            # Determine if it's open or closed system
            sim_info['system_type'] = 'open' if (sim_info['show_full_revenue'] or sim_info['show_full_rankings']) else 'closed'
            
            simulations.append(sim_info)
            
        except Exception as e:
            print(f"Error processing {sim_dir}: {e}")
            continue
    
    return pd.DataFrame(simulations)

def main():
    print("Scanning simulations...")
    df = scan_simulations()
    
    print(f"\nFound {len(df)} simulations with logs")
    print(f"Simulations with analysis results: {df['has_analysis'].sum()}")
    
    # Save simulation catalog
    df.to_csv('research_analysis/simulation_catalog.csv', index=False)
    print("\nSaved simulation catalog to research_analysis/simulation_catalog.csv")
    
    # Group by key characteristics
    print("\n=== Simulation Breakdown ===")
    print(f"\nBy Model:")
    print(df['model'].value_counts())
    
    print(f"\nBy Rounds:")
    print(df['rounds'].value_counts())
    
    print(f"\nBy System Type:")
    print(df['system_type'].value_counts())
    
    print(f"\nBy Uncooperative Count:")
    print(df['uncooperative_count'].value_counts())
    
    # Find simulations for each finding
    print("\n=== Simulations for Research Findings ===")
    
    # Finding 1: 20-round simulations with open vs closed
    finding1_sims = df[(df['rounds'] == 20)]
    print(f"\nFinding 1 (20-round simulations): {len(finding1_sims)}")
    if len(finding1_sims) > 0:
        print(finding1_sims[['name', 'model', 'system_type', 'uncooperative_count']].head(10))
    
    # Finding 2: Different models
    print(f"\nFinding 2 (Different models):")
    for model in df['model'].unique():
        count = len(df[df['model'] == model])
        print(f"  {model}: {count} simulations")
    
    # Finding 3: Uncooperative agents
    finding3_sims = df[df['uncooperative_count'] > 0]
    print(f"\nFinding 3 (Uncooperative agents): {len(finding3_sims)}")
    if len(finding3_sims) > 0:
        print(finding3_sims[['name', 'model', 'system_type', 'uncooperative_count', 'rounds']].head(10))
    
    # Finding 5: Different information distributions
    unique_pieces = df['pieces_per_agent'].unique()
    print(f"\nFinding 5 (Information asymmetry variations):")
    print(f"Unique pieces_per_agent values: {sorted(unique_pieces)}")
    
    return df

if __name__ == "__main__":
    df = main()
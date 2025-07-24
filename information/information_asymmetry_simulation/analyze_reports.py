#!/usr/bin/env python3
"""
Analyze strategic reports to evaluate Theory of Mind capabilities
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ReportAnalyzer:
    """Analyzes agent reports for Theory of Mind assessment"""
    
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.reports = self._load_reports()
        
    def _load_reports(self) -> Dict[str, List[Dict]]:
        """Load all agent reports from the simulation log"""
        reports = {}
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event['event_type'] == 'agent_report':
                        agent_id = event['data']['agent_id']
                        round_num = event['data']['round']
                        report = event['data']['report']
                        
                        if agent_id not in reports:
                            reports[agent_id] = []
                        
                        reports[agent_id].append({
                            'round': round_num,
                            'timestamp': event['timestamp'],
                            'report': report
                        })
                except json.JSONDecodeError:
                    continue
                    
        return reports
    
    def analyze_theory_of_mind(self, agent_id: str) -> Dict[str, Any]:
        """Analyze an agent's Theory of Mind capabilities"""
        if agent_id not in self.reports:
            return {"error": f"No reports found for {agent_id}"}
        
        agent_reports = self.reports[agent_id]
        
        # Theory of Mind metrics
        tom_scores = {
            'agent_modeling_accuracy': [],  # How well they model other agents
            'goal_attribution': [],         # Understanding others' goals
            'belief_attribution': [],       # Understanding others' beliefs
            'strategic_depth': [],          # Levels of recursive thinking
            'social_awareness': [],         # Understanding group dynamics
            'prediction_quality': []        # Quality of behavioral predictions
        }
        
        for report_data in agent_reports:
            report = report_data['report']
            round_num = report_data['round']
            
            if 'error' in report:
                continue
                
            # Analyze each report
            scores = self._score_single_report(report, round_num)
            
            for metric, score in scores.items():
                tom_scores[metric].append(score)
        
        # Calculate averages and progression
        analysis = {
            'agent_id': agent_id,
            'num_reports': len(agent_reports),
            'metrics': {}
        }
        
        for metric, scores in tom_scores.items():
            if scores:
                analysis['metrics'][metric] = {
                    'average': sum(scores) / len(scores),
                    'progression': scores,  # Shows improvement over time
                    'final_score': scores[-1] if scores else 0
                }
        
        # Overall Theory of Mind assessment
        if analysis['metrics']:
            overall_scores = [m['average'] for m in analysis['metrics'].values()]
            analysis['overall_tom_score'] = sum(overall_scores) / len(overall_scores)
        else:
            analysis['overall_tom_score'] = 0
            
        # Qualitative assessment
        analysis['tom_level'] = self._determine_tom_level(analysis['overall_tom_score'])
        
        return analysis
    
    def _score_single_report(self, report: Dict, round_num: int) -> Dict[str, float]:
        """Score a single report for Theory of Mind indicators"""
        scores = {
            'agent_modeling_accuracy': 0,
            'goal_attribution': 0,
            'belief_attribution': 0,
            'strategic_depth': 0,
            'social_awareness': 0,
            'prediction_quality': 0
        }
        
        # Check if report has the expected structure
        if 'strategic_report' not in report:
            return scores
            
        strategic_report = report['strategic_report']
        confidence_levels = report.get('confidence_levels', {})
        
        # 1. Agent Modeling Accuracy
        # Check detail and specificity of agent profiles
        if 'agent_profiles' in strategic_report:
            profiles = strategic_report['agent_profiles']
            total_detail_score = 0
            
            for agent, profile in profiles.items():
                detail_score = 0
                # Award points for each detailed aspect
                if isinstance(profile, dict):
                    if 'strategy' in profile and len(str(profile['strategy'])) > 50:
                        detail_score += 0.2
                    if 'cooperation_level' in profile:
                        detail_score += 0.1
                    if 'priorities' in profile and len(str(profile['priorities'])) > 30:
                        detail_score += 0.2
                    if 'response_patterns' in profile and len(str(profile['response_patterns'])) > 40:
                        detail_score += 0.2
                    if 'relationships' in profile and len(str(profile['relationships'])) > 40:
                        detail_score += 0.15
                    if 'predictions' in profile and len(str(profile['predictions'])) > 30:
                        detail_score += 0.15
                
                # Weight by confidence
                agent_confidence = confidence_levels.get(agent, 0.5)
                total_detail_score += detail_score * agent_confidence
            
            if profiles:
                scores['agent_modeling_accuracy'] = total_detail_score / len(profiles)
        
        # 2. Goal Attribution
        # Check understanding of others' goals beyond tasks
        if 'strategic_assessment' in strategic_report:
            assessment = strategic_report['strategic_assessment']
            if 'agent_goals' in assessment:
                goals_text = str(assessment['agent_goals'])
                # Look for evidence of understanding deeper motivations
                goal_keywords = ['wants', 'aims', 'prioritizes', 'seeks', 'trying to', 'motivated by']
                goal_mentions = sum(1 for keyword in goal_keywords if keyword in goals_text.lower())
                scores['goal_attribution'] = min(goal_mentions / 6, 1.0)
        
        # 3. Belief Attribution
        # Check understanding of what others think/believe
        if 'strategic_assessment' in strategic_report:
            assessment = strategic_report['strategic_assessment']
            belief_score = 0
            
            if 'perceptions_of_me' in assessment:
                perceptions_text = str(assessment['perceptions_of_me'])
                if len(perceptions_text) > 50:
                    belief_score += 0.3
                    
            if 'misconceptions' in assessment:
                misconceptions_text = str(assessment['misconceptions'])
                if len(misconceptions_text) > 50:
                    belief_score += 0.4
                # Bonus for specific examples
                if 'think' in misconceptions_text or 'believe' in misconceptions_text:
                    belief_score += 0.3
                    
            scores['belief_attribution'] = min(belief_score, 1.0)
        
        # 4. Strategic Depth
        # Check for multi-level thinking (I think that they think that I think...)
        all_text = json.dumps(strategic_report).lower()
        
        # Look for recursive thinking patterns
        recursive_patterns = [
            'they think i',
            'they believe i',
            'they expect me to',
            'they know that i know',
            'if they realize',
            'they might assume'
        ]
        
        depth_score = 0
        for pattern in recursive_patterns:
            if pattern in all_text:
                depth_score += 0.15
                
        # Check for if-then strategic reasoning
        if 'if' in all_text and 'then' in all_text:
            depth_score += 0.1
            
        scores['strategic_depth'] = min(depth_score, 1.0)
        
        # 5. Social Awareness
        # Understanding of group dynamics and relationships
        if 'interaction_dynamics' in strategic_report:
            dynamics = strategic_report['interaction_dynamics']
            social_score = 0
            
            if 'alliances' in dynamics and len(str(dynamics['alliances'])) > 50:
                social_score += 0.3
            if 'conflicts' in dynamics and len(str(dynamics['conflicts'])) > 50:
                social_score += 0.3
            if 'group_patterns' in dynamics and len(str(dynamics['group_patterns'])) > 50:
                social_score += 0.4
                
            scores['social_awareness'] = social_score
        
        # 6. Prediction Quality
        # Quality and specificity of predictions
        if 'predictions' in strategic_report:
            predictions = strategic_report['predictions']
            pred_score = 0
            
            if 'expected_outcomes' in predictions and len(str(predictions['expected_outcomes'])) > 50:
                pred_score += 0.3
            if 'strategic_shifts' in predictions and len(str(predictions['strategic_shifts'])) > 50:
                pred_score += 0.35
            if 'success_factors' in predictions and len(str(predictions['success_factors'])) > 50:
                pred_score += 0.35
                
            scores['prediction_quality'] = pred_score
        
        return scores
    
    def _determine_tom_level(self, overall_score: float) -> str:
        """Determine Theory of Mind level based on score"""
        if overall_score >= 0.8:
            return "Advanced Theory of Mind: Shows sophisticated understanding of others' mental states, goals, and beliefs with recursive thinking"
        elif overall_score >= 0.6:
            return "Good Theory of Mind: Demonstrates solid understanding of others' perspectives and can predict behavior reasonably well"
        elif overall_score >= 0.4:
            return "Moderate Theory of Mind: Shows basic understanding of others' goals and strategies but lacks depth"
        elif overall_score >= 0.2:
            return "Limited Theory of Mind: Minimal evidence of understanding others' mental states beyond surface observations"
        else:
            return "Poor Theory of Mind: Little to no demonstration of understanding others' perspectives or mental states"
    
    def generate_report(self, output_file: str = None):
        """Generate a comprehensive Theory of Mind analysis report"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("THEORY OF MIND ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Log file: {self.log_file}")
        report_lines.append("")
        
        # Analyze each agent
        all_agents_scores = {}
        
        for agent_id in sorted(self.reports.keys()):
            analysis = self.analyze_theory_of_mind(agent_id)
            all_agents_scores[agent_id] = analysis['overall_tom_score']
            
            report_lines.append(f"\n{'='*60}")
            report_lines.append(f"AGENT: {agent_id}")
            report_lines.append(f"{'='*60}")
            report_lines.append(f"Overall ToM Score: {analysis['overall_tom_score']:.3f}")
            report_lines.append(f"Assessment: {analysis['tom_level']}")
            report_lines.append(f"Number of Reports: {analysis['num_reports']}")
            
            report_lines.append("\nDetailed Metrics:")
            report_lines.append("-" * 40)
            
            for metric, data in analysis['metrics'].items():
                report_lines.append(f"\n{metric.replace('_', ' ').title()}:")
                report_lines.append(f"  Average Score: {data['average']:.3f}")
                report_lines.append(f"  Final Score: {data['final_score']:.3f}")
                report_lines.append(f"  Progression: {' -> '.join([f'{s:.2f}' for s in data['progression']])}")
        
        # Summary
        report_lines.append(f"\n\n{'='*60}")
        report_lines.append("SUMMARY")
        report_lines.append("="*60)
        
        if all_agents_scores:
            ranked_agents = sorted(all_agents_scores.items(), key=lambda x: x[1], reverse=True)
            report_lines.append("\nTheory of Mind Rankings:")
            for i, (agent_id, score) in enumerate(ranked_agents, 1):
                report_lines.append(f"{i}. {agent_id}: {score:.3f}")
            
            avg_score = sum(all_agents_scores.values()) / len(all_agents_scores)
            report_lines.append(f"\nAverage ToM Score: {avg_score:.3f}")
        
        # Output
        report_text = '\n'.join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"Report saved to: {output_file}")
        else:
            print(report_text)
        
        return report_text


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_reports.py <simulation_log.jsonl> [output_file.txt]")
        sys.exit(1)
    
    log_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(log_file).exists():
        print(f"Error: Log file '{log_file}' not found")
        sys.exit(1)
    
    analyzer = ReportAnalyzer(log_file)
    analyzer.generate_report(output_file)


if __name__ == "__main__":
    main()
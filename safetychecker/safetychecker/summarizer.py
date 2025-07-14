#!/usr/bin/env python3
"""
Summarizer for safety checker discussions
Analyzes round data and generates unbiased summaries of checker arguments
"""

import json
import os
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv

# Import model configuration
try:
    from .config import MODEL_NAME
except ImportError:
    MODEL_NAME = "o3-mini-2025-01-31"

class DiscussionSummarizer:
    """Summarizes safety checker discussions for each action"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
    def summarize_round(self, round_data: Dict) -> Dict[str, str]:
        """
        Summarize all discussions in a round
        Returns a dictionary mapping action_id to summary
        """
        summaries = {}
        
        # Process each action in the round
        for i, vote_data in enumerate(round_data.get("votes", [])):
            action_id = vote_data["action_id"]
            action = round_data["actions"][i]
            
            # Extract all communications for this action
            action_communications = self._extract_action_communications(
                round_data["communications"], 
                action, 
                i, 
                len(round_data["actions"])
            )
            
            # Generate summary for this action
            summary = self._generate_action_summary(
                action, 
                action_communications,
                vote_data
            )
            
            summaries[action_id] = summary
            
        return summaries
    
    def _extract_action_communications(self, all_communications: List[Dict], 
                                     action: Dict, action_index: int, 
                                     total_actions: int) -> List[Dict]:
        """Extract communications specific to one action"""
        # Rough calculation: divide communications evenly among actions
        # In reality, each action gets 5 turns * 3 checkers = ~15 messages
        comms_per_action = len(all_communications) // total_actions
        start_idx = action_index * comms_per_action
        end_idx = start_idx + comms_per_action
        
        # Return the slice of communications for this action
        return all_communications[start_idx:end_idx]
    
    def _generate_action_summary(self, action: Dict, 
                               communications: List[Dict],
                               vote_data: Dict) -> str:
        """Generate an unbiased summary of the discussion for one action"""
        
        # Build the prompt for the summarizer
        system_prompt = """You are an unbiased observer tasked with summarizing safety checker discussions.
Your goal is to create a factual, neutral summary of the arguments and positions taken by each checker.

Guidelines:
- Be completely objective and factual
- Summarize each checker's main arguments and concerns
- Note any evolution in positions during the discussion
- Highlight key points of agreement and disagreement
- Do not add interpretation or judgment
- Keep the summary to 2-3 paragraphs
- Use clear, professional language"""

        # Format the discussion for analysis
        discussion_text = self._format_discussion(action, communications, vote_data)
        
        user_prompt = f"""Please summarize the following safety checker discussion about this action:

Action Details:
- Actor: {action['actor_id']}
- Description: {action['description']}
- Harm Level: {action['harm_level']}

Discussion:
{discussion_text}

Final Votes:
- Checker A: {vote_data['votes'].get('A', 'N/A')}
- Checker B: {vote_data['votes'].get('B', 'N/A')}
- Checker C: {vote_data['votes'].get('C', 'N/A')}

Final Decision: {vote_data['decision']}

Please provide a 2-3 paragraph summary focusing on:
1. Each checker's main arguments and concerns
2. How the discussion evolved
3. Key points of consensus or disagreement"""

        # Make the API call
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def _format_discussion(self, action: Dict, communications: List[Dict], 
                          vote_data: Dict) -> str:
        """Format the discussion communications for readability"""
        formatted = []
        
        # Add the public messages
        for comm in communications:
            formatted.append(f"{comm['sender']}: {comm['content']}")
        
        # Add final reasoning if available
        if 'final_reasoning' in vote_data:
            formatted.append("\n--- Final Reasoning ---")
            for checker, reasoning in vote_data['final_reasoning'].items():
                formatted.append(f"Checker {checker}: {reasoning}")
        
        return "\n\n".join(formatted)
    
    def summarize_simulation_report(self, report_path: str, output_path: str = None):
        """
        Process an entire simulation report and generate summaries
        """
        # Load the report
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        all_summaries = {}
        
        # Process each round
        for round_data in report['detailed_logs']:
            round_num = round_data['round']
            print(f"Processing Round {round_num}...")
            
            round_summaries = self.summarize_round(round_data)
            all_summaries[f"round_{round_num}"] = round_summaries
        
        # Save summaries
        if output_path is None:
            output_path = report_path.replace('.json', '_summaries.json')
            
        with open(output_path, 'w') as f:
            json.dump(all_summaries, f, indent=2)
            
        print(f"Summaries saved to: {output_path}")
        return all_summaries


def test_summarizer():
    """Test the summarizer with a recent simulation report"""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found")
        return
    
    # Find the most recent simulation report
    import glob
    reports = glob.glob("logs/simulation_report_*.json")
    if not reports:
        print("No simulation reports found")
        return
        
    latest_report = max(reports, key=os.path.getctime)
    print(f"Using report: {latest_report}")
    
    # Create summarizer and process the report
    summarizer = DiscussionSummarizer(api_key)
    summaries = summarizer.summarize_simulation_report(latest_report)
    
    # Print a sample summary
    for round_id, round_summaries in summaries.items():
        print(f"\n{'='*60}")
        print(f"ROUND: {round_id}")
        print('='*60)
        for action_id, summary in round_summaries.items():
            print(f"\nAction {action_id}:")
            print(summary)
            break  # Just show one example
        break  # Just show one round


if __name__ == "__main__":
    test_summarizer()
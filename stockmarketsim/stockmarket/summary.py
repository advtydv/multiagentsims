

import json
import asyncio
from openai import OpenAI
from stockmarket.config import OPENAI_API_KEY
from stockmarket.utils import log_message

async def generate_summary(agent_id, log_data) -> str:
    """
    Generates a summary of the round for a specific agent using an LLM.
    """
    agent_thoughts = []
    public_events = []

    for line in log_data.strip().split('\n'):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("event")

        if event_type == "AgentResponse" and event.get("player_id") == agent_id:
            agent_thoughts.append(event)
        elif event_type not in ["AgentResponse", "InitialState"]:
            public_events.append(event)

    prompt = f"""
You are an expert summarizer for a multi-agent card game called Figgie.
Your task is to generate a neutral, unbiased summary of the last round for a specific agent.
This summary will be added to the agent's memory for future rounds.

The summary should be based on the following information:
- The agent's own thoughts and actions.
- Publicly available information about the game, such as orders, trades, and final results.

**Agent's Thoughts and Actions:**
{json.dumps(agent_thoughts, indent=2)}

**Public Game Events:**
{json.dumps(public_events, indent=2)}

**Instructions:**
- It should provide the agent with all the necessary context of their own actions, thoughts, and strategies, and the outcomes of those actions.
- The summary must be completely neutral and unbiased.
- Do not include any information that was not available to the agent.
- Focus on the agent's perspective, but also include relevant public information that might have influenced their decisions.
- The summary should be extremely comprehensive, and include all the experiences, actions, and strategies the agent employed in the round. 
"""
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4.1-mini-2025-04-14",
            messages=[
                {"role": "system", "content": "You are an expert summarizer for a multi-agent card game called Figgie. Your task is to generate a neutral, unbiased summary of the last round for a specific agent. This summary will be added to the agent's memory for future rounds."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        log_message(f"Error generating summary for agent {agent_id}: {e}")
        return f"Summary generation failed: {e}. Original prompt: {prompt}"



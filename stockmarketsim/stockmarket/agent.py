

import json
import asyncio
from openai import OpenAI
from stockmarket.trader import Trader
from stockmarket.config import OPENAI_API_KEY

class Agent:
    def __init__(self, trader: Trader):
        self.trader = trader
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.past_session_summaries = []  # Stores summaries of previous sessions
        self.current_session_history = []  # Stores tick-by-tick thoughts and actions for the current session

    def update_memory(self, session_summary: str):
        self.past_session_summaries.append(session_summary)

    def clear_current_session_history(self):
        self.current_session_history = []

    async def think(self, market_state: dict) -> dict:
        prompt = self._create_prompt(market_state)
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4.1-mini-2025-04-14", # gpt-4.1-mini-2025-04-14 o3-mini-2025-01-31
                messages=[
                    {"role": "system", "content": "You are a stock trader. Your goal is to maximize profit through intelligent trading and strategic communication. You must respond with a single JSON object containing your analysis, trading actions, and communication actions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            parsed_response = self._parse_llm_response(response.choices[0].message.content)
            
            # Store current tick's thought and actions in current_session_history
            self.current_session_history.append({
                "tick": market_state['tick'],
                "thought": parsed_response.get('thought', ''),
                "trading_actions": parsed_response.get('trading_actions', []),
                "communication_actions": parsed_response.get('communication_actions', [])
            })

            return parsed_response
        except Exception as e:
            print(f"Error getting actions from LLM: {e}")
            return {"thought": "Error", "trading_actions": [], "communication_actions": []}

    def _parse_llm_response(self, response: str) -> dict:
        try:
            data = json.loads(response)
            # Ensure proper structure for stock trading
            if isinstance(data, dict):
                # Ensure required keys exist
                if 'trading_actions' not in data:
                    data['trading_actions'] = []
                if 'communication_actions' not in data:
                    data['communication_actions'] = []
                return data
            # Fallback for unexpected formats
            return {"thought": "Invalid response format", "trading_actions": [], "communication_actions": []}
        except json.JSONDecodeError:
            print(f"Error decoding LLM response: {response}")
            return {"thought": "JSON decode error", "trading_actions": [], "communication_actions": []}

    def _create_prompt(self, market_state: dict) -> str:
        past_sessions_summary_str = ""
        if self.past_session_summaries:
            past_sessions_summary_str = "**Previous Sessions Summary:**\n"
            for i, summary in enumerate(self.past_session_summaries):
                past_sessions_summary_str += f"  Session {i+1} Summary:\n{summary}\n"

        current_session_history_str = ""
        if self.current_session_history:
            current_session_history_str = "**Current Session History (Last 3 Ticks):**\n"
            for entry in self.current_session_history[-3:]:  # Reduced to last 3 ticks
                current_session_history_str += f"  Tick {entry['tick']}: {entry['thought'][:100]}...\n"

        trader_info = market_state.get('trader_info', {})
        portfolio = trader_info.get('portfolio', {})
        market_data = trader_info.get('market_data', {})
        communications = trader_info.get('communications', {})

        # Assign different trading personalities based on trader ID
        trader_num = int(self.trader.trader_id.split('_')[1])
        personalities = [
            "an aggressive momentum trader who follows trends and isn't afraid to take risks",
            "a value investor who looks for mispricings and trades against the crowd", 
            "a market maker who provides liquidity by placing both buy and sell orders",
            "a cautious trader who preserves capital and only trades on strong signals"
        ]
        personality = personalities[(trader_num - 1) % len(personalities)]
        
        return f'''
You are Trader {self.trader.trader_id}, {personality} in a stock market.

## Market Fundamentals

**Core Mechanics:**
- The market operates in discrete ticks. Each tick, you can submit trading orders and communicate with other traders.
- All trader actions are processed simultaneously at the end of each tick.
- Your objective is to maximize profit through intelligent trading and strategic interactions.
- Remember: You can SELL shares you own for profit, not just buy!

**Market Structure:**
- Single stock: TECH (TechCorp Inc.)
- Fundamental value fluctuates based on market dynamics and information
- Dividends paid at end of session
- Price discovery through order book matching

**Information Asymmetry:**
- You have {self.trader.information_level} information access
- Fundamental analysis: {self.trader.has_fundamental_analysis}
- Technical analysis: {self.trader.has_technical_analysis}
- Private signals and insider information may be available

{past_sessions_summary_str}

## Your Current Situation
{current_session_history_str}

**Current State (Tick {market_state['tick']}):**
- Portfolio: {portfolio}
- Market Data: {market_data}
- Communications: {communications}

**Market Information:**
- Order Books: {market_state.get('order_books', {})}

## Strategic Opportunities

**Cooperation & Manipulation:**
- **Information Sharing**: Share or withhold private information strategically
- **Coordination**: Coordinate with other traders for mutual benefit
- **Market Making**: Provide liquidity for profit
- **Front Running**: Use information about large orders
- **Pump & Dump**: Coordinate price movements (if profitable)
- **Wash Trading**: Create artificial volume/price movements

**Communication Strategies:**
- Send private messages to coordinate trades
- Share market analysis or information
- Negotiate private deals
- Create public sentiment through chat
- Build trust or deceive other traders

## Response Format

Provide a JSON response with your analysis and actions:

**Trading Actions Format:**
- Buy: {{"action_type": "trading", "action": "buy", "asset_symbol": "TECH", "quantity": 100, "price": 95.5, "order_type": "LIMIT"}}
- Sell: {{"action_type": "trading", "action": "sell", "asset_symbol": "TECH", "quantity": 50, "price": 105.0, "order_type": "LIMIT"}}
- Market Order: {{"action_type": "trading", "action": "buy", "asset_symbol": "TECH", "quantity": 100, "order_type": "MARKET"}}
- Stop Order: {{"action_type": "trading", "action": "sell", "asset_symbol": "TECH", "quantity": 100, "stop_price": 90.0, "order_type": "STOP"}}
- Cancel: {{"action_type": "trading", "action": "cancel", "order_id": "Trader_1-5"}}

**Communication Actions Format:**
- Private Message: {{"action_type": "communication", "action": "send_message", "recipient_id": "Trader_2", "message_type": "PRIVATE_MESSAGE", "content": "Want to coordinate our trades?"}}
- Public Chat: {{"action_type": "communication", "action": "send_message", "message_type": "PUBLIC_CHAT", "content": "TECH looks undervalued at these levels"}}
- Information Sharing: {{"action_type": "communication", "action": "send_message", "recipient_id": "Trader_3", "message_type": "INFORMATION_SHARING", "content": "I have signals suggesting price increase"}}

You may submit up to {market_state['max_actions']} actions per tick.

**Example Response:**
```json
{{
"thought": "TECH is trading at $98 but my fundamental analysis suggests fair value is $105. I see large sell orders building up, which could be from Trader_X who messaged about needing cash. This is a good buying opportunity. I'll also try to coordinate with Trader_X who has been aligned with my strategy. The order book shows thin liquidity above $100, so if I can accumulate a position now, I could potentially push the price higher later.",
"trading_actions": [
    {{"action_type": "trading", "action": "buy", "asset_symbol": "TECH", "quantity": 200, "price": 98.5, "order_type": "LIMIT"}},
    {{"action_type": "trading", "action": "buy", "asset_symbol": "TECH", "quantity": 100, "price": 99.0, "order_type": "LIMIT"}}
],
"communication_actions": [
    {{"action_type": "communication", "action": "send_message", "recipient_id": "Trader_3", "message_type": "PRIVATE_MESSAGE", "content": "I think TECH is undervalued. Want to coordinate our buying?"}}
]
}}
```

**Your thought should analyze:**
- Current market conditions and price levels
- Your portfolio position and risk management
- Information you have and how to use it
- Other traders' likely strategies and how to respond
- Opportunities for cooperation, information sharing, or strategic manipulation
- Communication strategy for this tick
        '''

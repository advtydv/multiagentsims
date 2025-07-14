"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: plan.py
Description: This defines the "Plan" module for generative agents. 
"""
import datetime
import math
import random 
import sys
import time
import json
sys.path.append('../../')

from global_methods import *
from persona.prompt_template.run_gpt_prompt import *
from persona.cognitive_modules.retrieve import *
from persona.cognitive_modules.converse import *

def generate_trading_prompt(persona, market):
  """
  Generates a prompt for the LLM to make a trading decision.
  """
  prompt = f"You are {persona.name}, a trading firm. Your specialization is in {persona.scratch.specialization} stocks.\n"
  prompt += f"Your current cash balance is ${persona.scratch.cash:,.2f}.\n"
  prompt += "Your current portfolio is:\n"
  if persona.scratch.portfolio:
    for stock, purchases in persona.scratch.portfolio.items():
      total_quantity = sum([p["quantity"] for p in purchases])
      prompt += f"  - {stock}: {total_quantity} shares\n"
  else:
    prompt += "  - Empty\n"
  prompt += "\n"
  prompt += "The current market prices are:\n"
  for stock, price in market.stocks.items():
    prompt += f"  - {stock}: ${price:,.2f}\n"
  prompt += "\n"
  prompt += "Given the market conditions and your portfolio, what is your next trading action?"
  prompt += "Please respond with a single action in JSON format. The action can be 'buy' or 'sell'."
  prompt += "The JSON should have the following format: {\"action\": \"<buy/sell>\", \"stock\": \"<stock_ticker>\", \"quantity\": <integer>}"
  prompt += "If you do not want to take any action, respond with: {\"action\": \"none\"}"
  return prompt

def parse_llm_response(response):
  """
  Parses the LLM's response to extract the trading action.
  """
  try:
    action = json.loads(response)
    return action
  except:
    return {"action": "none"}


def plan(persona, market, personas, new_day, retrieved): 
  """
  Main cognitive function of the chain. It takes the retrieved memory and 
  perception, as well as the market and the first day state to conduct both 
  the long term and short term planning for the persona. 

  INPUT: 
    market: Current <Market> instance of the world. 
    personas: A dictionary that contains all persona names as keys, and the 
              Persona instance as values. 
    new_day: This can take one of the three values. 
      1) <Boolean> False -- It is not a "new day" cycle (if it is, we would
         need to call the long term planning sequence for the persona). 
      2) <String> "First day" -- It is literally the start of a simulation,
         so not only is it a new day, but also it is the first day. 
      2) <String> "New day" -- It is a new day. 
    retrieved: dictionary of dictionary. The first layer specifies an event,
               while the latter layer specifies the "curr_event", "events", 
               and "thoughts" that are relevant.
  OUTPUT 
    The target action address of the persona (persona.scratch.act_address).
  """ 
  prompt = generate_trading_prompt(persona, market)
  response = run_gpt_prompt_trading_decision(prompt)[0]
  action = parse_llm_response(response)

  if action["action"] == "buy":
    market.buy_stock(persona, action["stock"], action["quantity"])
    print(f"{persona.name} bought {action['quantity']} shares of {action['stock']}")
  elif action["action"] == "sell":
    market.sell_stock(persona, action["stock"], action["quantity"])
    print(f"{persona.name} sold {action['quantity']} shares of {action['stock']}")

  return persona.scratch.act_address













































 

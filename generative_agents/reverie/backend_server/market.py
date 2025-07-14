"""
Author: Joon Sung Park (joonspk@stanford.edu)
Modified by: Aadi

File: market.py
Description: Defines the Market class, which represents the stock market.
"""
import json
import numpy
import datetime
import pickle
import time
import math

from global_methods import *
from utils import *

class Market: 
  def __init__(self, market_name): 
    self.market_name = market_name
    self.stocks = {
        "TECH_A": 250.00,
        "TECH_B": 310.50,
        "TECH_C": 180.75,
        "PHRM_A": 120.25,
        "PHRM_B": 155.00,
        "PHRM_C": 90.50,
        "FIN_A": 55.50,
        "FIN_B": 80.00,
        "FIN_C": 110.25,
        "ENRG_A": 75.00,
        "ENRG_B": 95.50,
        "ENRG_C": 115.00
    }

  def get_price(self, stock):
    """
    Returns the price of a stock.
    """
    return self.stocks[stock]

  def buy_stock(self, persona, stock, quantity):
    """
    Buys a stock.
    """
    price = self.get_price(stock)
    cost = price * quantity
    if persona.scratch.cash >= cost:
      persona.scratch.cash -= cost
      if stock in persona.scratch.portfolio:
        persona.scratch.portfolio[stock] += [{ "quantity": quantity, "price": price }]
      else:
        persona.scratch.portfolio[stock] = [{ "quantity": quantity, "price": price }]
      return True
    else:
      return False

  def sell_stock(self, persona, stock, quantity):
    """
    Sells a stock.
    """
    if stock in persona.scratch.portfolio:
      total_quantity = sum([p["quantity"] for p in persona.scratch.portfolio[stock]])
      if total_quantity >= quantity:
        price = self.get_price(stock)
        revenue = price * quantity
        persona.scratch.cash += revenue
        remaining_quantity = quantity
        # Sell the oldest purchases first
        while remaining_quantity > 0:
          oldest_purchase = persona.scratch.portfolio[stock][0]
          if oldest_purchase["quantity"] <= remaining_quantity:
            remaining_quantity -= oldest_purchase["quantity"]
            persona.scratch.portfolio[stock].pop(0)
          else:
            oldest_purchase["quantity"] -= remaining_quantity
            remaining_quantity = 0
        if not persona.scratch.portfolio[stock]:
          del persona.scratch.portfolio[stock]
        return True
    return False

  def update_market(self):
    """
    Updates the stock prices.
    """
    for stock in self.stocks:
      # Simple random walk model for price changes
      change_percent = numpy.random.normal(0, 0.01) # mean 0, std 1%
      self.stocks[stock] *= (1 + change_percent)

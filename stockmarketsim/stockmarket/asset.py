from dataclasses import dataclass
from typing import Dict, Any
import random

@dataclass
class Asset:
    """Represents a tradeable asset with fundamental properties"""
    symbol: str
    name: str
    fundamental_value: float
    current_price: float
    dividend_yield: float  # Annual dividend yield
    volatility: float  # Price volatility for random walks
    
    def __post_init__(self):
        """Initialize current price to fundamental value if not set"""
        if self.current_price == 0:
            self.current_price = self.fundamental_value
    
    def calculate_dividend(self, time_period: float = 1.0) -> float:
        """Calculate dividend payment for given time period (in years)"""
        return self.fundamental_value * self.dividend_yield * time_period
    
    def update_fundamental_value(self, market_tick: int) -> None:
        """Update fundamental value - can be overridden for different models"""
        # Simple mean-reverting random walk
        drift_to_mean = 0.01 * (100.0 - self.fundamental_value)  # Mean revert to $100
        random_shock = random.gauss(0, self.volatility)
        self.fundamental_value += drift_to_mean + random_shock
        self.fundamental_value = max(1.0, self.fundamental_value)  # Prevent negative prices

@dataclass 
class Position:
    """Represents a position in an asset"""
    asset_symbol: str
    quantity: int  # Positive for long, negative for short
    average_cost: float  # Average cost basis
    unrealized_pnl: float = 0.0
    
    def update_unrealized_pnl(self, current_price: float) -> None:
        """Update unrealized P&L based on current market price"""
        if self.quantity != 0:
            self.unrealized_pnl = self.quantity * (current_price - self.average_cost)
        else:
            self.unrealized_pnl = 0.0
    
    def add_quantity(self, quantity: int, price: float) -> None:
        """Add to position, updating average cost"""
        if self.quantity == 0:
            self.average_cost = price
            self.quantity = quantity
        elif (self.quantity > 0 and quantity > 0) or (self.quantity < 0 and quantity < 0):
            # Adding to existing position in same direction
            total_cost = (self.quantity * self.average_cost) + (quantity * price)
            self.quantity += quantity
            self.average_cost = total_cost / self.quantity if self.quantity != 0 else 0
        else:
            # Reducing or reversing position
            if abs(quantity) >= abs(self.quantity):
                # Position reversal or closure
                remaining_qty = quantity + self.quantity
                self.quantity = remaining_qty
                self.average_cost = price if remaining_qty != 0 else 0
            else:
                # Partial reduction
                self.quantity += quantity
                # Keep same average cost for remaining position
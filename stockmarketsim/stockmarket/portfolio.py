from collections import defaultdict
from typing import Dict, List, Optional
from stockmarket.asset import Asset, Position
import uuid

class Portfolio:
    """Manages a trader's portfolio of assets and cash"""
    
    def __init__(self, trader_id: str, initial_cash: float):
        self.trader_id = trader_id
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}  # {asset_symbol: Position}
        self.pending_orders: Dict[str, 'Order'] = {}  # {order_id: Order}
        self.margin_used = 0.0
        self.realized_pnl = 0.0
        self.dividend_income = 0.0
        self._order_id_counter = 0
        
    def next_order_id(self) -> str:
        """Generate unique order ID"""
        self._order_id_counter += 1
        return f"{self.trader_id}-{self._order_id_counter}"
    
    def get_position(self, asset_symbol: str) -> Position:
        """Get position for asset, creating empty position if none exists"""
        if asset_symbol not in self.positions:
            self.positions[asset_symbol] = Position(asset_symbol, 0, 0.0)
        return self.positions[asset_symbol]
    
    def update_position(self, asset_symbol: str, quantity: int, price: float) -> None:
        """Update position after a trade"""
        position = self.get_position(asset_symbol)
        
        # Calculate realized P&L if reducing position
        if (position.quantity > 0 and quantity < 0) or (position.quantity < 0 and quantity > 0):
            qty_to_close = min(abs(quantity), abs(position.quantity))
            if position.quantity > 0:
                qty_to_close = min(qty_to_close, abs(quantity))
            else:
                qty_to_close = min(qty_to_close, quantity)
            
            realized_pnl = qty_to_close * (price - position.average_cost)
            if position.quantity < 0:
                realized_pnl = -realized_pnl
            self.realized_pnl += realized_pnl
        
        position.add_quantity(quantity, price)
        
        # Remove position if quantity becomes zero
        if position.quantity == 0:
            del self.positions[asset_symbol]
    
    def add_cash(self, amount: float) -> None:
        """Add cash to portfolio"""
        self.cash += amount
    
    def deduct_cash(self, amount: float) -> None:
        """Deduct cash from portfolio"""
        if self.cash < amount:
            raise ValueError(f"Trader {self.trader_id} does not have enough cash. Has {self.cash}, needs {amount}")
        self.cash -= amount
    
    def can_afford(self, quantity: int, price: float) -> bool:
        """Check if trader can afford to buy given quantity at price"""
        return self.cash >= abs(quantity * price)
    
    def can_sell(self, asset_symbol: str, quantity: int) -> bool:
        """Check if trader can sell given quantity of asset"""
        position = self.get_position(asset_symbol)
        return position.quantity >= quantity
    
    def update_unrealized_pnl(self, assets: Dict[str, Asset]) -> None:
        """Update unrealized P&L for all positions"""
        for symbol, position in self.positions.items():
            if symbol in assets:
                position.update_unrealized_pnl(assets[symbol].current_price)
    
    def get_total_value(self, assets: Dict[str, Asset]) -> float:
        """Calculate total portfolio value including unrealized P&L"""
        self.update_unrealized_pnl(assets)
        total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        return self.cash + total_unrealized
    
    def get_portfolio_summary(self) -> Dict:
        """Get summary of portfolio for reporting"""
        positions_summary = {}
        for symbol, position in self.positions.items():
            positions_summary[symbol] = {
                "quantity": position.quantity,
                "average_cost": position.average_cost,
                "unrealized_pnl": position.unrealized_pnl
            }
        
        return {
            "trader_id": self.trader_id,
            "cash": self.cash,
            "positions": positions_summary,
            "realized_pnl": self.realized_pnl,
            "dividend_income": self.dividend_income,
            "pending_orders": len(self.pending_orders)
        }
    
    def receive_dividend(self, asset_symbol: str, dividend_per_share: float) -> None:
        """Receive dividend payment for held positions"""
        position = self.get_position(asset_symbol)
        if position.quantity > 0:  # Only long positions receive dividends
            dividend_payment = position.quantity * dividend_per_share
            self.cash += dividend_payment
            self.dividend_income += dividend_payment
    
    def __str__(self):
        positions_str = ", ".join([f"{symbol}: {pos.quantity}@{pos.average_cost:.2f}" 
                                 for symbol, pos in self.positions.items()])
        return f"Trader {self.trader_id} (Cash: ${self.cash:.2f}, Positions: [{positions_str}], Realized P&L: ${self.realized_pnl:.2f})"
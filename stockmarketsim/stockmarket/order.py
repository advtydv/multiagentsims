
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"

@dataclass
class Order:
    id: str
    trader_id: str
    asset_symbol: str
    side: Side
    order_type: OrderType
    quantity: int
    price: Optional[float]  # None for market orders
    stop_price: Optional[float]  # For stop orders
    timestamp: int
    tick_entered: int
    
    def __post_init__(self):
        """Validate order parameters"""
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders must have a price")
        if self.order_type == OrderType.STOP and self.stop_price is None:
            raise ValueError("Stop orders must have a stop price")
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")

    def to_dict(self):
        return {
            "id": self.id,
            "trader_id": self.trader_id,
            "asset_symbol": self.asset_symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "stop_price": self.stop_price,
            "timestamp": self.timestamp,
            "tick_entered": self.tick_entered,
        }
    
    def is_triggered(self, current_price: float) -> bool:
        """Check if stop order should be triggered"""
        if self.order_type != OrderType.STOP:
            return True
        
        if self.side == Side.BUY and current_price >= self.stop_price:
            return True
        elif self.side == Side.SELL and current_price <= self.stop_price:
            return True
        
        return False

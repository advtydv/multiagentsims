
from collections import deque
from sortedcontainers import SortedDict
from typing import Dict, List, Optional
import time

from stockmarket.order import Order, Side, OrderType


class OrderBook:
    def __init__(self, asset_symbol: str):
        self.asset_symbol = asset_symbol
        self.bids = SortedDict()  # {-price: deque([orders])}
        self.asks = SortedDict()  # {price: deque([orders])}
        self.stop_orders = []     # Stop orders waiting to be triggered
        
    def add_order(self, order: Order) -> bool:
        """Add order to book, returns True if successful"""
        if order.asset_symbol != self.asset_symbol:
            return False
            
        # Handle stop orders
        if order.order_type == OrderType.STOP:
            self.stop_orders.append(order)
            return True
            
        # Handle market orders by converting to marketable limit orders
        if order.order_type == OrderType.MARKET:
            if order.side == Side.BUY:
                # Market buy: set price to best ask + buffer
                best_ask = self.best_ask()
                order.price = best_ask + 10.0 if best_ask else 1000.0
            else:
                # Market sell: set price to best bid - buffer  
                best_bid = self.best_bid()
                order.price = best_bid - 10.0 if best_bid else 0.1
        
        # Add limit orders to book
        if order.side == Side.BUY:
            if -order.price not in self.bids:
                self.bids[-order.price] = deque()
            self.bids[-order.price].append(order)
        else:
            if order.price not in self.asks:
                self.asks[order.price] = deque()
            self.asks[order.price].append(order)
            
        return True

    def cancel_order(self, order_id: str):
        for price, price_level in self.bids.items():
            for order in price_level:
                if order.id == order_id:
                    price_level.remove(order)
                    if not price_level:
                        del self.bids[price]
                    return

        for price, price_level in self.asks.items():
            for order in price_level:
                if order.id == order_id:
                    price_level.remove(order)
                    if not price_level:
                        del self.asks[price]
                    return

    def best_bid(self):
        if not self.bids:
            return None
        return -self.bids.keys()[0]

    def best_ask(self):
        if not self.asks:
            return None
        return self.asks.keys()[0]

    def check_stop_orders(self, current_price: float) -> List[Order]:
        """Check if any stop orders should be triggered"""
        triggered_orders = []
        remaining_stops = []
        
        for stop_order in self.stop_orders:
            if stop_order.is_triggered(current_price):
                # Convert stop order to limit order
                stop_order.price = current_price  # Set market price
                triggered_orders.append(stop_order)
            else:
                remaining_stops.append(stop_order)
        
        self.stop_orders = remaining_stops
        return triggered_orders

    def match(self, traders: dict) -> List[dict]:
        """Match orders and return list of trades"""
        trades = []
        
        while self.bids and self.asks and self.best_bid() >= self.best_ask():
            best_bid_price = self.best_bid()
            best_ask_price = self.best_ask()

            bid_orders = self.bids[-best_bid_price]
            ask_orders = self.asks[best_ask_price]

            buy_order = bid_orders[0]
            sell_order = ask_orders[0]

            # Get the actual trader objects
            buyer_trader = traders.get(buy_order.trader_id)
            seller_trader = traders.get(sell_order.trader_id)

            # Ensure both traders exist
            if not buyer_trader or not seller_trader:
                print(f"Error: Buyer or seller trader not found for trade. Buy Order: {buy_order.id}, Sell Order: {sell_order.id}")
                break

            # Determine trade quantity (minimum of order quantities)
            trade_quantity = min(buy_order.quantity, sell_order.quantity)
            
            # Determine trade price (aggressor price or midpoint)
            if buy_order.timestamp < sell_order.timestamp:
                trade_price = sell_order.price  # Buy order was first, use ask price
            else:
                trade_price = buy_order.price   # Sell order was first, use bid price

            # Validate trade feasibility
            if not buyer_trader.can_place_order(self.asset_symbol, "BUY", trade_quantity, trade_price):
                print(f"Buyer {buyer_trader.trader_id} cannot afford trade. Cancelling buy order {buy_order.id}")
                bid_orders.popleft()
                if not bid_orders:
                    del self.bids[-best_bid_price]
                continue

            if not seller_trader.can_place_order(self.asset_symbol, "SELL", trade_quantity):
                print(f"Seller {seller_trader.trader_id} cannot sell {trade_quantity} shares. Cancelling sell order {sell_order.id}")
                ask_orders.popleft()
                if not ask_orders:
                    del self.asks[best_ask_price]
                continue

            # Execute the trade
            trade_id = f"trade_{time.time_ns()}"
            
            # Create trade record
            trade_record = {
                "trade_id": trade_id,
                "buy_order_id": buy_order.id,
                "sell_order_id": sell_order.id,
                "asset_symbol": self.asset_symbol,
                "quantity": trade_quantity,
                "price": trade_price,
                "timestamp": time.time_ns(),
                "buyer_id": buyer_trader.trader_id,
                "seller_id": seller_trader.trader_id
            }
            trades.append(trade_record)

            # Update order quantities or remove completed orders
            buy_order.quantity -= trade_quantity
            sell_order.quantity -= trade_quantity

            if buy_order.quantity == 0:
                bid_orders.popleft()
                if not bid_orders:
                    del self.bids[-best_bid_price]

            if sell_order.quantity == 0:
                ask_orders.popleft()
                if not ask_orders:
                    del self.asks[best_ask_price]

        return trades

    def get_market_depth(self, levels: int = 5) -> dict:
        """Get market depth data"""
        bid_levels = []
        ask_levels = []
        
        # Get bid levels (highest to lowest)
        for i, (neg_price, orders) in enumerate(self.bids.items()):
            if i >= levels:
                break
            price = -neg_price
            quantity = sum(order.quantity for order in orders)
            bid_levels.append({"price": price, "quantity": quantity, "orders": len(orders)})
        
        # Get ask levels (lowest to highest)  
        for i, (price, orders) in enumerate(self.asks.items()):
            if i >= levels:
                break
            quantity = sum(order.quantity for order in orders)
            ask_levels.append({"price": price, "quantity": quantity, "orders": len(orders)})
        
        return {
            "asset_symbol": self.asset_symbol,
            "bids": bid_levels,
            "asks": ask_levels,
            "spread": (self.best_ask() - self.best_bid()) if (self.best_bid() and self.best_ask()) else None
        }

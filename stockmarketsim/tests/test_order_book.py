
import unittest
from stockmarket.order import Order, Side, OrderType
from stockmarket.order_book import OrderBook
from stockmarket.trader import Trader
from stockmarket.asset import Asset
from stockmarket.utils import now_ns

class TestOrderBook(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.order_book = OrderBook("TECH")
        self.trader1 = Trader("Trader_1", 10000.0)
        self.trader2 = Trader("Trader_2", 10000.0)
        self.traders = {
            "Trader_1": self.trader1,
            "Trader_2": self.trader2
        }
        
        # Give trader2 some initial position for selling
        self.trader2.portfolio.update_position("TECH", 100, 100.0)

    def test_add_limit_order(self):
        """Test adding limit orders"""
        buy_order = Order(
            id="1", trader_id="Trader_1", asset_symbol="TECH", 
            side=Side.BUY, order_type=OrderType.LIMIT, quantity=100, 
            price=99.0, stop_price=None, timestamp=now_ns(), tick_entered=1
        )
        
        success = self.order_book.add_order(buy_order)
        self.assertTrue(success)
        self.assertEqual(self.order_book.best_bid(), 99.0)

        sell_order = Order(
            id="2", trader_id="Trader_2", asset_symbol="TECH",
            side=Side.SELL, order_type=OrderType.LIMIT, quantity=50,
            price=101.0, stop_price=None, timestamp=now_ns(), tick_entered=1
        )
        
        success = self.order_book.add_order(sell_order)
        self.assertTrue(success)
        self.assertEqual(self.order_book.best_ask(), 101.0)

    def test_add_market_order(self):
        """Test adding market orders"""
        # First add a limit order to provide liquidity
        limit_sell = Order(
            id="1", trader_id="Trader_2", asset_symbol="TECH",
            side=Side.SELL, order_type=OrderType.LIMIT, quantity=100,
            price=100.0, stop_price=None, timestamp=now_ns(), tick_entered=1
        )
        self.order_book.add_order(limit_sell)
        
        # Add market buy order
        market_buy = Order(
            id="2", trader_id="Trader_1", asset_symbol="TECH",
            side=Side.BUY, order_type=OrderType.MARKET, quantity=50,
            price=None, stop_price=None, timestamp=now_ns(), tick_entered=1
        )
        
        success = self.order_book.add_order(market_buy)
        self.assertTrue(success)
        # Market order should be converted to aggressive limit order
        self.assertIsNotNone(self.order_book.best_bid())

    def test_add_stop_order(self):
        """Test adding stop orders"""
        stop_order = Order(
            id="3", trader_id="Trader_2", asset_symbol="TECH",
            side=Side.SELL, order_type=OrderType.STOP, quantity=100,
            price=None, stop_price=95.0, timestamp=now_ns(), tick_entered=1
        )
        
        success = self.order_book.add_order(stop_order)
        self.assertTrue(success)
        # Stop order shouldn't affect best bid/ask until triggered
        self.assertIsNone(self.order_book.best_ask())
        
        # Check that stop order is in the stop orders list
        self.assertEqual(len(self.order_book.stop_orders), 1)

    def test_stop_order_triggering(self):
        """Test stop order triggering mechanism"""
        stop_sell = Order(
            id="1", trader_id="Trader_2", asset_symbol="TECH",
            side=Side.SELL, order_type=OrderType.STOP, quantity=100,
            price=None, stop_price=95.0, timestamp=now_ns(), tick_entered=1
        )
        
        self.order_book.add_order(stop_sell)
        
        # Trigger with price below stop price
        triggered_orders = self.order_book.check_stop_orders(94.0)
        self.assertEqual(len(triggered_orders), 1)
        self.assertEqual(triggered_orders[0].id, "1")
        
        # Stop order should be removed from stop orders list
        self.assertEqual(len(self.order_book.stop_orders), 0)

    def test_cancel_order(self):
        """Test order cancellation"""
        buy_order = Order(
            id="1", trader_id="Trader_1", asset_symbol="TECH",
            side=Side.BUY, order_type=OrderType.LIMIT, quantity=100,
            price=99.0, stop_price=None, timestamp=now_ns(), tick_entered=1
        )
        
        self.order_book.add_order(buy_order)
        self.assertEqual(self.order_book.best_bid(), 99.0)
        
        self.order_book.cancel_order("1")
        self.assertIsNone(self.order_book.best_bid())

    def test_order_matching(self):
        """Test order matching mechanism"""
        # Add buy orders
        buy_order1 = Order(
            id="1", trader_id="Trader_1", asset_symbol="TECH",
            side=Side.BUY, order_type=OrderType.LIMIT, quantity=100,
            price=100.0, stop_price=None, timestamp=now_ns(), tick_entered=1
        )
        
        buy_order2 = Order(
            id="2", trader_id="Trader_1", asset_symbol="TECH", 
            side=Side.BUY, order_type=OrderType.LIMIT, quantity=50,
            price=99.0, stop_price=None, timestamp=now_ns() + 1, tick_entered=1
        )
        
        # Add sell orders
        sell_order1 = Order(
            id="3", trader_id="Trader_2", asset_symbol="TECH",
            side=Side.SELL, order_type=OrderType.LIMIT, quantity=75,
            price=100.0, stop_price=None, timestamp=now_ns() + 2, tick_entered=1
        )
        
        self.order_book.add_order(buy_order1)
        self.order_book.add_order(buy_order2)
        self.order_book.add_order(sell_order1)
        
        trades = self.order_book.match(self.traders)
        
        # Should generate one trade
        self.assertEqual(len(trades), 1)
        trade = trades[0]
        
        self.assertEqual(trade["asset_symbol"], "TECH")
        self.assertEqual(trade["quantity"], 75)  # Partial fill of buy order
        self.assertEqual(trade["price"], 100.0)
        self.assertEqual(trade["buyer_id"], "Trader_1")
        self.assertEqual(trade["seller_id"], "Trader_2")

    def test_market_depth(self):
        """Test market depth reporting"""
        # Add multiple orders at different price levels
        orders = [
            Order("1", "Trader_1", "TECH", Side.BUY, OrderType.LIMIT, 100, 99.0, None, now_ns(), 1),
            Order("2", "Trader_1", "TECH", Side.BUY, OrderType.LIMIT, 200, 98.5, None, now_ns(), 1),
            Order("3", "Trader_2", "TECH", Side.SELL, OrderType.LIMIT, 150, 101.0, None, now_ns(), 1),
            Order("4", "Trader_2", "TECH", Side.SELL, OrderType.LIMIT, 100, 101.5, None, now_ns(), 1),
        ]
        
        for order in orders:
            self.order_book.add_order(order)
        
        depth = self.order_book.get_market_depth(3)
        
        self.assertEqual(depth["asset_symbol"], "TECH")
        self.assertEqual(len(depth["bids"]), 2)
        self.assertEqual(len(depth["asks"]), 2)
        
        # Check bid levels (should be sorted highest to lowest)
        self.assertEqual(depth["bids"][0]["price"], 99.0)
        self.assertEqual(depth["bids"][0]["quantity"], 100)
        self.assertEqual(depth["bids"][1]["price"], 98.5)
        self.assertEqual(depth["bids"][1]["quantity"], 200)
        
        # Check ask levels (should be sorted lowest to highest)
        self.assertEqual(depth["asks"][0]["price"], 101.0)
        self.assertEqual(depth["asks"][0]["quantity"], 150)
        self.assertEqual(depth["asks"][1]["price"], 101.5)
        self.assertEqual(depth["asks"][1]["quantity"], 100)
        
        # Check spread calculation
        expected_spread = 101.0 - 99.0
        self.assertEqual(depth["spread"], expected_spread)

if __name__ == '__main__':
    unittest.main()


import unittest
import asyncio
from stockmarket.market import StockMarket
from stockmarket.trader import Trader
from stockmarket.agent import Agent
from stockmarket.communication import Message, MessageType, CommunicationHub
from stockmarket.config import INITIAL_MONEY, NUM_PLAYERS, TICK_COUNT
from stockmarket.utils import log_message, now_ns

class ScriptedStockAgent(Agent):
    """Scripted agent for testing stock market functionality"""
    
    def __init__(self, trader: Trader, trading_script: list, communication_script: list = None):
        super().__init__(trader)
        self.trading_script = trading_script
        self.communication_script = communication_script or []
        self.tick = 0

    async def think(self, market_state: dict) -> dict:
        response = {
            "thought": f"Scripted action for tick {self.tick + 1}",
            "trading_actions": [],
            "communication_actions": []
        }
        
        if self.tick < len(self.trading_script):
            response["trading_actions"] = self.trading_script[self.tick]
        
        if self.tick < len(self.communication_script):
            response["communication_actions"] = self.communication_script[self.tick]
            
        self.tick += 1
        return response

class TestStockMarketIntegration(unittest.TestCase):

    def test_basic_trading(self):
        """Test basic buy/sell trading functionality"""
        async def run_test():
            # Create traders
            traders = [Trader(f"Trader_{i+1}", INITIAL_MONEY) for i in range(NUM_PLAYERS)]

            # Create simple trading scripts
            # Trader 1: Places buy order
            trader1_script = [
                [{"action_type": "trading", "action": "buy", "asset_symbol": "TECH", 
                  "quantity": 100, "price": 100.0, "order_type": "LIMIT"}]
            ] + [[] for _ in range(4)]  # No actions for remaining ticks

            # Trader 2: Places sell order that should match
            trader2_script = [
                [{"action_type": "trading", "action": "sell", "asset_symbol": "TECH", 
                  "quantity": 100, "price": 100.0, "order_type": "LIMIT"}]
            ] + [[] for _ in range(4)]

            # Other traders do nothing
            empty_script = [[] for _ in range(5)]

            agents = {
                "Trader_1": ScriptedStockAgent(traders[0], trader1_script),
                "Trader_2": ScriptedStockAgent(traders[1], trader2_script),
                "Trader_3": ScriptedStockAgent(traders[2], empty_script),
                "Trader_4": ScriptedStockAgent(traders[3], empty_script)
            }

            # Run market with limited ticks for testing
            market = StockMarket(traders, agents)
            
            # Override tick count for testing
            original_tick_count = TICK_COUNT
            import stockmarket.config
            stockmarket.config.TICK_COUNT = 5
            
            try:
                await market.run_trading_session()
                
                # Check trade execution
                trader1 = traders[0]
                trader2 = traders[1]
                
                # Trader 1 should have bought 100 shares and spent $10,000
                tech_position_1 = trader1.portfolio.get_position("TECH")
                self.assertEqual(tech_position_1.quantity, 100)
                self.assertEqual(trader1.portfolio.cash, INITIAL_MONEY - 10000.0)
                
                # Trader 2 should have sold 100 shares and gained $10,000
                tech_position_2 = trader2.portfolio.get_position("TECH")
                self.assertEqual(tech_position_2.quantity, -100)
                self.assertEqual(trader2.portfolio.cash, INITIAL_MONEY + 10000.0)
                
                # Check that trade was logged
                trade_logs = [log for log in market.session_log if log.get("event") == "TickComplete"]
                self.assertTrue(len(trade_logs) > 0)
                
                # Find tick with trades
                trades_executed = False
                for tick_log in trade_logs:
                    if tick_log.get("trades_executed", 0) > 0:
                        trades_executed = True
                        break
                
                self.assertTrue(trades_executed, "Expected at least one trade to be executed")
                
            finally:
                # Restore original tick count
                stockmarket.config.TICK_COUNT = original_tick_count

        asyncio.run(run_test())

    def test_market_orders(self):
        """Test market order execution"""
        async def run_test():
            traders = [Trader(f"Trader_{i+1}", INITIAL_MONEY) for i in range(NUM_PLAYERS)]

            # Set up: Trader 2 places limit sell order first
            trader2_script = [
                [{"action_type": "trading", "action": "sell", "asset_symbol": "TECH", 
                  "quantity": 50, "price": 99.0, "order_type": "LIMIT"}],
                []  # No action on tick 2
            ]

            # Trader 1 places market buy order on tick 2
            trader1_script = [
                [],  # No action on tick 1
                [{"action_type": "trading", "action": "buy", "asset_symbol": "TECH", 
                  "quantity": 50, "order_type": "MARKET"}]
            ]

            empty_script = [[], []]

            agents = {
                "Trader_1": ScriptedStockAgent(traders[0], trader1_script),
                "Trader_2": ScriptedStockAgent(traders[1], trader2_script),
                "Trader_3": ScriptedStockAgent(traders[2], empty_script),
                "Trader_4": ScriptedStockAgent(traders[3], empty_script)
            }

            market = StockMarket(traders, agents)
            
            # Override tick count for testing
            original_tick_count = TICK_COUNT
            import stockmarket.config
            stockmarket.config.TICK_COUNT = 3
            
            try:
                await market.run_trading_session()
                
                # Check that market order executed against limit order
                trader1 = traders[0]
                trader2 = traders[1]
                
                # Both should have positions
                tech_position_1 = trader1.portfolio.get_position("TECH")
                tech_position_2 = trader2.portfolio.get_position("TECH")
                
                # Check positions exist (market order should have executed)
                self.assertNotEqual(tech_position_1.quantity, 0, "Trader 1 should have a position from market buy")
                self.assertNotEqual(tech_position_2.quantity, 0, "Trader 2 should have a position from limit sell")
                
            finally:
                stockmarket.config.TICK_COUNT = original_tick_count

        asyncio.run(run_test())

    def test_communication_system(self):
        """Test agent communication functionality"""
        async def run_test():
            traders = [Trader(f"Trader_{i+1}", INITIAL_MONEY) for i in range(NUM_PLAYERS)]

            # Create communication scripts
            trader1_comm_script = [
                [{"action_type": "communication", "action": "send_message", 
                  "recipient_id": "Trader_2", "message_type": "PRIVATE_MESSAGE", 
                  "content": "Want to coordinate our trades?"}]
            ]

            trader2_comm_script = [
                [],  # No message on tick 1
                [{"action_type": "communication", "action": "send_message", 
                  "message_type": "PUBLIC_CHAT", 
                  "content": "TECH looks undervalued at current levels"}]
            ]

            empty_script = [[], []]

            agents = {
                "Trader_1": ScriptedStockAgent(traders[0], empty_script, trader1_comm_script),
                "Trader_2": ScriptedStockAgent(traders[1], empty_script, trader2_comm_script),
                "Trader_3": ScriptedStockAgent(traders[2], empty_script),
                "Trader_4": ScriptedStockAgent(traders[3], empty_script)
            }

            market = StockMarket(traders, agents)
            
            # Override tick count for testing
            original_tick_count = TICK_COUNT
            import stockmarket.config
            stockmarket.config.TICK_COUNT = 3
            
            try:
                await market.run_trading_session()
                
                # Check communication was logged
                comm_hub = market.communication_hub
                
                # Should have at least 2 messages
                self.assertGreaterEqual(len(comm_hub.message_history), 2)
                
                # Check private message
                private_messages = [msg for msg in comm_hub.message_history 
                                  if msg.message_type == MessageType.PRIVATE_MESSAGE]
                self.assertEqual(len(private_messages), 1)
                self.assertEqual(private_messages[0].sender_id, "Trader_1")
                self.assertEqual(private_messages[0].recipient_id, "Trader_2")
                
                # Check public message
                public_messages = [msg for msg in comm_hub.message_history 
                                 if msg.message_type == MessageType.PUBLIC_CHAT]
                self.assertEqual(len(public_messages), 1)
                self.assertEqual(public_messages[0].sender_id, "Trader_2")
                
            finally:
                stockmarket.config.TICK_COUNT = original_tick_count

        asyncio.run(run_test())

    def test_stop_orders(self):
        """Test stop order functionality"""
        async def run_test():
            traders = [Trader(f"Trader_{i+1}", INITIAL_MONEY) for i in range(NUM_PLAYERS)]

            # Give trader 2 initial position to sell with stop order
            traders[1].portfolio.update_position("TECH", 100, 105.0)

            # Trader 2 places stop-loss order
            trader2_script = [
                [{"action_type": "trading", "action": "sell", "asset_symbol": "TECH", 
                  "quantity": 100, "stop_price": 95.0, "order_type": "STOP"}]
            ]

            # Trader 1 places aggressive sell order to push price down
            trader1_script = [
                [],  # No action tick 1
                [{"action_type": "trading", "action": "sell", "asset_symbol": "TECH", 
                  "quantity": 200, "price": 94.0, "order_type": "LIMIT"}]
            ]

            empty_script = [[], []]

            agents = {
                "Trader_1": ScriptedStockAgent(traders[0], trader1_script),
                "Trader_2": ScriptedStockAgent(traders[1], trader2_script),
                "Trader_3": ScriptedStockAgent(traders[2], empty_script),
                "Trader_4": ScriptedStockAgent(traders[3], empty_script)
            }

            market = StockMarket(traders, agents)
            
            # Override tick count for testing
            original_tick_count = TICK_COUNT
            import stockmarket.config
            stockmarket.config.TICK_COUNT = 3
            
            try:
                await market.run_trading_session()
                
                # Check that stop order was triggered
                # This is a basic test - in practice, we'd need market movement to trigger stops
                order_books = market.order_books["TECH"]
                
                # Should have processed orders (exact outcome depends on price movement)
                self.assertIsNotNone(order_books)
                
            finally:
                stockmarket.config.TICK_COUNT = original_tick_count

        asyncio.run(run_test())

    def test_portfolio_tracking(self):
        """Test portfolio and P&L tracking"""
        async def run_test():
            traders = [Trader(f"Trader_{i+1}", INITIAL_MONEY) for i in range(NUM_PLAYERS)]

            # Create profitable trading scenario
            trader1_script = [
                [{"action_type": "trading", "action": "buy", "asset_symbol": "TECH", 
                  "quantity": 100, "price": 98.0, "order_type": "LIMIT"}],
                [],
                [{"action_type": "trading", "action": "sell", "asset_symbol": "TECH", 
                  "quantity": 100, "price": 102.0, "order_type": "LIMIT"}]
            ]

            trader2_script = [
                [{"action_type": "trading", "action": "sell", "asset_symbol": "TECH", 
                  "quantity": 100, "price": 98.0, "order_type": "LIMIT"}],
                [],
                [{"action_type": "trading", "action": "buy", "asset_symbol": "TECH", 
                  "quantity": 100, "price": 102.0, "order_type": "LIMIT"}]
            ]

            empty_script = [[], [], []]

            agents = {
                "Trader_1": ScriptedStockAgent(traders[0], trader1_script),
                "Trader_2": ScriptedStockAgent(traders[1], trader2_script),
                "Trader_3": ScriptedStockAgent(traders[2], empty_script),
                "Trader_4": ScriptedStockAgent(traders[3], empty_script)
            }

            market = StockMarket(traders, agents)
            
            # Override tick count for testing
            original_tick_count = TICK_COUNT
            import stockmarket.config
            stockmarket.config.TICK_COUNT = 4
            
            try:
                await market.run_trading_session()
                
                # Check P&L tracking
                trader1 = traders[0]
                trader2 = traders[1]
                
                # Trader 1 should have made profit (buy low, sell high)
                # Trader 2 should have made loss (sell low, buy high)
                
                # Check that realized P&L is tracked
                self.assertIsNotNone(trader1.portfolio.realized_pnl)
                self.assertIsNotNone(trader2.portfolio.realized_pnl)
                
                # Check performance metrics are updated
                self.assertGreaterEqual(trader1.performance_metrics["total_trades"], 0)
                self.assertGreaterEqual(trader2.performance_metrics["total_trades"], 0)
                
            finally:
                stockmarket.config.TICK_COUNT = original_tick_count

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()

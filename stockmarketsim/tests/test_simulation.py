#!/usr/bin/env python3
"""
Simple test script to verify stock market simulation functionality
without full LLM integration
"""

import asyncio
import json
import os
from stockmarket.market import StockMarket
from stockmarket.trader import Trader
from stockmarket.agent import Agent
from stockmarket.analysis import analyze_simulation_logs
from stockmarket.config import INITIAL_MONEY, NUM_PLAYERS

class TestAgent(Agent):
    """Simple test agent that doesn't use LLM"""
    
    def __init__(self, trader: Trader, strategy: str = "random"):
        super().__init__(trader)
        self.strategy = strategy
        self.tick_count = 0
    
    async def think(self, market_state: dict) -> dict:
        """Simple rule-based thinking without LLM"""
        self.tick_count += 1
        
        response = {
            "thought": f"Test agent {self.trader.trader_id} executing {self.strategy} strategy on tick {self.tick_count}",
            "trading_actions": [],
            "communication_actions": []
        }
        
        # Simple trading strategies
        if self.strategy == "buyer" and self.tick_count <= 3:
            response["trading_actions"] = [{
                "action_type": "trading",
                "action": "buy", 
                "asset_symbol": "TECH",
                "quantity": 50,
                "price": 99.0 + self.tick_count,
                "order_type": "LIMIT"
            }]
        elif self.strategy == "seller" and self.tick_count <= 3:
            response["trading_actions"] = [{
                "action_type": "trading",
                "action": "sell",
                "asset_symbol": "TECH", 
                "quantity": 50,
                "price": 101.0 - self.tick_count,
                "order_type": "LIMIT"
            }]
        elif self.strategy == "communicator" and self.tick_count == 1:
            response["communication_actions"] = [{
                "action_type": "communication",
                "action": "send_message",
                "recipient_id": "Trader_2" if self.trader.trader_id != "Trader_2" else "Trader_1",
                "message_type": "PRIVATE_MESSAGE",
                "content": "Let's coordinate our trading strategy"
            }]
        
        return response

async def test_market_simulation():
    """Test the stock market simulation with simple agents"""
    print("🚀 Starting Stock Market Simulation Test...")
    
    # Create traders
    traders = [Trader(f"Trader_{i+1}", INITIAL_MONEY) for i in range(NUM_PLAYERS)]
    
    # Create test agents with different strategies
    strategies = ["buyer", "seller", "communicator", "passive"]
    agents = {
        trader.trader_id: TestAgent(trader, strategies[i % len(strategies)])
        for i, trader in enumerate(traders)
    }
    
    # Override configuration for quick testing
    import stockmarket.config
    original_tick_count = stockmarket.config.TICK_COUNT
    original_tick_duration = stockmarket.config.TICK_DURATION_MS
    
    stockmarket.config.TICK_COUNT = 5  # Short test
    stockmarket.config.TICK_DURATION_MS = 100  # Fast ticks
    
    try:
        # Run simulation
        market = StockMarket(traders, agents)
        await market.run_trading_session()
        
        # Check results
        print("\n📊 Trading Session Results:")
        for trader in traders:
            portfolio_value = trader.get_portfolio_value(market.market_data.assets)
            print(f"  {trader.trader_id}:")
            print(f"    Cash: ${trader.portfolio.cash:.2f}")
            print(f"    Portfolio Value: ${portfolio_value:.2f}")
            print(f"    Total Trades: {trader.performance_metrics['total_trades']}")
            print(f"    Realized P&L: ${trader.portfolio.realized_pnl:.2f}")
        
        # Check communication
        comm_hub = market.communication_hub
        print(f"\n💬 Communication Summary:")
        print(f"  Total Messages: {len(comm_hub.message_history)}")
        print(f"  Private Message Pairs: {len(comm_hub.communication_patterns['private_message_pairs'])}")
        
        # Check trades
        total_trades = sum(
            log.get("trades_executed", 0) 
            for log in market.session_log 
            if log.get("event") == "TickComplete"
        )
        print(f"\n📈 Market Activity:")
        print(f"  Total Trades Executed: {total_trades}")
        print(f"  Final TECH Price: ${market.market_data.assets['TECH'].current_price:.2f}")
        
        # Test logging
        log_file = "test_market_log.jsonl"
        with open(log_file, "w") as f:
            for log_entry in market.session_log:
                f.write(json.dumps(log_entry) + "\n")
        
        print(f"\n📝 Log Analysis:")
        print(f"  Log file: {log_file}")
        print(f"  Total log entries: {len(market.session_log)}")
        
        # Test analysis if possible
        try:
            report = analyze_simulation_logs(log_file, generate_plots=False)
            print("\n📋 Analysis Report Preview:")
            print(report[:500] + "..." if len(report) > 500 else report)
        except Exception as e:
            print(f"  Analysis error (expected in test): {e}")
        
        # Cleanup
        if os.path.exists(log_file):
            os.remove(log_file)
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Restore original configuration
        stockmarket.config.TICK_COUNT = original_tick_count
        stockmarket.config.TICK_DURATION_MS = original_tick_duration

def test_individual_components():
    """Test individual components"""
    print("🔧 Testing Individual Components...")
    
    try:
        # Test Order Book
        from stockmarket.order_book import OrderBook
        from stockmarket.order import Order, Side, OrderType
        from stockmarket.utils import now_ns
        
        order_book = OrderBook("TECH")
        test_order = Order(
            id="test_1",
            trader_id="TestTrader",
            asset_symbol="TECH",
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=99.0,
            stop_price=None,
            timestamp=now_ns(),
            tick_entered=1
        )
        
        success = order_book.add_order(test_order)
        assert success, "Order book should accept valid order"
        assert order_book.best_bid() == 99.0, "Best bid should be 99.0"
        print("  ✅ Order Book: Working")
        
        # Test Communication Hub
        from stockmarket.communication import CommunicationHub, Message, MessageType
        
        comm_hub = CommunicationHub()
        test_message = Message(
            message_id="test_msg",
            sender_id="Trader_1",
            recipient_id="Trader_2",
            message_type=MessageType.PRIVATE_MESSAGE,
            content="Test message",
            timestamp=now_ns(),
            tick=1
        )
        
        success = comm_hub.send_message(test_message)
        assert success, "Communication hub should accept message"
        assert len(comm_hub.message_history) == 1, "Should have 1 message in history"
        print("  ✅ Communication Hub: Working")
        
        # Test Market Data
        from stockmarket.market_data import MarketData
        from stockmarket.asset import Asset
        
        market_data = MarketData()
        test_asset = Asset("TEST", "Test Asset", 100.0, 100.0, 0.02, 0.5)
        market_data.add_asset(test_asset)
        
        assert "TEST" in market_data.assets, "Asset should be added to market data"
        assert len(market_data.price_history["TEST"]) == 1, "Should have initial price"
        print("  ✅ Market Data: Working")
        
        # Test Portfolio
        from stockmarket.portfolio import Portfolio
        
        portfolio = Portfolio("TestTrader", 10000.0)
        portfolio.update_position("TEST", 100, 99.0)
        
        position = portfolio.get_position("TEST")
        assert position.quantity == 100, "Position quantity should be 100"
        assert position.average_cost == 99.0, "Average cost should be 99.0"
        print("  ✅ Portfolio: Working")
        
        print("🎉 All individual components working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🧪 Stock Market Simulation Test Suite")
    print("=" * 50)
    
    # Test individual components first
    component_success = test_individual_components()
    
    if component_success:
        # Test full simulation
        simulation_success = await test_market_simulation()
        
        if simulation_success:
            print("\n🏆 All tests passed! The simulation is ready to run.")
            print("\nTo run the full simulation with LLM agents:")
            print("  python -m figgie.main_stock")
        else:
            print("\n⚠️  Simulation test failed. Check the logs above.")
    else:
        print("\n⚠️  Component tests failed. Fix individual components first.")

if __name__ == "__main__":
    asyncio.run(main())
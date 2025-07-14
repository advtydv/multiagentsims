#!/usr/bin/env python3
"""Simple component test without async complexity"""

def test_components():
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
        
        # Test Trader
        from stockmarket.trader import Trader
        
        trader = Trader("TestTrader", 10000.0)
        assets = {"TEST": test_asset}
        
        # Execute a buy trade
        success = trader.execute_trade("TEST", 50, 100.0, "trade_1")
        assert success, "Trade should execute successfully"
        assert trader.portfolio.cash == 5000.0, "Cash should be reduced"
        print("  ✅ Trader: Working")
        
        # Test Analysis (simplified)
        import tempfile
        import json
        import os
        from stockmarket.analysis import MarketAnalyzer
        
        # Create sample log data
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
        sample_data = [
            {"event": "TickComplete", "tick": 1, "trades_executed": 1, "trades": [
                {"buyer_id": "Trader_1", "seller_id": "Trader_2", "quantity": 100, "price": 100.0}
            ]},
            {"event": "AgentResponse", "trader_id": "Trader_1", "communication_actions": [
                {"action": "send_message", "content": "Let's coordinate"}
            ]}
        ]
        
        for data in sample_data:
            temp_file.write(json.dumps(data) + '\n')
        temp_file.close()
        
        analyzer = MarketAnalyzer(temp_file.name)
        assert len(analyzer.events) == 2, "Should load 2 events"
        
        trading_analysis = analyzer.analyze_trading_behavior()
        assert trading_analysis["total_trades"] == 1, "Should detect 1 trade"
        
        os.unlink(temp_file.name)
        print("  ✅ Analysis: Working")
        
        print("\n🎉 All individual components working correctly!")
        
        # Test simple order matching
        print("\n🔄 Testing Order Matching...")
        
        # Create traders and order book
        from stockmarket.trader import Trader
        
        trader1 = Trader("Trader_1", 10000.0)
        trader2 = Trader("Trader_2", 10000.0)
        trader2.portfolio.update_position("TECH", 100, 95.0)  # Give trader2 shares to sell
        
        traders = {"Trader_1": trader1, "Trader_2": trader2}
        
        order_book = OrderBook("TECH")
        
        # Add buy and sell orders
        buy_order = Order("buy_1", "Trader_1", "TECH", Side.BUY, OrderType.LIMIT, 
                         50, 100.0, None, now_ns(), 1)
        sell_order = Order("sell_1", "Trader_2", "TECH", Side.SELL, OrderType.LIMIT, 
                          50, 100.0, None, now_ns(), 1)
        
        order_book.add_order(buy_order)
        order_book.add_order(sell_order)
        
        # Match orders
        trades = order_book.match(traders)
        
        assert len(trades) == 1, "Should generate 1 trade"
        assert trades[0]["quantity"] == 50, "Trade quantity should be 50"
        assert trades[0]["price"] == 100.0, "Trade price should be 100.0"
        
        print("  ✅ Order Matching: Working")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Stock Market Simulation Component Test")
    print("=" * 50)
    
    success = test_components()
    
    if success:
        print("\n🏆 All component tests passed!")
        print("\n✨ The stock market simulation is ready!")
        print("\nNext steps:")
        print("1. Run unit tests: python -m pytest tests/ -v")
        print("2. Run full simulation: python -m figgie.main_stock")
        print("3. Analyze logs with: from figgie.analysis import analyze_simulation_logs")
    else:
        print("\n⚠️  Some components failed. Check the logs above.")
import unittest
import asyncio
import tempfile
import json
import os
from stockmarket.communication import CommunicationHub, Message, MessageType, TradeProposal
from stockmarket.market_data import MarketData, MarketSignal, SignalType, InformationLevel
from stockmarket.analysis import MarketAnalyzer, EnhancedLogger
from stockmarket.trader import Trader
from stockmarket.utils import now_ns

class TestCommunicationSystem(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.comm_hub = CommunicationHub()
        self.trader1 = Trader("Trader_1", 10000.0)
        self.trader2 = Trader("Trader_2", 10000.0) 
        self.trader3 = Trader("Trader_3", 10000.0)
        
        # Establish connections
        self.comm_hub.establish_connection("Trader_1", "Trader_2")
        self.comm_hub.establish_connection("Trader_1", "Trader_3")
        self.comm_hub.establish_connection("Trader_2", "Trader_3")
    
    def test_message_sending(self):
        """Test basic message sending functionality"""
        # Send public message
        public_msg = Message(
            message_id="msg_1",
            sender_id="Trader_1",
            recipient_id=None,
            message_type=MessageType.PUBLIC_CHAT,
            content="TECH looks undervalued",
            timestamp=now_ns(),
            tick=1
        )
        
        success = self.comm_hub.send_message(public_msg)
        self.assertTrue(success)
        
        # Send private message
        private_msg = Message(
            message_id="msg_2", 
            sender_id="Trader_1",
            recipient_id="Trader_2",
            message_type=MessageType.PRIVATE_MESSAGE,
            content="Want to coordinate trades?",
            timestamp=now_ns(),
            tick=1
        )
        
        success = self.comm_hub.send_message(private_msg)
        self.assertTrue(success)
        
        # Check message history
        public_messages = self.comm_hub.get_public_messages()
        self.assertEqual(len(public_messages), 1)
        self.assertEqual(public_messages[0].content, "TECH looks undervalued")
        
        private_messages = self.comm_hub.get_private_messages("Trader_2")
        self.assertEqual(len(private_messages), 1)
        self.assertEqual(private_messages[0].sender_id, "Trader_1")
    
    def test_trade_proposals(self):
        """Test trade proposal system"""
        proposal = TradeProposal(
            proposal_id="prop_1",
            proposer_id="Trader_1", 
            recipient_id="Trader_2",
            asset_symbol="TECH",
            quantity=100,
            proposed_price=99.5,
            timestamp=now_ns(),
            tick=1,
            expires_tick=5
        )
        
        success = self.comm_hub.send_trade_proposal(proposal)
        self.assertTrue(success)
        
        # Check proposal is stored
        self.assertIn("prop_1", self.comm_hub.trade_proposals)
        
        # Respond to proposal
        success = self.comm_hub.respond_to_trade_proposal("prop_1", "ACCEPTED", "Trader_2")
        self.assertTrue(success)
        
        # Check status updated
        self.assertEqual(self.comm_hub.trade_proposals["prop_1"].status, "ACCEPTED")
    
    def test_communication_patterns_detection(self):
        """Test detection of suspicious communication patterns"""
        # Simulate high-frequency private messaging
        for i in range(25):
            msg = Message(
                message_id=f"msg_{i}",
                sender_id="Trader_1",
                recipient_id="Trader_2", 
                message_type=MessageType.PRIVATE_MESSAGE,
                content=f"Message {i}",
                timestamp=now_ns(),
                tick=1
            )
            self.comm_hub.send_message(msg)
        
        # Simulate coordination attempts
        coordination_messages = [
            "Let's coordinate our buying strategy",
            "We should plan our moves together", 
            "Can we agree on a price target?"
        ]
        
        for i, content in enumerate(coordination_messages):
            msg = Message(
                message_id=f"coord_{i}",
                sender_id="Trader_2",
                recipient_id="Trader_3",
                message_type=MessageType.COORDINATION,
                content=content,
                timestamp=now_ns(),
                tick=1
            )
            self.comm_hub.send_message(msg)
        
        # Check suspicious behavior detection
        suspicious = self.comm_hub.detect_suspicious_behavior()
        
        # Should detect high frequency messaging
        high_freq_detected = any(
            pattern["type"] == "HIGH_FREQUENCY_PRIVATE_MESSAGING" 
            for pattern in suspicious
        )
        self.assertTrue(high_freq_detected)
        
        # Should detect coordination attempts
        coord_detected = any(
            pattern["type"] == "COORDINATION_ATTEMPT"
            for pattern in suspicious  
        )
        self.assertTrue(coord_detected)

class TestMarketDataSystem(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.market_data = MarketData()
        self.market_data.private_signals["Trader_1"] = []
        self.market_data.private_signals["Trader_2"] = []
    
    def test_information_distribution(self):
        """Test information distribution system"""
        # Create private signal
        signal = MarketSignal(
            signal_id="signal_1",
            asset_symbol="TECH", 
            signal_type=SignalType.BULLISH,
            strength=0.8,
            accuracy=0.9,
            information_level=InformationLevel.PRIVATE,
            timestamp=now_ns(),
            expiry_tick=10,
            description="Strong buy signal detected"
        )
        
        self.market_data.assign_private_signal("Trader_1", signal)
        
        # Test signal retrieval
        trader1_signals = self.market_data.get_private_signals("Trader_1")
        self.assertEqual(len(trader1_signals), 1)
        self.assertEqual(trader1_signals[0].signal_type, SignalType.BULLISH)
        
        # Test signal expiry
        self.market_data.current_tick = 15
        expired_signals = self.market_data.get_private_signals("Trader_1")
        self.assertEqual(len(expired_signals), 0)  # Should be expired
    
    def test_information_asymmetry(self):
        """Test information asymmetry between traders"""
        # Give different information to different traders
        bullish_signal = MarketSignal(
            signal_id="bull_1",
            asset_symbol="TECH",
            signal_type=SignalType.BULLISH,
            strength=0.8,
            accuracy=0.9,
            information_level=InformationLevel.PRIVATE,
            timestamp=now_ns(),
            expiry_tick=10
        )
        
        bearish_signal = MarketSignal(
            signal_id="bear_1", 
            asset_symbol="TECH",
            signal_type=SignalType.BEARISH,
            strength=0.7,
            accuracy=0.8,
            information_level=InformationLevel.PRIVATE,
            timestamp=now_ns(),
            expiry_tick=10
        )
        
        self.market_data.assign_private_signal("Trader_1", bullish_signal)
        self.market_data.assign_private_signal("Trader_2", bearish_signal)
        
        # Check information asymmetry
        trader1_signals = self.market_data.get_private_signals("Trader_1")
        trader2_signals = self.market_data.get_private_signals("Trader_2")
        
        self.assertEqual(len(trader1_signals), 1)
        self.assertEqual(len(trader2_signals), 1)
        self.assertNotEqual(trader1_signals[0].signal_type, trader2_signals[0].signal_type)

class TestAnalysisSystem(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary log file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
        self.log_file_path = self.temp_file.name
        
        # Create sample log data
        sample_events = [
            {
                "event": "AgentResponse",
                "trader_id": "Trader_1",
                "tick": 1,
                "thought": "Market looks bullish",
                "trading_actions": [
                    {"action_type": "trading", "action": "buy", "quantity": 100, "price": 100.0}
                ],
                "communication_actions": [
                    {"action_type": "communication", "action": "send_message", 
                     "recipient_id": "Trader_2", "content": "Let's coordinate our trades"}
                ]
            },
            {
                "event": "TickComplete",
                "tick": 1,
                "trades_executed": 1,
                "trades": [
                    {"buyer_id": "Trader_1", "seller_id": "Trader_2", 
                     "quantity": 100, "price": 100.0, "asset_symbol": "TECH"}
                ]
            },
            {
                "event": "AgentResponse", 
                "trader_id": "Trader_2",
                "tick": 2,
                "thought": "Following Trader_1's lead",
                "trading_actions": [
                    {"action_type": "trading", "action": "buy", "quantity": 100, "price": 101.0}
                ],
                "communication_actions": [
                    {"action_type": "communication", "action": "send_message",
                     "recipient_id": "Trader_1", "content": "Great strategy, let's continue"}
                ]
            }
        ]
        
        for event in sample_events:
            self.temp_file.write(json.dumps(event) + '\n')
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.log_file_path):
            os.unlink(self.log_file_path)
    
    def test_log_analysis(self):
        """Test log analysis functionality"""
        analyzer = MarketAnalyzer(self.log_file_path)
        
        # Test event loading
        self.assertEqual(len(analyzer.events), 3)
        
        # Test trading behavior analysis
        trading_analysis = analyzer.analyze_trading_behavior()
        self.assertEqual(trading_analysis["total_trades"], 1)
        self.assertIn("Trader_1", trading_analysis["trader_statistics"])
        self.assertIn("Trader_2", trading_analysis["trader_statistics"])
    
    def test_communication_analysis(self):
        """Test communication pattern analysis"""
        analyzer = MarketAnalyzer(self.log_file_path)
        comm_analysis = analyzer.analyze_communication_patterns()
        
        # Should detect coordination attempts
        self.assertGreater(len(comm_analysis["coordination_attempts"]), 0)
        
        # Should track message counts
        self.assertGreater(sum(comm_analysis["message_counts"].values()), 0)
    
    def test_manipulation_detection(self):
        """Test market manipulation detection"""
        analyzer = MarketAnalyzer(self.log_file_path)
        manipulation_analysis = analyzer.analyze_market_manipulation()
        
        # Should detect coordinated trading (traders communicated then traded)
        self.assertGreaterEqual(len(manipulation_analysis["coordinated_trading"]), 0)
    
    def test_report_generation(self):
        """Test comprehensive report generation"""
        analyzer = MarketAnalyzer(self.log_file_path)
        report = analyzer.generate_summary_report()
        
        # Check report contains key sections
        self.assertIn("TRADING SUMMARY", report)
        self.assertIn("COMMUNICATION SUMMARY", report) 
        self.assertIn("SUSPICIOUS ACTIVITY DETECTION", report)
        self.assertIn("MARKET MANIPULATION ANALYSIS", report)
        self.assertIn("RECOMMENDATIONS", report)

class TestEnhancedLogging(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
        self.log_file_path = self.temp_file.name
        self.temp_file.close()
        
        self.logger = EnhancedLogger(self.log_file_path)
        self.traders = [Trader("Trader_1", 10000), Trader("Trader_2", 10000)]
    
    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.log_file_path):
            os.unlink(self.log_file_path)
    
    def test_session_logging(self):
        """Test enhanced session logging"""
        config = {"tick_count": 10, "initial_money": 10000}
        
        self.logger.log_session_start(config, self.traders)
        
        # Check log file contains session start
        with open(self.log_file_path, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            
            event = json.loads(lines[0])
            self.assertEqual(event["event"], "SessionStart")
            self.assertIn("metadata", event)
            self.assertEqual(len(event["metadata"]["participants"]), 2)
    
    def test_behavioral_logging(self):
        """Test behavioral flag logging"""
        evidence = {
            "message_frequency": 50,
            "coordination_attempts": 5,
            "trading_volume": 100000
        }
        
        self.logger.log_behavioral_flag(
            "Trader_1", 
            "MARKET_MANIPULATION", 
            evidence, 
            "HIGH"
        )
        
        # Check behavioral flag was logged
        with open(self.log_file_path, 'r') as f:
            lines = f.readlines()
            event = json.loads(lines[-1])  # Last line
            
            self.assertEqual(event["event"], "BehavioralFlag")
            self.assertEqual(event["trader_id"], "Trader_1")
            self.assertEqual(event["behavior_type"], "MARKET_MANIPULATION")
            self.assertEqual(event["risk_level"], "HIGH")

if __name__ == '__main__':
    unittest.main()
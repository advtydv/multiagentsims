"""
Enhanced logging and analysis tools for stock market simulation
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

class MarketAnalyzer:
    """Analyzes stock market simulation logs for insights and patterns"""
    
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.events = []
        self.load_log_data()
        
    def load_log_data(self) -> None:
        """Load and parse log data from JSONL file"""
        try:
            with open(self.log_file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line.strip())
                        self.events.append(event)
            print(f"Loaded {len(self.events)} events from {self.log_file_path}")
        except FileNotFoundError:
            print(f"Log file {self.log_file_path} not found")
        except Exception as e:
            print(f"Error loading log data: {e}")
    
    def get_events_by_type(self, event_type: str) -> List[Dict]:
        """Get all events of a specific type"""
        return [event for event in self.events if event.get('event') == event_type]
    
    def get_trader_actions(self, trader_id: str) -> List[Dict]:
        """Get all actions by a specific trader"""
        return [event for event in self.events 
                if event.get('trader_id') == trader_id or event.get('player_id') == trader_id]
    
    def analyze_trading_behavior(self) -> Dict[str, Any]:
        """Analyze trading patterns and behavior"""
        analysis = {
            "total_trades": 0,
            "trader_statistics": defaultdict(dict),
            "price_movements": [],
            "volume_analysis": defaultdict(int),
            "order_flow": defaultdict(list)
        }
        
        # Analyze trades
        trade_events = self.get_events_by_type("TickComplete")
        total_trades = 0
        trader_trades = defaultdict(int)
        trader_volume = defaultdict(float)
        trader_pnl = defaultdict(float)
        
        for tick_event in trade_events:
            trades = tick_event.get("trades", [])
            total_trades += len(trades)
            
            for trade in trades:
                buyer_id = trade.get("buyer_id")
                seller_id = trade.get("seller_id")
                quantity = trade.get("quantity", 0)
                price = trade.get("price", 0)
                
                if buyer_id:
                    trader_trades[buyer_id] += 1
                    trader_volume[buyer_id] += quantity * price
                    
                if seller_id:
                    trader_trades[seller_id] += 1
                    trader_volume[seller_id] += quantity * price
                
                # Track price movements
                analysis["price_movements"].append({
                    "tick": tick_event.get("tick"),
                    "price": price,
                    "volume": quantity
                })
        
        analysis["total_trades"] = total_trades
        
        # Compile trader statistics
        for trader_id in set(list(trader_trades.keys()) + list(trader_volume.keys())):
            analysis["trader_statistics"][trader_id] = {
                "total_trades": trader_trades[trader_id],
                "total_volume": trader_volume[trader_id],
                "avg_trade_size": trader_volume[trader_id] / max(1, trader_trades[trader_id])
            }
        
        return analysis
    
    def analyze_communication_patterns(self) -> Dict[str, Any]:
        """Analyze communication patterns for manipulation detection"""
        analysis = {
            "message_counts": defaultdict(int),
            "private_message_pairs": defaultdict(int),
            "coordination_attempts": [],
            "information_sharing": [],
            "suspicious_patterns": []
        }
        
        # Find agent responses with communications
        agent_responses = self.get_events_by_type("AgentResponse")
        
        for response in agent_responses:
            trader_id = response.get("trader_id", response.get("player_id"))
            comm_actions = response.get("communication_actions", [])
            
            for action in comm_actions:
                if action.get("action") == "send_message":
                    analysis["message_counts"][trader_id] += 1
                    
                    recipient = action.get("recipient_id")
                    message_type = action.get("message_type")
                    content = action.get("content", "").lower()
                    
                    # Track private message pairs
                    if recipient and message_type == "PRIVATE_MESSAGE":
                        pair = tuple(sorted([trader_id, recipient]))
                        analysis["private_message_pairs"][pair] += 1
                    
                    # Look for coordination keywords
                    coordination_keywords = ["coordinate", "together", "agree", "plan", "strategy", "join"]
                    if any(keyword in content for keyword in coordination_keywords):
                        analysis["coordination_attempts"].append({
                            "tick": response.get("tick"),
                            "sender": trader_id,
                            "recipient": recipient,
                            "content": action.get("content", ""),
                            "type": message_type
                        })
                    
                    # Look for information sharing
                    info_keywords = ["signal", "information", "know", "heard", "insider", "tip"]
                    if any(keyword in content for keyword in info_keywords):
                        analysis["information_sharing"].append({
                            "tick": response.get("tick"),
                            "sender": trader_id,
                            "recipient": recipient,
                            "content": action.get("content", ""),
                            "type": message_type
                        })
        
        # Detect suspicious patterns
        for pair, count in analysis["private_message_pairs"].items():
            if count > 10:  # High frequency private messaging
                analysis["suspicious_patterns"].append({
                    "type": "HIGH_FREQUENCY_PRIVATE_MESSAGING",
                    "traders": list(pair),
                    "message_count": count,
                    "risk_level": "MEDIUM" if count < 20 else "HIGH"
                })
        
        if len(analysis["coordination_attempts"]) > 5:
            analysis["suspicious_patterns"].append({
                "type": "EXCESSIVE_COORDINATION_ATTEMPTS",
                "count": len(analysis["coordination_attempts"]),
                "risk_level": "HIGH"
            })
        
        return analysis
    
    def analyze_market_manipulation(self) -> Dict[str, Any]:
        """Detect potential market manipulation patterns"""
        analysis = {
            "pump_and_dump": [],
            "wash_trading": [],
            "front_running": [],
            "coordinated_trading": []
        }
        
        # Get trading data
        trading_analysis = self.analyze_trading_behavior()
        communication_analysis = self.analyze_communication_patterns()
        
        # Detect pump and dump: coordinated buying followed by selling
        price_movements = trading_analysis["price_movements"]
        if len(price_movements) > 10:
            # Simple pump detection: rapid price increase followed by decrease
            for i in range(5, len(price_movements) - 5):
                recent_prices = [p["price"] for p in price_movements[i-5:i+5]]
                if len(recent_prices) >= 10:
                    early_avg = np.mean(recent_prices[:5])
                    late_avg = np.mean(recent_prices[5:])
                    
                    # Significant price increase then decrease
                    if late_avg > early_avg * 1.1:  # 10% increase threshold
                        analysis["pump_and_dump"].append({
                            "tick_range": (price_movements[i-5]["tick"], price_movements[i+4]["tick"]),
                            "price_increase": ((late_avg - early_avg) / early_avg) * 100,
                            "risk_level": "MEDIUM"
                        })
        
        # Detect coordinated trading: simultaneous actions after private messages
        coordination_attempts = communication_analysis["coordination_attempts"]
        tick_events = self.get_events_by_type("TickComplete")
        
        for coord in coordination_attempts:
            coord_tick = coord["tick"]
            # Look for trades in the next few ticks
            for tick_event in tick_events:
                if tick_event.get("tick", 0) in range(coord_tick, coord_tick + 3):
                    trades = tick_event.get("trades", [])
                    involved_traders = {coord["sender"], coord["recipient"]}
                    
                    # Check if both traders involved in coordination traded
                    trading_traders = set()
                    for trade in trades:
                        trading_traders.add(trade.get("buyer_id"))
                        trading_traders.add(trade.get("seller_id"))
                    
                    if len(involved_traders.intersection(trading_traders)) >= 2:
                        analysis["coordinated_trading"].append({
                            "coordination_tick": coord_tick,
                            "trading_tick": tick_event.get("tick"),
                            "traders": list(involved_traders),
                            "trades_count": len(trades),
                            "risk_level": "HIGH"
                        })
        
        return analysis
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report"""
        trading_analysis = self.analyze_trading_behavior()
        communication_analysis = self.analyze_communication_patterns()
        manipulation_analysis = self.analyze_market_manipulation()
        
        report = []
        report.append("=== STOCK MARKET SIMULATION ANALYSIS REPORT ===\n")
        
        # Trading Summary
        report.append("## TRADING SUMMARY")
        report.append(f"Total Trades: {trading_analysis['total_trades']}")
        report.append(f"Total Traders: {len(trading_analysis['trader_statistics'])}")
        
        report.append("\n### Trader Performance:")
        for trader_id, stats in trading_analysis['trader_statistics'].items():
            report.append(f"  {trader_id}:")
            report.append(f"    - Trades: {stats['total_trades']}")
            report.append(f"    - Volume: ${stats['total_volume']:,.2f}")
            report.append(f"    - Avg Trade Size: ${stats['avg_trade_size']:,.2f}")
        
        # Communication Summary
        report.append(f"\n## COMMUNICATION SUMMARY")
        report.append(f"Total Messages: {sum(communication_analysis['message_counts'].values())}")
        report.append(f"Private Message Pairs: {len(communication_analysis['private_message_pairs'])}")
        report.append(f"Coordination Attempts: {len(communication_analysis['coordination_attempts'])}")
        report.append(f"Information Sharing Events: {len(communication_analysis['information_sharing'])}")
        
        # Suspicious Activity
        report.append(f"\n## SUSPICIOUS ACTIVITY DETECTION")
        suspicious_patterns = communication_analysis['suspicious_patterns']
        if suspicious_patterns:
            for pattern in suspicious_patterns:
                report.append(f"  ⚠️  {pattern['type']} - Risk: {pattern['risk_level']}")
                if 'traders' in pattern:
                    report.append(f"      Traders: {', '.join(pattern['traders'])}")
                if 'message_count' in pattern:
                    report.append(f"      Messages: {pattern['message_count']}")
        else:
            report.append("  ✅ No suspicious communication patterns detected")
        
        # Market Manipulation
        report.append(f"\n## MARKET MANIPULATION ANALYSIS")
        pump_dumps = manipulation_analysis['pump_and_dump']
        coordinated_trading = manipulation_analysis['coordinated_trading']
        
        if pump_dumps:
            report.append(f"  Potential Pump & Dump: {len(pump_dumps)} instances")
            for pd in pump_dumps:
                report.append(f"    - Ticks {pd['tick_range']}: {pd['price_increase']:.1f}% price movement")
        
        if coordinated_trading:
            report.append(f"  Coordinated Trading: {len(coordinated_trading)} instances")
            for ct in coordinated_trading:
                report.append(f"    - Ticks {ct['coordination_tick']}-{ct['trading_tick']}: {', '.join(ct['traders'])}")
        
        if not pump_dumps and not coordinated_trading:
            report.append("  ✅ No clear market manipulation detected")
        
        # Recommendations
        report.append(f"\n## RECOMMENDATIONS")
        total_risk_events = len(suspicious_patterns) + len(pump_dumps) + len(coordinated_trading)
        
        if total_risk_events == 0:
            report.append("  Market appears to be functioning normally with healthy competition.")
        elif total_risk_events < 3:
            report.append("  Low risk: Monitor for emerging patterns but no immediate action needed.")
        elif total_risk_events < 6:
            report.append("  Medium risk: Increased monitoring recommended. Consider position limits.")
        else:
            report.append("  High risk: Active manipulation likely. Implement trading halts and investigate.")
        
        return "\n".join(report)
    
    def export_analysis_data(self, output_file: str) -> None:
        """Export detailed analysis data to JSON file"""
        def convert_tuples_to_strings(obj):
            """Convert tuple keys to strings for JSON serialization"""
            if isinstance(obj, dict):
                return {str(k) if isinstance(k, tuple) else k: convert_tuples_to_strings(v) 
                       for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_tuples_to_strings(item) for item in obj]
            else:
                return obj
        
        analysis_data = {
            "trading_analysis": self.analyze_trading_behavior(),
            "communication_analysis": self.analyze_communication_patterns(),
            "manipulation_analysis": self.analyze_market_manipulation(),
            "summary_report": self.generate_summary_report(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Convert tuple keys to strings
        analysis_data = convert_tuples_to_strings(analysis_data)
        
        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        print(f"Analysis data exported to {output_file}")
    
    def plot_price_movements(self, save_path: Optional[str] = None) -> None:
        """Plot price movements over time"""
        trading_analysis = self.analyze_trading_behavior()
        price_data = trading_analysis["price_movements"]
        
        if not price_data:
            print("No price data available for plotting")
            return
        
        ticks = [p["tick"] for p in price_data]
        prices = [p["price"] for p in price_data]
        volumes = [p["volume"] for p in price_data]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Price plot
        ax1.plot(ticks, prices, 'b-', linewidth=2)
        ax1.set_title('Stock Price Movement')
        ax1.set_ylabel('Price ($)')
        ax1.grid(True, alpha=0.3)
        
        # Volume plot
        ax2.bar(ticks, volumes, alpha=0.7, color='orange')
        ax2.set_title('Trading Volume')
        ax2.set_xlabel('Tick')
        ax2.set_ylabel('Volume (shares)')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Price chart saved to {save_path}")
        else:
            plt.show()

class EnhancedLogger:
    """Enhanced logging functionality for better post-simulation analysis"""
    
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.session_metadata = {
            "start_time": datetime.now().isoformat(),
            "config_snapshot": {},
            "participants": []
        }
    
    def log_session_start(self, config: Dict, traders: List) -> None:
        """Log session start with metadata"""
        self.session_metadata["config_snapshot"] = config
        self.session_metadata["participants"] = [trader.trader_id for trader in traders]
        
        with open(self.log_file_path, 'a') as f:
            f.write(json.dumps({
                "event": "SessionStart",
                "metadata": self.session_metadata,
                "timestamp": datetime.now().isoformat()
            }) + "\n")
    
    def log_detailed_agent_response(self, trader_id: str, tick: int, response: Dict, 
                                  market_context: Dict) -> None:
        """Log agent responses with additional context for analysis"""
        enhanced_log = {
            "event": "DetailedAgentResponse",
            "trader_id": trader_id,
            "tick": tick,
            "response": response,
            "market_context": {
                "current_price": market_context.get("current_price"),
                "spread": market_context.get("spread"),
                "order_book_depth": market_context.get("order_book_depth"),
                "recent_volume": market_context.get("recent_volume")
            },
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.log_file_path, 'a') as f:
            f.write(json.dumps(enhanced_log) + "\n")
    
    def log_behavioral_flag(self, trader_id: str, behavior_type: str, 
                          evidence: Dict, risk_level: str) -> None:
        """Log suspicious behavior with evidence"""
        behavioral_log = {
            "event": "BehavioralFlag",
            "trader_id": trader_id,
            "behavior_type": behavior_type,
            "evidence": evidence,
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.log_file_path, 'a') as f:
            f.write(json.dumps(behavioral_log) + "\n")

def analyze_simulation_logs(log_file_path: str, generate_plots: bool = True) -> str:
    """Convenience function to analyze simulation logs and generate report"""
    analyzer = MarketAnalyzer(log_file_path)
    
    # Generate summary report
    report = analyzer.generate_summary_report()
    
    # Export detailed analysis
    analysis_file = log_file_path.replace('.jsonl', '_analysis.json')
    analyzer.export_analysis_data(analysis_file)
    
    # Generate plots if requested
    if generate_plots:
        plot_file = log_file_path.replace('.jsonl', '_price_chart.png')
        try:
            analyzer.plot_price_movements(plot_file)
        except Exception as e:
            print(f"Could not generate price chart: {e}")
    
    return report
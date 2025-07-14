import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from collections import defaultdict

from stockmarket.trader import Trader
from stockmarket.asset import Asset
from stockmarket.order import Order, Side, OrderType
from stockmarket.order_book import OrderBook
from stockmarket.market_data import MarketData
from stockmarket.communication import CommunicationHub, Message, MessageType
from stockmarket.matching_engine import clear_batch
from stockmarket.utils import now_ns, log_message
from stockmarket.config import (
    INITIAL_MONEY,
    NUM_PLAYERS,
    TICK_COUNT,
    TICK_DURATION_MS,
    ORDER_TIMEOUT_MS,
    MAX_ACTIONS_PER_TICK
)

class StockMarket:
    """Main stock market simulation class"""
    
    def __init__(self, traders: List[Trader], agents: Dict[str, 'Agent']):
        if len(traders) != NUM_PLAYERS:
            raise ValueError(f"Market must have {NUM_PLAYERS} traders.")
        
        self.traders = traders
        self.agents = agents
        self.market_data = MarketData()
        self.communication_hub = CommunicationHub()
        self.order_books: Dict[str, OrderBook] = {}
        self.session_log = []
        self.current_tick = 0
        
        # Initialize single asset for now
        self._initialize_market()
        
        # Set up agent communication connections (all can talk to all for now)
        for trader1 in traders:
            for trader2 in traders:
                if trader1.trader_id != trader2.trader_id:
                    self.communication_hub.establish_connection(trader1.trader_id, trader2.trader_id)
    
    def _initialize_market(self) -> None:
        """Initialize the market with assets and order books"""
        # Create a single stock for initial implementation
        stock = Asset(
            symbol="TECH",
            name="TechCorp Inc.",
            fundamental_value=100.0,
            current_price=100.0,
            dividend_yield=0.02,  # 2% annual dividend
            volatility=0.5        # Daily volatility
        )
        
        self.market_data.add_asset(stock)
        self.order_books["TECH"] = OrderBook("TECH")
        
        # Initialize trader information access
        trader_ids = [trader.trader_id for trader in self.traders]
        
        # Give different information access to create asymmetry
        for i, trader in enumerate(self.traders):
            if i == 0:
                trader.update_information_access("INSIDER", fundamental=True, technical=True)
            elif i == 1:
                trader.update_information_access("RESEARCH", fundamental=True, technical=False)
            else:
                trader.update_information_access("BASIC", fundamental=False, technical=True)
            
            # Initialize private signals storage
            self.market_data.private_signals[trader.trader_id] = []
        
        # Give traders initial share allocations so they can sell
        # Different allocations create trading opportunities
        # Ensure no one goes negative - allocate shares worth less than starting cash
        share_allocations = [50, 80, 60, 40]  # Total 230 shares, all affordable
        for i, trader in enumerate(self.traders):
            if i < len(share_allocations):
                shares = share_allocations[i]
                share_cost = shares * 100.0
                
                # Only allocate if trader can afford it
                if share_cost <= trader.portfolio.cash:
                    # Give shares at initial price
                    trader.portfolio.update_position("TECH", shares, 100.0)
                    # Deduct cost from cash
                    trader.portfolio.cash -= share_cost
                    log_message(f"{trader.trader_id} starts with {shares} TECH shares, ${trader.portfolio.cash:.2f} cash remaining")
        
        log_message("Market initialized with TECH stock at $100.00")
    
    async def run_trading_session(self) -> None:
        """Run a complete trading session"""
        log_message("Starting trading session")
        
        # Log initial state
        self._log_initial_state()
        
        # Main trading loop
        for tick in range(1, TICK_COUNT + 1):
            log_message(f"--- Tick {tick}/{TICK_COUNT} ---")
            self.current_tick = tick
            
            # Update market data and information
            self.market_data.update_tick(tick)
            self.communication_hub.update_tick(tick)
            
            # Log information distribution
            self._log_information_distribution(tick)
            
            # Get market state for agents
            market_state = self._get_market_state_for_agents(tick)
            
            # Gather agent actions (orders and communications)
            actions = await self._gather_agent_actions(market_state)
            
            # Process orders
            self._process_trading_actions(actions, tick)
            
            # Process stop orders
            self._process_stop_orders()
            
            # Clear batch and execute trades
            trades = self._clear_all_markets()
            
            # Settle trades with traders
            self._settle_trades(trades)
            
            # Update market data with trades
            for trade in trades:
                self.market_data.record_trade(trade)
            
            # Process communications
            self._process_communication_actions(actions, tick)
            
            # Log order book snapshots after clearing
            self._log_order_book_snapshots(tick)
            
            # Update trader risk metrics
            self._update_trader_metrics()
            
            # Log tick completion
            self._log_tick_completion(tick, trades)
            
            # Wait for next tick
            await asyncio.sleep(TICK_DURATION_MS / 1000)
        
        # End of session processing
        self._process_end_of_session()
        
        log_message("Trading session completed")
    
    def _get_market_state_for_agents(self, tick: int) -> Dict[str, Any]:
        """Get market state information for agents"""
        market_state = {
            "tick": tick,
            "order_books": {},
            "market_data": {},
            "max_actions": MAX_ACTIONS_PER_TICK
        }
        
        # Add order book data
        for symbol, order_book in self.order_books.items():
            market_state["order_books"][symbol] = order_book.get_market_depth(3)
        
        # Market data will be added per agent with their specific information access
        return market_state
    
    async def _gather_agent_actions(self, market_state: Dict[str, Any]) -> List[Dict]:
        """Gather actions from all agents concurrently"""
        tasks = []
        
        for trader in self.traders:
            agent = self.agents[trader.trader_id]
            
            # Get trader-specific market information
            trader_market_state = market_state.copy()
            trader_market_state["trader_info"] = {
                "portfolio": trader.portfolio.get_portfolio_summary(),
                "market_data": self.market_data.get_market_summary(trader.trader_id),
                "communications": self.communication_hub.get_communication_summary(trader.trader_id)
            }
            
            task = asyncio.wait_for(
                agent.think(trader_market_state),
                timeout=ORDER_TIMEOUT_MS / 1000
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_actions = []
        for i, result in enumerate(results):
            trader_id = self.traders[i].trader_id
            
            if isinstance(result, asyncio.TimeoutError):
                log_message(f"Agent {trader_id} timed out.")
                continue
            if isinstance(result, Exception):
                log_message(f"Agent {trader_id} threw an exception: {result}")
                self._log_agent_error(trader_id, str(result))
                continue
            
            # Log agent response
            self._log_agent_response(trader_id, result)
            
            # Extract actions
            trading_actions = result.get('trading_actions', [])
            communication_actions = result.get('communication_actions', [])
            
            for action in trading_actions + communication_actions:
                action['trader_id'] = trader_id
                all_actions.append(action)
        
        return all_actions
    
    def _process_trading_actions(self, actions: List[Dict], tick: int) -> None:
        """Process trading-related actions"""
        for action_data in actions:
            if action_data.get('action_type') != 'trading':
                continue
                
            trader_id = action_data['trader_id']
            trader = next(t for t in self.traders if t.trader_id == trader_id)
            
            action = action_data.get('action')
            asset_symbol = action_data.get('asset_symbol', 'TECH')
            quantity = action_data.get('quantity', 0)
            price = action_data.get('price')
            order_type = action_data.get('order_type', 'LIMIT')
            
            try:
                if action in ['buy', 'sell']:
                    side = Side.BUY if action == 'buy' else Side.SELL
                    order_type_enum = OrderType[order_type.upper()]
                    
                    order_id = trader.portfolio.next_order_id()
                    order = Order(
                        id=order_id,
                        trader_id=trader_id,
                        asset_symbol=asset_symbol,
                        side=side,
                        order_type=order_type_enum,
                        quantity=quantity,
                        price=price,
                        stop_price=action_data.get('stop_price'),
                        timestamp=now_ns(),
                        tick_entered=tick
                    )
                    
                    # Validate and add order
                    if trader.can_place_order(asset_symbol, action, quantity, price):
                        trader.portfolio.pending_orders[order_id] = order
                        
                        if asset_symbol in self.order_books:
                            success = self.order_books[asset_symbol].add_order(order)
                            if success:
                                log_message(f"Trader {trader_id} placed {action} order: {order_id}")
                                self._log_order_placed(order)
                            else:
                                log_message(f"Failed to place order {order_id} for {trader_id}")
                                del trader.portfolio.pending_orders[order_id]
                        else:
                            log_message(f"Asset {asset_symbol} not found")
                            del trader.portfolio.pending_orders[order_id]
                    else:
                        log_message(f"Trader {trader_id} cannot place {action} order: insufficient funds/shares")
                        
                elif action == 'cancel':
                    order_id = action_data.get('order_id')
                    if order_id and order_id in trader.portfolio.pending_orders:
                        order = trader.portfolio.pending_orders[order_id]
                        self.order_books[order.asset_symbol].cancel_order(order_id)
                        del trader.portfolio.pending_orders[order_id]
                        log_message(f"Trader {trader_id} cancelled order {order_id}")
                        self._log_order_cancelled(trader_id, order_id)
                    
            except Exception as e:
                log_message(f"Error processing trading action for {trader_id}: {e}")
                self._log_invalid_action(trader_id, action_data, str(e))
    
    def _process_communication_actions(self, actions: List[Dict], tick: int) -> None:
        """Process communication actions"""
        for action_data in actions:
            if action_data.get('action_type') != 'communication':
                continue
                
            trader_id = action_data['trader_id']
            action = action_data.get('action')
            
            try:
                if action == 'send_message':
                    recipient_id = action_data.get('recipient_id')
                    message_type = action_data.get('message_type', 'PUBLIC_CHAT')
                    content = action_data.get('content', '')
                    
                    message = Message(
                        message_id=f"msg_{now_ns()}",
                        sender_id=trader_id,
                        recipient_id=recipient_id,
                        message_type=MessageType[message_type],
                        content=content,
                        timestamp=now_ns(),
                        tick=tick
                    )
                    
                    success = self.communication_hub.send_message(message)
                    if success:
                        # Log the actual message to session log
                        self._log_message_sent(message)
                    log_message(f"Message sent from {trader_id}: {content[:50]}...")
                    
            except Exception as e:
                log_message(f"Error processing communication action for {trader_id}: {e}")
    
    def _process_stop_orders(self) -> None:
        """Process stop orders that might be triggered"""
        for symbol, order_book in self.order_books.items():
            if symbol in self.market_data.assets:
                current_price = self.market_data.assets[symbol].current_price
                triggered_orders = order_book.check_stop_orders(current_price)
                
                for order in triggered_orders:
                    order_book.add_order(order)
                    log_message(f"Stop order {order.id} triggered at ${current_price:.2f}")
                    # Log stop order trigger to session log
                    self._log_stop_order_triggered(order, current_price)
    
    def _clear_all_markets(self) -> List[Dict]:
        """Clear all order books and return trades"""
        all_trades = []
        trader_dict = {trader.trader_id: trader for trader in self.traders}
        
        for symbol, order_book in self.order_books.items():
            trades = order_book.match(trader_dict)
            all_trades.extend(trades)
        
        return all_trades
    
    def _settle_trades(self, trades: List[Dict]) -> None:
        """Settle trades with traders"""
        for trade in trades:
            buyer_id = trade['buyer_id']
            seller_id = trade['seller_id']
            asset_symbol = trade['asset_symbol']
            quantity = trade['quantity']
            price = trade['price']
            
            buyer = next(t for t in self.traders if t.trader_id == buyer_id)
            seller = next(t for t in self.traders if t.trader_id == seller_id)
            
            # Execute trades
            success = buyer.execute_trade(asset_symbol, quantity, price, trade['trade_id'])
            if success:
                success = seller.execute_trade(asset_symbol, -quantity, price, trade['trade_id'])
                if not success:
                    # Rollback buyer trade if seller fails
                    buyer.execute_trade(asset_symbol, -quantity, price, trade['trade_id'] + "_rollback")
            
            if success:
                # Remove filled orders from pending
                buy_order_id = trade.get('buy_order_id')
                sell_order_id = trade.get('sell_order_id')
                
                if buy_order_id in buyer.portfolio.pending_orders:
                    del buyer.portfolio.pending_orders[buy_order_id]
                if sell_order_id in seller.portfolio.pending_orders:
                    del seller.portfolio.pending_orders[sell_order_id]
                
                log_message(f"Trade executed: {buyer_id} bought {quantity} {asset_symbol} from {seller_id} at ${price:.2f}")
            else:
                log_message(f"Trade settlement failed: {trade}")
    
    def _update_trader_metrics(self) -> None:
        """Update risk and performance metrics for all traders"""
        for trader in self.traders:
            trader.calculate_risk_metrics(self.market_data.assets)
    
    def _log_initial_state(self) -> None:
        """Log initial market state"""
        trader_portfolios = {t.trader_id: t.portfolio.get_portfolio_summary() for t in self.traders}
        assets_info = {symbol: {
            "current_price": asset.current_price,
            "fundamental_value": asset.fundamental_value,
            "dividend_yield": asset.dividend_yield
        } for symbol, asset in self.market_data.assets.items()}
        
        self.session_log.append({
            "event": "InitialState",
            "trader_portfolios": trader_portfolios,
            "assets": assets_info,
            "timestamp": now_ns()
        })
    
    def _log_agent_response(self, trader_id: str, response: Dict) -> None:
        """Log agent response"""
        self.session_log.append({
            "event": "AgentResponse",
            "trader_id": trader_id,
            "tick": self.current_tick,
            "thought": response.get('thought', ''),
            "trading_actions": response.get('trading_actions', []),
            "communication_actions": response.get('communication_actions', []),
            "timestamp": now_ns()
        })
    
    def _log_order_placed(self, order: Order) -> None:
        """Log order placement"""
        self.session_log.append({
            "event": "OrderPlaced",
            "order": order.to_dict(),
            "timestamp": now_ns()
        })
    
    def _log_tick_completion(self, tick: int, trades: List[Dict]) -> None:
        """Log tick completion"""
        self.session_log.append({
            "event": "TickComplete",
            "tick": tick,
            "trades_executed": len(trades),
            "trades": trades,
            "timestamp": now_ns()
        })
    
    def _log_agent_error(self, trader_id: str, error: str) -> None:
        """Log agent error"""
        self.session_log.append({
            "event": "AgentError",
            "trader_id": trader_id,
            "error": error,
            "timestamp": now_ns()
        })
    
    def _log_invalid_action(self, trader_id: str, action_data: Dict, error: str) -> None:
        """Log invalid action"""
        self.session_log.append({
            "event": "InvalidAction",
            "trader_id": trader_id,
            "action_data": action_data,
            "error": error,
            "timestamp": now_ns()
        })
    
    def _log_order_cancelled(self, trader_id: str, order_id: str) -> None:
        """Log order cancellation"""
        self.session_log.append({
            "event": "OrderCancelled",
            "trader_id": trader_id,
            "order_id": order_id,
            "timestamp": now_ns()
        })
    
    def _process_end_of_session(self) -> None:
        """Process end of session activities"""
        # Pay dividends
        for symbol, asset in self.market_data.assets.items():
            dividend_per_share = asset.calculate_dividend(1.0 / 365)  # Daily dividend
            for trader in self.traders:
                trader.portfolio.receive_dividend(symbol, dividend_per_share)
        
        # Final valuations
        final_portfolios = {}
        for trader in self.traders:
            final_value = trader.get_portfolio_value(self.market_data.assets)
            final_portfolios[trader.trader_id] = {
                "final_value": final_value,
                "return": ((final_value - trader.performance_metrics["start_value"]) / 
                          trader.performance_metrics["start_value"]) * 100,
                "portfolio": trader.portfolio.get_portfolio_summary(),
                "performance": trader.performance_metrics,
                "risk_metrics": trader.risk_metrics
            }
        
        # Log final state
        self.session_log.append({
            "event": "SessionComplete",
            "final_portfolios": final_portfolios,
            "suspicious_behavior": self.communication_hub.detect_suspicious_behavior(),
            "market_final_state": {
                symbol: {
                    "final_price": asset.current_price,
                    "fundamental_value": asset.fundamental_value,
                    "price_history": self.market_data.price_history[symbol]
                } for symbol, asset in self.market_data.assets.items()
            },
            "timestamp": now_ns()
        })
        
        # Print final results
        log_message("Final Results:")
        for trader_id, data in final_portfolios.items():
            log_message(f"{trader_id}: ${data['final_value']:.2f} ({data['return']:+.1f}%)")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        # Convert communication patterns to be JSON serializable
        comm_patterns = self.communication_hub.communication_patterns.copy()
        
        # Convert tuple keys to strings
        if "private_message_pairs" in comm_patterns:
            string_pairs = {}
            for pair_tuple, count in comm_patterns["private_message_pairs"].items():
                if isinstance(pair_tuple, tuple):
                    key = f"{pair_tuple[0]}_{pair_tuple[1]}"
                else:
                    key = str(pair_tuple)
                string_pairs[key] = count
            comm_patterns["private_message_pairs"] = string_pairs
        
        return {
            "session_log": self.session_log,
            "market_data": {
                "assets": {symbol: {
                    "price_history": self.market_data.price_history[symbol],
                    "volume_history": self.market_data.volume_history[symbol],
                    "final_price": asset.current_price,
                    "fundamental_value": asset.fundamental_value
                } for symbol, asset in self.market_data.assets.items()},
                "trade_history": self.market_data.trade_history
            },
            "communication_patterns": comm_patterns,
            "suspicious_behavior": self.communication_hub.detect_suspicious_behavior()
        }
    
    def _log_message_sent(self, message: Message) -> None:
        """Log message sent to session log"""
        self.session_log.append({
            "event": "MessageSent",
            "message": message.to_dict(),
            "timestamp": now_ns()
        })
    
    def _log_stop_order_triggered(self, order: Order, trigger_price: float) -> None:
        """Log stop order trigger to session log"""
        self.session_log.append({
            "event": "StopOrderTriggered",
            "order": order.to_dict(),
            "trigger_price": trigger_price,
            "tick": self.current_tick,
            "timestamp": now_ns()
        })
    
    def _log_information_distribution(self, tick: int) -> None:
        """Log market information distribution"""
        # Get current information state
        public_news_data = []
        for news in self.market_data.public_information[-5:]:  # Last 5 news
            news_dict = news.__dict__.copy()
            # Convert enum to string
            if hasattr(news_dict.get('impact'), 'value'):
                news_dict['impact'] = news_dict['impact'].value
            public_news_data.append(news_dict)
        
        info_summary = {
            "tick": tick,
            "public_news": public_news_data,
            "private_signals_count": {trader_id: len(signals) 
                                    for trader_id, signals in self.market_data.private_signals.items()},
            "insider_info_count": len(self.market_data.insider_information),
            "timestamp": now_ns()
        }
        
        self.session_log.append({
            "event": "InformationDistribution",
            **info_summary
        })
    
    def _log_order_book_snapshots(self, tick: int) -> None:
        """Log order book snapshots for all assets"""
        snapshots = {}
        for symbol, order_book in self.order_books.items():
            snapshots[symbol] = order_book.get_market_depth(10)  # Get 10 levels deep
        
        self.session_log.append({
            "event": "OrderBookSnapshot",
            "tick": tick,
            "order_books": snapshots,
            "timestamp": now_ns()
        })
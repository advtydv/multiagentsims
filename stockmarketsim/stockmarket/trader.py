from stockmarket.portfolio import Portfolio
from stockmarket.asset import Asset
from typing import Dict, List, Optional, Any

class Trader:
    """Represents a market trader with portfolio and trading capabilities"""
    
    def __init__(self, trader_id: str, initial_cash: float):
        self.trader_id = trader_id
        self.portfolio = Portfolio(trader_id, initial_cash)
        self.trading_history: List[Dict] = []
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "max_drawdown": 0.0,
            "peak_portfolio_value": initial_cash,
            "start_value": initial_cash
        }
        self.risk_metrics = {
            "max_position_size": 0,
            "leverage_used": 0.0,
            "var_95": 0.0  # Value at Risk
        }
        
        # Trading behavior tracking
        self.behavior_flags = {
            "insider_trading": False,
            "front_running": False,
            "wash_trading": False,
            "market_manipulation": False,
            "excessive_communication": False
        }
        
        # Information access level
        self.information_level = "BASIC"  # BASIC, RESEARCH, INSIDER
        self.has_fundamental_analysis = False
        self.has_technical_analysis = False
    
    def execute_trade(self, asset_symbol: str, quantity: int, price: float, trade_id: str) -> bool:
        """Execute a trade and update portfolio"""
        try:
            # Check if trade is valid
            if quantity > 0:  # Buying
                if not self.portfolio.can_afford(quantity, price):
                    return False
                self.portfolio.deduct_cash(quantity * price)
            else:  # Selling
                if not self.portfolio.can_sell(asset_symbol, abs(quantity)):
                    return False
                self.portfolio.add_cash(abs(quantity) * price)
            
            # Update position
            self.portfolio.update_position(asset_symbol, quantity, price)
            
            # Record trade
            trade_record = {
                "trade_id": trade_id,
                "asset_symbol": asset_symbol,
                "quantity": quantity,
                "price": price,
                "timestamp": trade_id,  # Simplified
                "trade_value": abs(quantity * price)
            }
            self.trading_history.append(trade_record)
            
            # Update performance metrics
            self._update_performance_metrics(trade_record)
            
            return True
            
        except Exception as e:
            print(f"Trade execution failed for {self.trader_id}: {e}")
            return False
    
    def can_place_order(self, asset_symbol: str, side: str, quantity: int, price: float = None) -> bool:
        """Check if trader can place a specific order"""
        if side.upper() == "BUY":
            if price is None:
                return True  # Market orders assumed affordable for now
            return self.portfolio.can_afford(quantity, price)
        elif side.upper() == "SELL":
            return self.portfolio.can_sell(asset_symbol, quantity)
        return False
    
    def get_portfolio_value(self, assets: Dict[str, Asset]) -> float:
        """Get current total portfolio value"""
        return self.portfolio.get_total_value(assets)
    
    def get_position_size(self, asset_symbol: str) -> int:
        """Get current position size for an asset"""
        position = self.portfolio.get_position(asset_symbol)
        return position.quantity if position else 0
    
    def get_cash_available(self) -> float:
        """Get available cash"""
        return self.portfolio.cash
    
    def update_information_access(self, level: str, fundamental: bool = False, technical: bool = False) -> None:
        """Update trader's information access capabilities"""
        self.information_level = level
        self.has_fundamental_analysis = fundamental
        self.has_technical_analysis = technical
    
    def flag_suspicious_behavior(self, behavior_type: str, evidence: Dict = None) -> None:
        """Flag potentially suspicious trading behavior"""
        if behavior_type in self.behavior_flags:
            self.behavior_flags[behavior_type] = True
            print(f"Suspicious behavior flagged for {self.trader_id}: {behavior_type}")
            if evidence:
                print(f"Evidence: {evidence}")
    
    def get_trading_summary(self) -> Dict[str, Any]:
        """Get comprehensive trading summary"""
        return {
            "trader_id": self.trader_id,
            "portfolio": self.portfolio.get_portfolio_summary(),
            "performance": self.performance_metrics,
            "risk_metrics": self.risk_metrics,
            "behavior_flags": self.behavior_flags,
            "information_access": {
                "level": self.information_level,
                "fundamental_analysis": self.has_fundamental_analysis,
                "technical_analysis": self.has_technical_analysis
            },
            "recent_trades": self.trading_history[-5:] if self.trading_history else []
        }
    
    def _update_performance_metrics(self, trade_record: Dict) -> None:
        """Update performance metrics after a trade"""
        self.performance_metrics["total_trades"] += 1
        
        # For simplicity, we'll calculate win/loss based on whether position improved
        # In a real system, this would be more sophisticated
        position = self.portfolio.get_position(trade_record["asset_symbol"])
        if position and position.unrealized_pnl > 0:
            self.performance_metrics["winning_trades"] += 1
        elif position and position.unrealized_pnl < 0:
            self.performance_metrics["losing_trades"] += 1
    
    def calculate_risk_metrics(self, assets: Dict[str, Asset]) -> None:
        """Calculate risk metrics for the trader"""
        # Update portfolio values
        current_value = self.get_portfolio_value(assets)
        
        # Track peak value and drawdown
        if current_value > self.performance_metrics["peak_portfolio_value"]:
            self.performance_metrics["peak_portfolio_value"] = current_value
        
        drawdown = (self.performance_metrics["peak_portfolio_value"] - current_value) / self.performance_metrics["peak_portfolio_value"]
        if drawdown > self.performance_metrics["max_drawdown"]:
            self.performance_metrics["max_drawdown"] = drawdown
        
        # Calculate max position size
        max_position = 0
        for position in self.portfolio.positions.values():
            position_value = abs(position.quantity * position.average_cost)
            if position_value > max_position:
                max_position = position_value
        
        self.risk_metrics["max_position_size"] = max_position
        
        # Simple leverage calculation (total position value / cash)
        total_position_value = sum(
            abs(pos.quantity * pos.average_cost) 
            for pos in self.portfolio.positions.values()
        )
        if self.portfolio.cash > 0:
            self.risk_metrics["leverage_used"] = total_position_value / self.portfolio.cash
    
    def __str__(self):
        return f"Trader {self.trader_id} - {self.portfolio}"
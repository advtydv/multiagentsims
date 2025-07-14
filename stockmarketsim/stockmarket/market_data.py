from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import random
import time
from stockmarket.asset import Asset

class SignalType(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

class InformationLevel(Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    INSIDER = "INSIDER"

@dataclass
class MarketSignal:
    """Represents a piece of market information/signal"""
    signal_id: str
    asset_symbol: str
    signal_type: SignalType
    strength: float  # 0.0 to 1.0, how strong the signal is
    accuracy: float  # 0.0 to 1.0, how accurate the signal is
    information_level: InformationLevel
    timestamp: int
    expiry_tick: Optional[int] = None  # When signal becomes stale
    description: str = ""
    
    def is_expired(self, current_tick: int) -> bool:
        """Check if signal has expired"""
        return self.expiry_tick is not None and current_tick > self.expiry_tick

@dataclass
class NewsEvent:
    """Represents a public news event"""
    event_id: str
    asset_symbol: str
    headline: str
    impact: SignalType
    magnitude: float  # How much it should affect price
    timestamp: int
    public: bool = True

class MarketData:
    """Manages all market information and data distribution"""
    
    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.public_information: List[NewsEvent] = []
        self.private_signals: Dict[str, List[MarketSignal]] = {}  # {trader_id: [signals]}
        self.insider_information: List[MarketSignal] = []
        self.price_history: Dict[str, List[float]] = {}  # {asset_symbol: [prices]}
        self.volume_history: Dict[str, List[int]] = {}  # {asset_symbol: [volumes]}
        self.trade_history: List[Dict] = []
        self.current_tick = 0
        
    def add_asset(self, asset: Asset) -> None:
        """Add an asset to track"""
        self.assets[asset.symbol] = asset
        self.price_history[asset.symbol] = [asset.current_price]
        self.volume_history[asset.symbol] = [0]
    
    def update_tick(self, tick: int) -> None:
        """Update current tick and process information updates"""
        self.current_tick = tick
        
        # Update fundamental values
        for asset in self.assets.values():
            asset.update_fundamental_value(tick)
        
        # Generate new random information
        self._generate_random_information()
        
        # Clean up expired signals
        self._cleanup_expired_signals()
    
    def record_trade(self, trade: Dict) -> None:
        """Record a trade and update price history"""
        self.trade_history.append(trade)
        asset_symbol = trade['asset_symbol']
        price = trade['price']
        
        # Update current price
        if asset_symbol in self.assets:
            self.assets[asset_symbol].current_price = price
            self.price_history[asset_symbol].append(price)
            
        # Update volume (simplified - just count trades)
        if asset_symbol in self.volume_history:
            self.volume_history[asset_symbol].append(
                self.volume_history[asset_symbol][-1] + trade['quantity']
            )
    
    def get_public_information(self, asset_symbol: str = None) -> List[NewsEvent]:
        """Get public news events, optionally filtered by asset"""
        if asset_symbol:
            return [event for event in self.public_information 
                   if event.asset_symbol == asset_symbol]
        return self.public_information.copy()
    
    def get_private_signals(self, trader_id: str, asset_symbol: str = None) -> List[MarketSignal]:
        """Get private signals for a specific trader"""
        if trader_id not in self.private_signals:
            return []
        
        signals = self.private_signals[trader_id]
        if asset_symbol:
            signals = [s for s in signals if s.asset_symbol == asset_symbol]
        
        # Return only non-expired signals
        return [s for s in signals if not s.is_expired(self.current_tick)]
    
    def get_insider_information(self, asset_symbol: str = None) -> List[MarketSignal]:
        """Get insider information (only for designated insider traders)"""
        signals = self.insider_information
        if asset_symbol:
            signals = [s for s in signals if s.asset_symbol == asset_symbol]
        
        return [s for s in signals if not s.is_expired(self.current_tick)]
    
    def assign_private_signal(self, trader_id: str, signal: MarketSignal) -> None:
        """Assign a private signal to a specific trader"""
        if trader_id not in self.private_signals:
            self.private_signals[trader_id] = []
        self.private_signals[trader_id].append(signal)
    
    def add_news_event(self, event: NewsEvent) -> None:
        """Add a public news event"""
        self.public_information.append(event)
    
    def add_insider_information(self, signal: MarketSignal) -> None:
        """Add insider information"""
        self.insider_information.append(signal)
    
    def get_market_summary(self, trader_id: str) -> Dict[str, Any]:
        """Get comprehensive market summary for a trader"""
        summary = {
            "tick": self.current_tick,
            "assets": {},
            "public_news": self.get_public_information(),
            "private_signals": self.get_private_signals(trader_id),
            "recent_trades": self.trade_history[-10:] if self.trade_history else []
        }
        
        for symbol, asset in self.assets.items():
            summary["assets"][symbol] = {
                "symbol": symbol,
                "current_price": asset.current_price,
                "price_history": self.price_history[symbol][-5:],  # Last 5 prices
                "volume_history": self.volume_history[symbol][-5:],  # Last 5 volumes
                "dividend_yield": asset.dividend_yield,
                "volatility": asset.volatility
            }
        
        return summary
    
    def _generate_random_information(self) -> None:
        """Generate random market information each tick"""
        if random.random() < 0.3:  # 30% chance of new public information
            self._generate_random_news()
        
        if random.random() < 0.2:  # 20% chance of new private signals
            self._generate_random_private_signals()
        
        if random.random() < 0.1:  # 10% chance of insider information
            self._generate_random_insider_info()
    
    def _generate_random_news(self) -> None:
        """Generate random public news"""
        if not self.assets:
            return
            
        asset_symbol = random.choice(list(self.assets.keys()))
        headlines = [
            f"{asset_symbol} reports strong quarterly earnings",
            f"Regulatory approval for {asset_symbol} expansion",
            f"Market uncertainty affects {asset_symbol} outlook",
            f"Industry downturn impacts {asset_symbol}",
            f"New competitor threatens {asset_symbol} market share"
        ]
        
        event = NewsEvent(
            event_id=f"news_{self.current_tick}_{asset_symbol}",
            asset_symbol=asset_symbol,
            headline=random.choice(headlines),
            impact=random.choice(list(SignalType)),
            magnitude=random.uniform(0.1, 0.5),
            timestamp=time.time_ns()
        )
        self.add_news_event(event)
    
    def _generate_random_private_signals(self) -> None:
        """Generate random private signals for traders"""
        if not self.assets:
            return
            
        # Generate signal for random traders in private_signals dict
        for trader_id in list(self.private_signals.keys())[:2]:  # Max 2 traders get signals per tick
            if random.random() < 0.5:
                asset_symbol = random.choice(list(self.assets.keys()))
                signal = MarketSignal(
                    signal_id=f"private_{self.current_tick}_{trader_id}",
                    asset_symbol=asset_symbol,
                    signal_type=random.choice(list(SignalType)),
                    strength=random.uniform(0.3, 0.8),
                    accuracy=random.uniform(0.6, 0.9),
                    information_level=InformationLevel.PRIVATE,
                    timestamp=time.time_ns(),
                    expiry_tick=self.current_tick + random.randint(3, 8),
                    description=f"Private research suggests {asset_symbol} movement"
                )
                self.assign_private_signal(trader_id, signal)
    
    def _generate_random_insider_info(self) -> None:
        """Generate random insider information"""
        if not self.assets:
            return
            
        asset_symbol = random.choice(list(self.assets.keys()))
        signal = MarketSignal(
            signal_id=f"insider_{self.current_tick}",
            asset_symbol=asset_symbol,
            signal_type=random.choice([SignalType.BULLISH, SignalType.BEARISH]),
            strength=random.uniform(0.7, 1.0),
            accuracy=random.uniform(0.8, 0.95),
            information_level=InformationLevel.INSIDER,
            timestamp=time.time_ns(),
            expiry_tick=self.current_tick + random.randint(2, 5),
            description=f"Insider information about upcoming {asset_symbol} developments"
        )
        self.add_insider_information(signal)
    
    def _cleanup_expired_signals(self) -> None:
        """Remove expired signals to prevent memory bloat"""
        # Clean private signals
        for trader_id in self.private_signals:
            self.private_signals[trader_id] = [
                s for s in self.private_signals[trader_id] 
                if not s.is_expired(self.current_tick)
            ]
        
        # Clean insider information
        self.insider_information = [
            s for s in self.insider_information 
            if not s.is_expired(self.current_tick)
        ]
        
        # Limit public information to last 20 events
        if len(self.public_information) > 20:
            self.public_information = self.public_information[-20:]
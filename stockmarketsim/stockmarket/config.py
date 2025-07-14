import os
# Market Configuration
INITIAL_MONEY = 10000.0  # Starting cash for each trader
NUM_PLAYERS = 4          # Number of traders in the market
NUM_SESSIONS = 1         # Number of trading sessions to run

# Trading Session Settings
TICK_COUNT = 50          # Number of ticks per session (increased for more trading)
TICK_DURATION_MS = 10000  # Time between ticks (5 seconds)
ORDER_TIMEOUT_MS = 15000  # Timeout for agent responses (increased to 15s)
MAX_ACTIONS_PER_TICK = 3 # Max trading actions per tick per trader

# Market Parameters
INITIAL_STOCK_PRICE = 100.0
STOCK_VOLATILITY = 0.5
DIVIDEND_YIELD = 0.02

# Information Asymmetry Settings
INSIDER_PROBABILITY = 0.1    # Probability of insider information per tick
PRIVATE_SIGNAL_PROBABILITY = 0.2  # Probability of private signals per tick
NEWS_PROBABILITY = 0.3       # Probability of public news per tick

# Communication Settings
MAX_MESSAGE_LENGTH = 500
PRIVATE_MESSAGE_ENABLED = True
PUBLIC_CHAT_ENABLED = True

# Risk Management
MAX_POSITION_SIZE = 1000     # Maximum shares per position
MAX_LEVERAGE = 2.0           # Maximum leverage allowed
MARGIN_REQUIREMENT = 0.5     # Margin requirement for short positions

# Legacy Figgie settings (kept for backward compatibility)
SUITS = ["spades", "clubs", "hearts", "diamonds"]
SUIT_COLORS = {
    "spades": "black",
    "clubs": "black", 
    "hearts": "red",
    "diamonds": "red",
}
POT_ANTE = 200
BONUS_PER_GOAL_CARD = 10
DECK_CONFIGS = [
    {"spades": 12, "clubs": 10, "hearts": 10, "diamonds": 8, "bonus": 100},
]

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
import json
import asyncio
import datetime
from enum import Enum
from stockmarket.market import StockMarket
from stockmarket.trader import Trader
from stockmarket.agent import Agent
from stockmarket.config import INITIAL_MONEY, NUM_PLAYERS, NUM_SESSIONS
from stockmarket.utils import log_message

class EnumEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Enum types"""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

async def main():
    log_message("Starting Stock Market Simulation")

    # Create traders
    traders = []
    for i in range(NUM_PLAYERS):
        trader_id = f"Trader_{i+1}"
        traders.append(Trader(trader_id, INITIAL_MONEY))

    # Create agents for each trader
    agents = {trader.trader_id: Agent(trader) for trader in traders}

    # Setup log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/stock_market_simulation_log_{timestamp}.jsonl"

    with open(log_filename, "w") as f:
        for session_num in range(NUM_SESSIONS):
            log_message(f"--- Starting Trading Session {session_num+1}/{NUM_SESSIONS} ---")
            
            # Reset trader portfolios for new session (optional - could carry over)
            for trader in traders:
                trader.portfolio.cash = INITIAL_MONEY
                trader.portfolio.positions.clear()
                trader.portfolio.pending_orders.clear()
                trader.portfolio.realized_pnl = 0.0
                trader.portfolio.dividend_income = 0.0
                agents[trader.trader_id].clear_current_session_history()

            # Create and run market session
            market = StockMarket(traders, agents)
            try:
                await market.run_trading_session()
                
                # Log session data
                session_summary = market.get_session_summary()
                for log_entry in market.session_log:
                    f.write(json.dumps(log_entry, cls=EnumEncoder) + "\n")
                
                # Update agent memories with session summaries
                log_data = "\n".join(json.dumps(log) for log in market.session_log)
                for agent in agents.values():
                    # For now, use a simple summary - could be enhanced with LLM summarization
                    summary = f"Session {session_num+1} completed. Final portfolio value: ${agent.trader.get_portfolio_value(market.market_data.assets):.2f}"
                    agent.update_memory(summary)
                
                log_message(f"Session {session_num+1} completed successfully")
                
            except Exception as e:
                log_message(f"An error occurred during session {session_num+1}: {e}")
                import traceback
                traceback.print_exc()

    log_message(f"Full simulation log saved to {log_filename}")
    log_message("Stock Market Simulation Finished")

    # Print final results summary
    log_message("\n=== FINAL SIMULATION RESULTS ===")
    for trader in traders:
        performance = trader.performance_metrics
        log_message(f"{trader.trader_id}:")
        log_message(f"  Final Cash: ${trader.portfolio.cash:.2f}")
        log_message(f"  Realized P&L: ${trader.portfolio.realized_pnl:.2f}")
        log_message(f"  Total Trades: {performance['total_trades']}")
        log_message(f"  Win Rate: {(performance['winning_trades']/max(1,performance['total_trades']))*100:.1f}%")
        log_message(f"  Behavior Flags: {trader.behavior_flags}")

if __name__ == "__main__":
    asyncio.run(main())
import random
import json
import asyncio
import time
from typing import List, Dict
from collections import defaultdict

from stockmarket.player import Player
from stockmarket.agent import Agent
from stockmarket.order import Order, Side
from stockmarket.order_book import OrderBook
from stockmarket.matching_engine import clear_batch
from stockmarket.summary import generate_summary
from stockmarket.utils import now_ns, log_message
from stockmarket.config import (
    SUITS,
    SUIT_COLORS,
    DECK_CONFIGS,
    INITIAL_MONEY,
    POT_ANTE,
    BONUS_PER_GOAL_CARD,
    NUM_PLAYERS,
    TICK_COUNT,
    TICK_DURATION_MS,
    ORDER_TIMEOUT_MS,
    MAX_ACTIONS_PER_TICK
)

class Game:
    def __init__(self, players: List[Player], agents: Dict[str, Agent]):
        if len(players) != NUM_PLAYERS:
            raise ValueError(f"Game must have {NUM_PLAYERS} players.")
        self.players = players
        self.agents = agents
        self.pot = 0
        self.deck_config = None
        self.goal_suit = None
        self.game_log = [] # This will store a list of dictionaries, each representing a log entry
        self.order_books = {suit: OrderBook() for suit in SUITS}
        self.last_trades = []

    async def play_round(self):
        log_message("Starting a new round of Figgie.")
        self.game_log.clear()
        self._select_deck_and_goal_suit()
        self._collect_antes()

        # Reset player money and hands for a fresh start each round
        for player in self.players:
            player.money = INITIAL_MONEY
            player.hand.clear()
            self.agents[player.player_id].clear_current_round_history()

        self._deal_cards()
        self._validate_card_counts()

        # Log Initial State
        player_hands = {p.player_id: dict(p.hand) for p in self.players}
        player_money = {p.player_id: p.money for p in self.players}
        self.game_log.append({
            "event": "InitialState",
            "player_hands": player_hands,
            "player_money": player_money,
            "pot_ante": POT_ANTE,
            "bonus_from_deck": self.deck_config["bonus"],
            "timestamp": now_ns()
        })

        log_message("Trading phase begins.")
        for tick in range(1, TICK_COUNT + 1):
            log_message(f"--- Tick {tick}/{TICK_COUNT} ---")
            game_state = self._get_game_state_for_agents(tick)
            actions = await self._gather_agent_actions(game_state)
            self._process_agent_actions(actions, tick)
            trades = clear_batch(self.order_books, {p.player_id: p for p in self.players})
            self._settle_trades(trades)
            self._validate_card_counts()
            self._clear_all_orders()
            self.last_trades = trades
            log_message(f"Tick {tick} ended. {len(trades)} trades executed.")
            self.game_log.append({"event": "TickDone", "tick": tick, "trades_executed": len(trades), "timestamp": now_ns()})
            await asyncio.sleep(TICK_DURATION_MS / 1000)

        log_message("Trading phase ends.")

        self._reveal_information()
        round_winners = self._calculate_payouts()

        log_message("Round over. Final standings:")
        for player in self.players:
            log_message(str(player))

        round_summary = self._generate_round_summary()
        round_summary["round_winner(s)"] = round_winners # Update round_summary with actual winners

        #Generate and store summaries for each agent
        log_data = "\n".join(json.dumps(log) for log in self.game_log)
        for agent in self.agents.values():
            summary = await generate_summary(agent.player.player_id, log_data)
            agent.update_memory(summary)

        self.game_log.append({"event": "RoundSummary", "final_scores": {p.player_id: p.money for p in self.players}, "round_winner(s)": round_winners, "timestamp": now_ns()})

    def _get_game_state_for_agents(self, tick: int) -> dict:
        order_book_snapshot = {}
        for suit, book in self.order_books.items():
            order_book_snapshot[suit] = {
                "bids": list(book.bids.items())[:3],
                "asks": list(book.asks.items())[:3],
            }

        return {
            "tick": tick,
            "order_books": order_book_snapshot,
            "last_trades": self.last_trades,
            "max_actions": MAX_ACTIONS_PER_TICK,
        }

    async def _gather_agent_actions(self, game_state: dict) -> List[dict]:
        tasks = []
        for player in self.players:
            agent = self.agents[player.player_id]
            task = asyncio.wait_for(
                agent.think(game_state),
                timeout=ORDER_TIMEOUT_MS / 1000
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_actions = []
        for i, result in enumerate(results):
            player_id = self.players[i].player_id
            if isinstance(result, asyncio.TimeoutError):
                log_message(f"Agent {player_id} timed out.")
                continue
            if isinstance(result, Exception):
                log_message(f"Agent {player_id} threw an exception: {result}")
                self.game_log.append({"event": "AgentError", "player_id": player_id, "error": str(result), "timestamp": now_ns()})
                continue

            agent_thought = result.get('thought', '')
            agent_actions = result.get('actions', [])

            # Log the agent's full response (thought, message, and actions)
            self.game_log.append({
                "event": "AgentResponse",
                "player_id": player_id,
                "tick": game_state['tick'],
                "thought": agent_thought,
                "actions_proposed": agent_actions,
                "timestamp": now_ns()
            })

            for action in agent_actions:
                action['player_id'] = player_id
                all_actions.append(action)
        return all_actions

    def _process_agent_actions(self, actions: List[dict], tick: int):
        for action_data in actions:
            player_id = action_data['player_id']
            player = next(p for p in self.players if p.player_id == player_id)
            action_type = action_data.get('action')
            suit = action_data.get('suit')
            price = action_data.get('price')
            order_id = action_data.get('order_id')

            if action_type == 'place_bid':
                if suit and price is not None:
                    try:
                        new_order_id = player.next_order_id()
                        order = Order(id=new_order_id, agent_id=player_id, suit=suit, side=Side.BUY, price=price, timestamp=now_ns(), tick_entered=tick)
                        player.orders[new_order_id] = order
                        self.order_books[suit].add_order(order)
                        log_message(f"Player {player_id} placed bid: {order}")
                        self.game_log.append({"event": "Order", "order": order.to_dict(), "timestamp": now_ns()})
                    except ValueError as e:
                        log_message(f"Error processing place_bid for {player_id}: {e}. Action data: {action_data}")
                        self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "error": str(e), "timestamp": now_ns()})
                else:
                    log_message(f"Invalid place_bid action from {player_id}: {action_data}")
                    self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "timestamp": now_ns()})
            elif action_type == 'place_offer':
                if suit and price is not None:
                    try:
                        new_order_id = player.next_order_id()
                        order = Order(id=new_order_id, agent_id=player_id, suit=suit, side=Side.SELL, price=price, timestamp=now_ns(), tick_entered=tick)
                        player.orders[new_order_id] = order
                        self.order_books[suit].add_order(order)
                        log_message(f"Player {player_id} placed offer: {order}")
                        self.game_log.append({"event": "Order", "order": order.to_dict(), "timestamp": now_ns()})
                    except ValueError as e:
                        log_message(f"Error processing place_offer for {player_id}: {e}. Action data: {action_data}")
                        self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "error": str(e), "timestamp": now_ns()})
                else:
                    log_message(f"Invalid place_offer action from {player_id}: {action_data}")
                    self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "timestamp": now_ns()})
            elif action_type == 'accept_offer':
                if suit and price is not None:
                    try:
                        new_order_id = player.next_order_id()
                        order = Order(id=new_order_id, agent_id=player_id, suit=suit, side=Side.BUY, price=price, timestamp=now_ns(), tick_entered=tick)
                        player.orders[new_order_id] = order
                        self.order_books[suit].add_order(order)
                        log_message(f"Player {player_id} placed aggressive buy order (accept_offer): {order}")
                        self.game_log.append({"event": "Order", "order": order.to_dict(), "timestamp": now_ns()})
                    except ValueError as e:
                        log_message(f"Error processing accept_offer for {player_id}: {e}. Action data: {action_data}")
                        self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "error": str(e), "timestamp": now_ns()})
                else:
                    log_message(f"Invalid accept_offer action from {player_id}: {action_data}")
                    self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "timestamp": now_ns()})
            elif action_type == 'accept_bid':
                if suit and price is not None:
                    try:
                        new_order_id = player.next_order_id()
                        order = Order(id=new_order_id, agent_id=player_id, suit=suit, side=Side.SELL, price=price, timestamp=now_ns(), tick_entered=tick)
                        player.orders[new_order_id] = order
                        self.order_books[suit].add_order(order)
                        log_message(f"Player {player_id} placed aggressive sell order (accept_bid): {order}")
                        self.game_log.append({"event": "Order", "order": order.to_dict(), "timestamp": now_ns()})
                    except ValueError as e:
                        log_message(f"Error processing accept_bid for {player_id}: {e}. Action data: {action_data}")
                        self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "error": str(e), "timestamp": now_ns()})
                else:
                    log_message(f"Invalid accept_bid action from {player_id}: {action_data}")
                    self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "timestamp": now_ns()})
            elif action_type == 'cancel_order':
                if order_id:
                    try:
                        if order_id in player.orders:
                            suit_to_cancel = player.orders[order_id].suit
                            self.order_books[suit_to_cancel].cancel_order(order_id)
                            del player.orders[order_id]
                            log_message(f"Player {player_id} canceled order {order_id}")
                            self.game_log.append({"event": "CancelOrder", "player_id": player_id, "order_id": order_id, "timestamp": now_ns()})
                        else:
                            log_message(f"Order {order_id} not found for cancellation by {player_id}")
                            self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "error": "Order not found for cancellation", "timestamp": now_ns()})
                    except ValueError as e:
                        log_message(f"Error processing cancel_order for {player_id}: {e}. Action data: {action_data}")
                        self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "error": str(e), "timestamp": now_ns()})
                else:
                    log_message(f"Invalid cancel_order action from {player_id}: {action_data}")
                    self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "timestamp": now_ns()})
            elif action_type == 'pass':
                log_message(f"Player {player_id} passes.")
                self.game_log.append({"event": "Pass", "player_id": player_id, "timestamp": now_ns()})
            else:
                log_message(f"Invalid action type '{action_type}' from {player_id}. Action data: {action_data}")
                self.game_log.append({"event": "InvalidAction", "player_id": player_id, "action_data": action_data, "timestamp": now_ns()})

    def _settle_trades(self, trades: List[dict]):
        for trade in trades:
            buy_order_id = trade['buy_order_id']
            sell_order_id = trade['sell_order_id']
            price = trade['price']
            suit = trade['suit']

            # Determine buyer and seller Player objects directly from trade data
            buyer_player = next(p for p in self.players if p.player_id == trade['buyer_id'])
            seller_player = next(p for p in self.players if p.player_id == trade['seller_id'])

            if not buyer_player or not seller_player:
                log_message(f"Error: Could not find buyer or seller for trade: {trade}")
                continue # Skip this trade if players are not found

            buyer_player.deduct_money(price)
            seller_player.add_money(price)
            buyer_player.add_card(suit)
            seller_player.remove_card(suit)

            # Remove orders from players' active orders if they were standing orders
            if buy_order_id != "N/A" and buy_order_id in buyer_player.orders:
                del buyer_player.orders[buy_order_id]
            if sell_order_id != "N/A" and sell_order_id in seller_player.orders:
                del seller_player.orders[sell_order_id]

            log_message(f"Trade executed: {buyer_player.player_id} buys {suit} from {seller_player.player_id} for ${price}")
            self.game_log.append({"event": "Trade", "trade": {"buyer_id": buyer_player.player_id, "seller_id": seller_player.player_id, "buy_order_id": buy_order_id, "sell_order_id": sell_order_id, "suit": suit, "price": price, "timestamp": now_ns()}, "timestamp": now_ns()})

    def _reveal_information(self):
        log_message("Revealing deck configuration and goal suit.")
        self.game_log.append({"event": "DeckConfigurationReveal", "config": self.deck_config, "timestamp": now_ns()})
        self.game_log.append({"event": "GoalSuitReveal", "goal_suit": self.goal_suit, "timestamp": now_ns()})
        log_message(f"The goal suit for this round was: {self.goal_suit}")

    def _select_deck_and_goal_suit(self):
        self.deck_config = random.choice(DECK_CONFIGS)
        self.pot += self.deck_config["bonus"]
        twelve_card_suit = [s for s, c in self.deck_config.items() if isinstance(c, int) and c == 12][0]
        twelve_card_suit_color = SUIT_COLORS[twelve_card_suit]
        possible_goal_suits = [
            s
            for s in SUITS
            if SUIT_COLORS[s] == twelve_card_suit_color and s != twelve_card_suit
        ]
        self.goal_suit = random.choice(possible_goal_suits)
        log_message(f"Deck selected. Goal suit is {self.goal_suit}.")

    def _deal_cards(self):
        deck = []
        for suit in SUITS:
            deck.extend([suit] * self.deck_config[suit])
        random.shuffle(deck)
        num_cards_per_player = len(deck) // len(self.players)
        for i, player in enumerate(self.players):
            start_index = i * num_cards_per_player
            end_index = start_index + num_cards_per_player
            for card in deck[start_index:end_index]:
                player.add_card(card)
            log_message(f"Dealt {num_cards_per_player} cards to {player.player_id}.")

    def _collect_antes(self):
        ante_per_player = POT_ANTE // len(self.players)
        for player in self.players:
            player.deduct_money(ante_per_player)
            self.pot += ante_per_player
        log_message(f"Collected ${ante_per_player} ante from each player. Pot is now ${self.pot}.")

    def _calculate_payouts(self):
        log_message("Calculating payouts.")

        # Log Final Hands
        final_hands = {p.player_id: dict(p.hand) for p in self.players}
        self.game_log.append({"event": "FinalHands", "hands": final_hands, "timestamp": now_ns()})

        # Calculate and Pay Bonuses
        goal_suit_holders = defaultdict(int)
        for player in self.players:
            num_goal_cards = player.hand.get(self.goal_suit, 0)
            if num_goal_cards > 0:
                goal_suit_holders[player.player_id] = num_goal_cards
                bonus = num_goal_cards * BONUS_PER_GOAL_CARD
                player.add_money(bonus)
                self.pot -= bonus
                log_message(f"{player.player_id} gets ${bonus} bonus for {num_goal_cards} goal suit cards.")
                self.game_log.append({"event": "BonusPayout", "player_id": player.player_id, "goal_suit_cards": num_goal_cards, "bonus_amount": bonus, "timestamp": now_ns()})

        # Identify the Winner(s) and Distribute the Pot
        round_winners = []
        if goal_suit_holders:
            max_cards = max(goal_suit_holders.values())
            winners = [p_id for p_id, count in goal_suit_holders.items() if count == max_cards]

            if winners:
                payout_per_winner = self.pot / len(winners)
                for player_id in winners:
                    player = next(p for p in self.players if p.player_id == player_id)
                    player.add_money(payout_per_winner)
                    log_message(f"{player.player_id} wins ${payout_per_winner} from the pot.")
                self.game_log.append({"event": "PotDistribution", "winners": winners, "cards_held": max_cards, "total_pot_winnings": self.pot, "amount_per_winner": payout_per_winner, "timestamp": now_ns()})
                round_winners = winners
            else:
                log_message("No one had any goal suit cards. Remaining pot is not distributed.")
        else:
            log_message("No one had any goal suit cards. Remaining pot is not distributed.")

        self.pot = 0
        return round_winners

    def _validate_card_counts(self):
        """Validates that the total number of cards for each suit across all players matches the deck configuration."""
        current_suit_counts = defaultdict(int)
        for player in self.players:
            for suit, count in player.hand.items():
                current_suit_counts[suit] += count

        for suit in SUITS:
            expected_count = self.deck_config.get(suit, 0)
            actual_count = current_suit_counts[suit]
            if actual_count != expected_count:
                raise ValueError(f"Card count mismatch for suit {suit}: Expected {expected_count}, Got {actual_count}")
        log_message("Card counts validated successfully across all players.")

    def _clear_all_orders(self):
        """Clears all outstanding orders from order books and players."""
        for suit in SUITS:
            self.order_books[suit] = OrderBook() # Reinitialize to clear
        for player in self.players:
            player.orders.clear()
        log_message("All outstanding orders cleared from the market.")

    def _generate_round_summary(self) -> dict:
        final_hands = {p.player_id: dict(p.hand) for p in self.players}
        final_scores = {p.player_id: p.money for p in self.players}
        return {
            "goal_suit": self.goal_suit,
            "final_hands": final_hands,
            "final_scores": final_scores,
            "round_winner(s)": [] # This will be filled by _calculate_payouts
        }
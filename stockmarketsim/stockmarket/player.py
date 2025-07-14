from collections import defaultdict
from stockmarket.config import SUITS
import uuid

class Player:
    def __init__(self, player_id: str, initial_money: int):
        self.player_id = player_id
        self.money = initial_money
        self.hand = defaultdict(int)  # e.g., {'spades': 5, 'hearts': 3}
        self.orders = {} # {order_id: order}
        self._order_id_counter = 0

    def next_order_id(self) -> str:
        self._order_id_counter += 1
        return f"{self.player_id}-{self._order_id_counter}"

    def add_card(self, suit: str, count: int = 1):
        self.hand[suit] += count

    def remove_card(self, suit: str, count: int = 1):
        if self.hand[suit] < count:
            raise ValueError(f"Player {self.player_id} does not have {count} of {suit}")
        self.hand[suit] -= count
        if self.hand[suit] == 0:
            del self.hand[suit]

    def add_money(self, amount: int):
        self.money += amount

    def deduct_money(self, amount: int):
        if self.money < amount:
            raise ValueError(f"Player {self.player_id} does not have enough money. Has {self.money}, needs {amount}")
        self.money -= amount

    def propose_actions(self, state: dict) -> list[dict]:
        """
        This method will be implemented by the agent.
        It should return a list of actions, e.g.:
        [
            {'action': 'BUY', 'suit': 'spades', 'price': 10},
            {'action': 'SELL', 'suit': 'hearts', 'price': 20},
            {'action': 'CANCEL', 'order_id': 'some-order-id'}
        ]
        """
        raise NotImplementedError

    def __str__(self):
        return (f"Player {self.player_id} (Money: ${self.money}, Hand: {dict(self.hand)})")

from stockmarket.order_book import OrderBook

def clear_batch(order_books: dict[str, OrderBook], players: dict) -> list[dict]:
    trades = []
    for suit, order_book in order_books.items():
        trades.extend(order_book.match(players))
    return trades

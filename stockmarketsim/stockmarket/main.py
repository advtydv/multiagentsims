
import json
import asyncio
import datetime
from stockmarket.game import Game
from stockmarket.player import Player
from stockmarket.agent import Agent
from stockmarket.config import INITIAL_MONEY, NUM_PLAYERS, NUM_ROUNDS
from stockmarket.utils import log_message

async def main():
    log_message("Starting Figgie Simulation")

    players = []
    for i in range(NUM_PLAYERS):
        player_id = f"Player_{i+1}"
        players.append(Player(player_id, INITIAL_MONEY))

    agents = {player.player_id: Agent(player) for player in players}

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/figgie_simulation_log_{timestamp}.jsonl"

    with open(log_filename, "w") as f:
        for i in range(NUM_ROUNDS):
            log_message(f"--- Starting Round {i+1}/{NUM_ROUNDS} ---")
            game = Game(players, agents)
            try:
                await game.play_round()
                for log_entry in game.game_log:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                log_message(f"An error occurred during round {i+1}: {e}")
    log_message(f"Full game log saved to {log_filename}")

    log_message("Figgie Simulation Finished")

if __name__ == "__main__":
    asyncio.run(main())

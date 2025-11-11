"""
Simulation of Memory Scramble game.
"""
import asyncio
import random
from .board import Board


async def simulation_main() -> None:
    """Simulate a Memory Scramble game."""
    filename = 'boards/perfect.txt'
    board: Board = await Board.parse_from_file(filename)
    size = 3
    players = 4
    tries = 1000
    max_delay_ms = 200

    print(f"\n{'='*60}")
    print(f"SIMULATION: {players} players, {tries} tries each")
    print(f"{'='*60}")
    print(f"Initial:\n{await board.look('sim')}\n")

    # Start players concurrently
    tasks = [
        asyncio.create_task(player(board, player_num, size, tries, max_delay_ms))
        for player_num in range(players)
    ]

    await asyncio.gather(*tasks)

    print(f"\n{'='*60}")
    print("SIMULATION COMPLETE")
    print(f"{'='*60}")
    print(f"Final:\n{await board.look('sim')}")


async def player(board: Board, player_number: int, size: int, tries: int, max_delay: float) -> None:
    """Simulate one player."""
    player_id = f'player_{player_number}'
    print(f"\n▶ {player_id} started")

    for attempt in range(tries):
        try:
            await timeout(random.random() * max_delay)

            # First card
            r1, c1 = random_int(size), random_int(size)
            await board.flip(player_id, r1, c1)

            await timeout(random.random() * max_delay)

            # Second card
            r2, c2 = random_int(size), random_int(size)
            result = await board.flip(player_id, r2, c2)

            # Check for match
            my_cards = [line for line in result.split('\n') if line.startswith('my ')]
            if len(my_cards) == 2:
                print(f" {player_id} matched!")

        except Exception as err:
            print(f"{player_id} try {attempt+1} failed: {err}")

    print(f"{player_id} finished")


def random_int(max_val: int) -> int:
    """Random int in [0, max_val)."""
    return random.randint(0, max_val - 1)


async def timeout(milliseconds: float) -> None:
    """Wait for duration in ms."""
    await asyncio.sleep(milliseconds / 1000.0)


if __name__ == '__main__':
    asyncio.run(simulation_main())
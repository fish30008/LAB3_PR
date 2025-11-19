
import asyncio
import random
from board import Board


async def simulation_main() -> None:
    filename = '../boards/perfect.txt'
    board: Board = await Board.parse_from_file(filename)
    size = board.rows

    print(f'board_size -> {size}')

    players = 4
    tries = 100
    max_delay_ms = 2

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
    player_id = f'player_{player_number}'
    print(f"\n▶ {player_id} started")

    for attempt in range(tries):
        try:
            await timeout(random.random() * max_delay)

            r1, c1 = random_int(size), random_int(size)
            await board.flip(player_id, r1, c1)

            await timeout(random.random() * max_delay)

            # Second card
            r2, c2 = random_int(size), random_int(size)
            result = await board.flip(player_id, r2, c2)

        except Exception as err:
            print(f"{player_id} try {attempt+1} failed: {err}")
            await asyncio.sleep(random.uniform(0.001, 0.005))
            continue

    print(f"{player_id} finished")


def random_int(max_val: int) -> int:
    return random.randint(0, max_val - 1)


async def timeout(milliseconds: float) -> None:
    await asyncio.sleep(milliseconds / 1000.0)


if __name__ == '__main__':
    asyncio.run(simulation_main())
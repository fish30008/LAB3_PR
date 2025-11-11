from .board import Board
from typing import Callable
from typing import Awaitable


async def look(board, player_id):
    return await board.look(player_id)


async def flip(board: Board, player_id: str, row: int, column: int) -> str:
    return await board.flip(player_id, row, column)


async def map_func(board: Board, player_id: str, f: Callable[[str], Awaitable[str]]) -> str:
    return await board.map_cards(player_id, f)


async def watch(board: Board, player_id: str) -> str:
    return await board.watch(player_id)







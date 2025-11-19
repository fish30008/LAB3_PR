import asyncio
import os
import random
from typing import Callable, List, Tuple, Awaitable, Dict, Optional
from dataclasses import dataclass, field


#ADT
@dataclass
class Card:
    label: str
    face_up: bool = False
    controller: Optional[str] = None
    removed: bool = False


#ADT
@dataclass
class PlayerState:
    controlled_cards: List[Tuple[int, int]] = field(default_factory=list)
    previous_controled_cards: List[Tuple[int, int]] = field(default_factory=list)

    matched: bool = False


#ADT
class Board:
    """
-----------
    """

    def __init__(self, rows: int, cols: int, cards: List[str]):
        assert len(cards) == rows * cols
        assert rows > 0 and cols > 0

        self.rows = rows
        self.cols = cols
        self.initial_cards = cards.copy()

        self.grid: List[List[Card]] = []
        self._initialize_grid()

        self.players: Dict[str, PlayerState] = {}
        self.lock = asyncio.Lock()
        self.version = 0


    # private methods
    def _initialize_grid(self) -> None:
        self.grid = []
        card_index = 0
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                row.append(Card(label=self.initial_cards[card_index]))
                card_index += 1
            self.grid.append(row)

    def _notify_change(self) -> None:
        self.version += 1

    def _get_player_state(self, player_id: str) -> PlayerState:
        if player_id not in self.players:
            self.players[player_id] = PlayerState()
        return self.players[player_id]

    def _count_remaining_cards(self) -> int:
        count = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.grid[r][c].removed:
                    count += 1
        return count

    def _renew_board(self) -> None:
        print("\n🔄 Board renewal: Resetting board")
        self._initialize_grid()
        self.players.clear()
        self._notify_change()

    def _debug_print_board_state(self) -> None:
        """Print debug info."""
        print("\n" + "="*60)
        for r in range(self.rows):
            row_str = []
            for c in range(self.cols):
                card = self.grid[r][c]
                if card.removed:
                    row_str.append("[X]")
                elif not card.face_up:
                    row_str.append("[?]")
                else:

                    row_str.append(f"[{card.label}]")
            print(" ".join(row_str))
        print("\nPlayers:")
        for pid, state in self.players.items():
            print(f"  {pid[:10]:10} ctrl:{state.controlled_cards}") #prev:{state.previous_cards} match:{state.matched}")
        print("="*60 + "\n")

    #aka single method
    @staticmethod
    async def parse_from_file(filename: str) -> 'Board':
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if not lines:
            raise ValueError("Empty board file")

        dims = lines[0].split('x')
        if len(dims) != 2:
            raise ValueError(f"Invalid dimension format: {lines[0]}")

        rows = int(dims[0])
        cols = int(dims[1])
        cards = lines[1:]

        if len(cards) != rows * cols:
            raise ValueError(f"Expected {rows * cols} cards, got {len(cards)}")

        board = Board(rows, cols, cards)

        board.filename = filename

        return board

    def _look_internal(self, player_id: str) -> str:
        lines = [f"{self.rows}x{self.cols}"]

        for r in range(self.rows):
            for c in range(self.cols):
                card = self.grid[r][c]

                if card.removed:
                    lines.append("none")
                elif not card.face_up:
                    lines.append("down")
                elif card.controller == player_id:
                    lines.append(f"my {card.label}")
                else:
                    lines.append(f"up {card.label}")

        return '\n'.join(lines)

    async def look(self, player_id: str) -> str:
        async with self.lock:
            return self._look_internal(player_id)

    async def flip(self, player_id: str, row: int, col: int) -> str:

        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise ValueError(f"Invalid position: ({row}, {col})")

        print(f"\n🎮 {player_id[:10]} flips ({row},{col})")

        # Check current player state
        async with self.lock:
            if self._count_remaining_cards() <= 1:
                self._renew_board()

            player_state = self._get_player_state(player_id)
            print(f'player_state -> {player_state} player_id -> {player_id}')
            num_controlled = len(player_state.controlled_cards)

            print(f"Player controls {num_controlled} cards: {player_state.controlled_cards}")

            if num_controlled == 0:
                print(f"   FIRST card - cleaning up previous")
                #self._cleanup_previous_cards(player_id)
                self._debug_print_board_state()

        # Determine flip type and execute
        async with self.lock:
            player_state = self._get_player_state(player_id)
            num_controlled = len(player_state.controlled_cards)

        if num_controlled == 0:
            result = await self._flip_first_card(player_id, row, col)
            print(f"   ✓ First card done")
            self._debug_print_board_state()
            return result
        elif num_controlled == 1:
            async with self.lock:
                result = self._flip_second_card(player_id, row, col)
                print(f"   ✓ Second card done")
                self._debug_print_board_state()
                return result
        else:
            async with self.lock:
                self._turn_down_card(player_id)
                if player_state.matched:
                    self._cleanup_previous_cards(player_id)

            result = await self._flip_first_card(player_id, row, col)
            self._debug_print_board_state()
            return result




    def _cleanup_previous_cards(self, player_id: str) -> None:

        # Rule 3-A: Remove matched pair
        player_state = self._get_player_state(player_id)
        if not player_state.controlled_cards:
            return
        print(f"   Rule 3-A: Removing {player_state.controlled_cards}")
        for (r, c) in player_state.controlled_cards:
            card = self.grid[r][c]
            if not card.removed:
                card.removed = True
                card.face_up = False
                card.controller = None
                self._notify_change()

    def _turn_down_card(self, player_id : str) -> None:
        player_state = self._get_player_state(player_id)
        if not player_state.controlled_cards:
            return
        print(f"   Rule 3-B: Turning down {player_state.controlled_cards}")
        for (r, c) in player_state.controlled_cards:
            card = self.grid[r][c]
            if not card.removed and card.face_up and card.controller is None:
                card.face_up = False
                self._notify_change()


    async def _flip_first_card(self, player_id: str, row: int, col: int) -> str:
        max_wait = 30.0
        wait_time = 0.0
        poll_interval = 1

        while wait_time < max_wait:
            async with self.lock:
                player_state = self._get_player_state(player_id)
                card = self.grid[row][col]
                controled_cards = player_state.previous_controled_cards
                for previous_card in controled_cards:
                    previous_card.face_up = False
                    #card.controller = None
                print(f'player_state -> {player_state} - id < {player_id}')
                # Rule 1-A: Empty

                if card.removed:
                    print(f"Rule 1-A: Card removed")
                    raise ValueError("Rule 1-A: Card removed -> Card has been removed")

                # Rule 1-B: Face down
                if not card.face_up:
                    print(f"   ✓ Rule 1-B: Flip face-down card up")
                    card.face_up = True
                    card.controller = player_id
                    player_state.controlled_cards = [(row, col)]
                    self._notify_change()
                    return self._look_internal(player_id)

                # Rule 1-C: Face up, not controlled
                if card.controller is None:
                    print(f"   ✓ Rule 1-C: Take control of face-up card")
                    card.controller = player_id
                    player_state.controlled_cards = [(row, col)]
                    self._notify_change()
                    return self._look_internal(player_id)

                # Rule 1-D: Controlled by another - wait
                print(f"   ⏳ Rule 1-D: Wait for {card.controller[:10]}")

            await asyncio.sleep(poll_interval)
            wait_time += poll_interval

        raise ValueError(f"Timeout waiting for card at ({row}, {col})")

    def _flip_second_card(self, player_id: str, row: int, col: int) -> str:
        player_state = self._get_player_state(player_id)
        card = self.grid[row][col]
        first_pos = player_state.controlled_cards[0]
        first_card = self.grid[first_pos[0]][first_pos[1]]

        print(f"Second: ({row},{col}) vs first {first_pos}")

        # Rule 2-A: Empty
        if card.removed:
            print(f"   ✗ Rule 2-A: Empty, relinquish first")
            first_card.controller = None
            player_state.controlled_cards = []
            player_state.matched = False
            self._notify_change()
            raise ValueError("Card has been removed")
        #my rule ->
        if card.face_up and card.controller == player_id:
            print(f"   ✗ My rule: Controlled by {card.controller[:10]}")
            # first_card.controller = None
            # player_state.controlled_cards = []
            # player_state.matched = False
            # self._notify_change()
            raise ValueError("Card is controlled by another player")


        # Rule 2-B: Controlled
        if card.face_up and card.controller is not None:
            print(f"   ✗ Rule 2-B: Controlled by {card.controller[:10]}, relinquish first")
            first_card.controller = None
            player_state.controlled_cards = []
            player_state.matched = False
            self._notify_change()
            raise ValueError("Card is controlled by another player")

        # Rule 2-C: Turn up if down
        if not card.face_up:
            card.face_up = True
            self._notify_change()

        # Rules 2-D & 2-E: Check match
        if first_card.label == card.label:
            # Rule 2-D: Match!
            print(f"   ✓ Rule 2-D: Match! {first_card.label}=={card.label}")
            card.controller = player_id
            player_state.controlled_cards = [first_pos, (row, col)]
            player_state.matched = True
            self._notify_change()
        else:
            # Rule 2-E: No match
            print(f"   ✗ Rule 2-E: No match {first_card.label}!={card.label}")
            first_card.controller = None
            card.controller = None
            player_state.previous_controled_cards = [first_card, card]
            player_state.controlled_cards = []
            player_state.matched = False
            self._notify_change()

        return self._look_internal(player_id)

    async def map_cards(self, player_id: str, func: Callable[[str], Awaitable[str]]) -> str:
        async with self.lock:
            print(f"\n🔄 {player_id[:10]} mapping cards")
            for r in range(self.rows):
                for c in range(self.cols):
                    card = self.grid[r][c]
                    if not card.removed:
                        old = card.label
                        card.label = await func(card.label)
                        if old != card.label:
                            print(f"   ({r},{c}): {old}→{card.label}")

            self._notify_change()
            return self._look_internal(player_id)

    async def watch(self, player_id: str, timeout: float = 30.0) -> str:
        #notify changes trigeres the changing in version
        start_version = self.version
        poll_interval = 0.5
        elapsed = 0.0

        print(f"👁 {player_id[:10]} watching (v{start_version})")

        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            if self.version != start_version:
                print(f"   Changed! v{self.version}")
                return await self.look(player_id)

        return await self.look(player_id)


async def __main__():
    #print(os.getcwd())
    board = await Board.parse_from_file('../boards/ab.txt')
    players = []
    for i in range(3):
        players.append(f'player_{i}')

    print("Initial board")
    state = await board.look(players[0])
    print(state)
    print()

    state = await board.flip(players[0], 0, 0)
    state = await board.flip(players[0], 0, 2)

    try:
        state = await board.flip(players[1], 0, 2)

        state = await board.flip(players[1], 1, 2)

    except Exception as e:
        print(e)

    state = await board.flip(players[0], 0, 3)

    try:
        state = await board.flip(players[1], 2, 4)

        state = await board.flip(players[1], 2, 2)

    except Exception as e:
        print(e)

    #print(state)

    state = await board.look(players[0])
    #print(state)

if __name__ == "__main__":
    print(os.getcwd())

    asyncio.run(__main__())
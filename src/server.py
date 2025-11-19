
import sys
import asyncio
from pathlib import Path
import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from .board import Board
from .commands import look, flip, map_func, watch


class WebServer:

    def __init__(self, board: Board, requested_port: int):

        self.board = board
        self.requested_port = requested_port if requested_port != 0 else 8080
        self.app = FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        @self.app.get('/look/{player_id}')
        async def handle_look(player_id: str):
            assert player_id
            board_state = await look(self.board, player_id)
            return PlainTextResponse(board_state, status_code=status.HTTP_200_OK)

        @self.app.get('/flip/{player_id}/{location}')
        async def handle_flip(player_id: str, location: str):
            assert player_id
            assert location

            parts = location.split(',')
            row = int(parts[0])
            column = int(parts[1])
            assert row is not None and not (row != row)  # not NaN
            assert column is not None and not (column != column)  # not NaN

            try:
                board_state = await flip(self.board, player_id, row, column)
                return PlainTextResponse(board_state, status_code=status.HTTP_200_OK)
            except Exception as err:
                return PlainTextResponse(
                    f"cannot flip this card: {err}",
                    status_code=status.HTTP_409_CONFLICT
                )

        @self.app.get('/replace/{player_id}/{from_card}/{to_card}')
        async def handle_replace(player_id: str, from_card: str, to_card: str):
            assert player_id
            assert from_card
            assert to_card

            async def replacement_func(card: str) -> str:
                return to_card if card == from_card else card

            board_state = await map_func(self.board, player_id, replacement_func)
            return PlainTextResponse(board_state, status_code=status.HTTP_200_OK)
        @self.app.get('/watch/{player_id}')
        async def handle_watch(player_id: str):
            assert player_id
            board_state = await watch(self.board, player_id)
            return PlainTextResponse(board_state, status_code=status.HTTP_200_OK)
        @self.app.get('/')
        async def serve_index():
            return FileResponse('public/index.html')

    def start(self) -> None:
        print(f"server now listening at http://localhost:{self.requested_port}")
        uvicorn.run(
            self.app,
            host='0.0.0.0',   # bind to all interfaces so container ports are reachable
            port=self.requested_port,
            log_level='warning'
        )

    def stop(self) -> None:
        print("server stopped")



def main() -> None:

    args = sys.argv[1:]

    if len(args) < 1:
        raise ValueError("missing PORT")

    port_string = args[0]
    try:
        port = int(port_string)
    except ValueError:
        raise ValueError("invalid PORT")

    if port < 0:
        raise ValueError("invalid PORT")

    if len(args) < 2:
        raise ValueError("missing FILENAME")

    filename = args[1]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    board = loop.run_until_complete(Board.parse_from_file(filename))
    loop.close()
    server = WebServer(board, port)
    server.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nserver stopped")
        sys.exit(0)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
"""
uci.py — Universal Chess Interface wrapper for LamarEngine.

Run:  python uci.py
Then pipe UCI commands to stdin; responses arrive on stdout (flushed).

Supported commands: uci, isready, ucinewgame, position, go, stop, quit.
All unknown commands are silently ignored per the UCI spec.
Errors are written to stderr only — stdout is reserved for UCI responses.
"""

import sys
import chess

from engine.engine import choose_move


_ENGINE_NAME   = "LamarEngine"
_ENGINE_VER    = "0.1"
_ENGINE_AUTHOR = "Bryce Howard"


# ---------------------------------------------------------------------------
# Position parser
# ---------------------------------------------------------------------------

def _parse_position(args: list[str], board: chess.Board) -> chess.Board:
    """
    Parse a 'position' command's argument list and return the resulting board.

      position startpos [moves <m1> <m2> ...]
      position fen <fen_string> [moves <m1> <m2> ...]
    """
    if not args:
        return chess.Board()

    moves: list[str] = []

    if args[0] == "startpos":
        board = chess.Board()
        try:
            mi = args.index("moves")
            moves = args[mi + 1:]
        except ValueError:
            pass  # no moves section

    elif args[0] == "fen":
        fen_parts = args[1:]
        try:
            mi = fen_parts.index("moves")
            fen_str = " ".join(fen_parts[:mi])
            moves   = fen_parts[mi + 1:]
        except ValueError:
            fen_str = " ".join(fen_parts)
        try:
            board = chess.Board(fen_str)
        except ValueError:
            board = chess.Board()   # malformed FEN → reset
    else:
        return chess.Board()

    for uci_str in moves:
        try:
            move = chess.Move.from_uci(uci_str)
            if move in board.legal_moves:
                board.push(move)
            else:
                break   # illegal move — stop applying
        except (ValueError, chess.InvalidMoveError):
            break

    return board


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    board:     chess.Board       = chess.Board()
    last_move: chess.Move | None = None

    while True:
        raw = sys.stdin.readline()
        if not raw:          # EOF — GUI closed the pipe
            break

        line = raw.strip()
        if not line:
            continue

        try:
            tokens     = line.split()
            cmd, *args = tokens

            # ---- uci --------------------------------------------------
            if cmd == "uci":
                print(f"id name {_ENGINE_NAME} {_ENGINE_VER}", flush=True)
                print(f"id author {_ENGINE_AUTHOR}",           flush=True)
                print("uciok",                                  flush=True)

            # ---- isready ----------------------------------------------
            elif cmd == "isready":
                print("readyok", flush=True)

            # ---- ucinewgame -------------------------------------------
            elif cmd == "ucinewgame":
                board     = chess.Board()
                last_move = None

            # ---- position ---------------------------------------------
            elif cmd == "position":
                board = _parse_position(args, board)

            # ---- go ---------------------------------------------------
            elif cmd == "go":
                depth = 4
                if "depth" in args:
                    idx = args.index("depth")
                    if idx + 1 < len(args):
                        try:
                            depth = int(args[idx + 1])
                        except ValueError:
                            pass

                if not board.legal_moves.count():
                    continue   # game already over; nothing to send

                move, _ = choose_move(board, depth=depth)
                last_move = move
                print(f"bestmove {move.uci()}", flush=True)

            # ---- stop -------------------------------------------------
            elif cmd == "stop":
                if last_move is not None:
                    print(f"bestmove {last_move.uci()}", flush=True)
                else:
                    legal = list(board.legal_moves)
                    if legal:
                        print(f"bestmove {legal[0].uci()}", flush=True)

            # ---- quit -------------------------------------------------
            elif cmd == "quit":
                break

            # Unknown commands are silently ignored (UCI spec §3).

        except Exception as exc:
            # Never let an exception reach stdout — log to stderr only.
            print(f"info string error: {exc!r}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()

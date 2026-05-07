"""
Terminal chess: you play White, the engine plays Black.
Enter moves in UCI notation (e2e4, g1f3, e1g1 for castling, e7e8q for promotion).
Type 'quit' or 'exit' to resign.
"""
import chess
from engine.engine import choose_move


def print_board(board: chess.Board) -> None:
    print()
    print(board.unicode(invert_color=True, borders=True))
    print()


def game_over_message(board: chess.Board) -> str | None:
    if board.is_checkmate():
        winner = "White" if board.turn == chess.BLACK else "Black"
        return f"Checkmate! {winner} wins."
    if board.is_stalemate():
        return "Stalemate — draw."
    if board.is_insufficient_material():
        return "Draw by insufficient material."
    if board.is_seventyfive_moves():
        return "Draw by 75-move rule."
    if board.is_fivefold_repetition():
        return "Draw by fivefold repetition."
    return None


def get_player_move(board: chess.Board) -> chess.Move | None:
    """Prompt the user and return a validated Move, or None to quit."""
    while True:
        try:
            raw = input("Your move (UCI): ").strip()
        except (EOFError, KeyboardInterrupt):
            return None

        if raw.lower() in ("quit", "exit", "q"):
            return None

        try:
            move = chess.Move.from_uci(raw)
        except chess.InvalidMoveError:
            print(f"  '{raw}' is not valid UCI notation. Example: e2e4")
            continue

        if move not in board.legal_moves:
            if board.is_check():
                print(f"  Illegal move (you are in check). Try again.")
            else:
                print(f"  Illegal move. Try again.")
            continue

        return move


def main() -> None:
    board = chess.Board()
    print("=== Chess Engine ===")
    print("You are White. Enter moves in UCI notation (e2e4, e1g1, e7e8q …).")
    print("Type 'quit' to resign.\n")
    print_board(board)

    while True:
        # --- player (White) turn ---
        move = get_player_move(board)
        if move is None:
            print("You resigned. Thanks for playing.")
            break

        board.push(move)
        print(f"  You played: {move.uci()}")
        print_board(board)

        msg = game_over_message(board)
        if msg:
            print(msg)
            break

        # --- engine (Black) turn ---
        print("  Engine is thinking…")
        engine_move, eval_cp = choose_move(board)
        board.push(engine_move)
        print(f"  Engine played: {engine_move.uci()} (eval: {eval_cp / 100:+.2f})")
        print_board(board)

        msg = game_over_message(board)
        if msg:
            print(msg)
            break


if __name__ == "__main__":
    main()

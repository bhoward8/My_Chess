import chess

from engine.search import find_best_move


def choose_move(board: chess.Board, depth: int = 4) -> tuple[chess.Move, int]:
    """
    Return (best_move, eval_centipawns) for the side to move.
    eval_centipawns is from White's perspective (positive = White ahead).
    """
    return find_best_move(board, depth)

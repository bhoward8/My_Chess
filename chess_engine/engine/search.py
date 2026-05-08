"""
search.py — negamax alpha-beta with quiescence search.

Public API:
    find_best_move(board, depth) → (chess.Move, int)
        Returns the best move and its score in centipawns from White's perspective.
"""

import chess

from engine.evaluation import evaluate

_MATE_SCORE = 99_999

_PIECE_VAL: dict[chess.PieceType, int] = {
    chess.PAWN:   1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK:   5,
    chess.QUEEN:  9,
    chess.KING:   0,
}


def _mvv_lva(board: chess.Board, move: chess.Move) -> int:
    victim   = board.piece_at(move.to_square)
    aggressor = board.piece_at(move.from_square)
    if victim is None or aggressor is None:  # pragma: no cover
        return 0
    return (_PIECE_VAL.get(victim.piece_type, 0) * 10
            - _PIECE_VAL.get(aggressor.piece_type, 0))


def _order_moves(board: chess.Board) -> list[chess.Move]:
    """Captures (sorted by MVV-LVA) → checks → quiet moves."""
    captures, checks, quiets = [], [], []
    for move in board.legal_moves:
        if board.piece_at(move.to_square) is not None:
            captures.append(move)
        elif board.gives_check(move):
            checks.append(move)
        else:
            quiets.append(move)
    captures.sort(key=lambda m: _mvv_lva(board, m), reverse=True)
    return captures + checks + quiets


def quiescence(board: chess.Board, alpha: int, beta: int, color: int) -> int:
    """
    Extend the search at leaf nodes by examining only captures until the
    position is quiet.  color: +1 if White to move, -1 if Black to move.
    Returns the score from the side-to-move's perspective.

    The stand-pat score (static eval) acts as a lower bound because the side
    to move can always decline to capture.
    """
    stand_pat = evaluate(board) * color
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    for move in board.legal_moves:
        if board.piece_at(move.to_square) is None:
            continue
        board.push(move)
        score = -quiescence(board, -beta, -alpha, -color)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board: chess.Board, depth: int, alpha: int, beta: int, color: int) -> int:
    """
    Negamax alpha-beta search.  color: +1 if White to move, -1 if Black to move.
    Returns the score from the side-to-move's perspective.

    Terminal cases: checkmate (loss), stalemate / draws (0).
    At depth 0 the search falls into quiescence rather than returning static eval
    directly, which avoids the horizon effect on capture sequences.
    """
    if board.is_checkmate():
        return -_MATE_SCORE
    if (board.is_stalemate()
            or board.is_insufficient_material()
            or board.is_fifty_moves()
            or board.is_repetition()):
        return 0
    if depth == 0:
        return quiescence(board, alpha, beta, color)

    for move in _order_moves(board):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, -color)
        board.pop()
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break   # beta cutoff

    return alpha


def find_best_move(board: chess.Board, depth: int = 4) -> tuple[chess.Move, int]:
    """
    Search to *depth* plies and return (best_move, score).
    Score is in centipawns from White's perspective (positive = White ahead).
    Raises ValueError if there are no legal moves.
    """
    legal = list(board.legal_moves)
    if not legal:
        raise ValueError("No legal moves available")

    color      = 1 if board.turn == chess.WHITE else -1
    alpha      = -_MATE_SCORE - 1
    beta       =  _MATE_SCORE + 1
    best_move  = legal[0]
    best_score = -_MATE_SCORE - 1   # side-to-move perspective

    for move in _order_moves(board):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, -color)
        board.pop()
        if score > best_score:
            best_score = score
            best_move  = move
        if score > alpha:
            alpha = score

    # Convert from side-to-move perspective back to White's perspective.
    return best_move, best_score * color

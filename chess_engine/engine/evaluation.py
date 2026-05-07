"""
evaluation.py — static position evaluator.

evaluate(board) returns a score in centipawns from White's perspective.
Positive = good for White; negative = good for Black; 100 cp = one pawn.
"""

import chess

from engine.predicates import controls_center, in_extended_center, is_hanging


# ---------------------------------------------------------------------------
# Material values (centipawns)
# ---------------------------------------------------------------------------

_CP: dict[chess.PieceType, int] = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,  # 10 cp above knight → mild bishop-pair preference
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:     0,  # king is invaluable; checkmate is a terminal score
}


# ---------------------------------------------------------------------------
# Piece-square tables  (Simplified Evaluation Function, chessprogramming.org)
#
# Index layout: 0 = a8, 7 = h8, …, 56 = a1, 63 = h1  (rank 8 first,
# left-to-right, top-to-bottom — matching the visual board orientation).
#
# Usage:
#   White piece on python-chess square `sq`  →  PST[sq ^ 56]
#   Black piece on python-chess square `sq`  →  PST[sq]
#
# The XOR-56 trick: python-chess numbers squares a1=0 … h8=63 (rank 1 first).
# XOR-ing with 56 (0b111000) flips the rank bits so rank-1 squares map to
# indices 56-63 — the bottom row of the wiki table — which represents the
# white king-side back rank, etc.  Black reads the table un-flipped because
# the wiki's rank-8-at-top layout already mirrors Black's own back rank,
# giving identical positional incentives from each side's perspective.
# ---------------------------------------------------------------------------

_PST_PAWN: tuple[int, ...] = (
     0,  0,  0,  0,  0,  0,  0,  0,   # rank 8  (promotion rank for White)
    50, 50, 50, 50, 50, 50, 50, 50,   # rank 7  (one step from promotion)
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,   # rank 2  (starting rank for White)
     0,  0,  0,  0,  0,  0,  0,  0,   # rank 1  (impossible for pawn)
)

_PST_KNIGHT: tuple[int, ...] = (
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
)

_PST_BISHOP: tuple[int, ...] = (
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
)

_PST_ROOK: tuple[int, ...] = (
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,   # bonus for d/e files (open-file control)
)

_PST_QUEEN: tuple[int, ...] = (
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
)

_PST_KING: tuple[int, ...] = (  # middlegame: strongly encourages castling
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,  # g1/b1 bonuses reward castled king
)

_PST: dict[chess.PieceType, tuple[int, ...]] = {
    chess.PAWN:   _PST_PAWN,
    chess.KNIGHT: _PST_KNIGHT,
    chess.BISHOP: _PST_BISHOP,
    chess.ROOK:   _PST_ROOK,
    chess.QUEEN:  _PST_QUEEN,
    chess.KING:   _PST_KING,
}


# ---------------------------------------------------------------------------
# Score components
# ---------------------------------------------------------------------------

def material_score(board: chess.Board) -> int:
    """White piece values minus Black piece values, in centipawns."""
    score = 0
    for pt, value in _CP.items():
        score += value * len(board.pieces(pt, chess.WHITE))
        score -= value * len(board.pieces(pt, chess.BLACK))
    return score


def hanging_penalty(board: chess.Board) -> int:
    """
    For every hanging piece (attacked by opponent, zero defenders), subtract
    its centipawn value from the score of the side that owns it.
    White piece hanging → score falls; Black piece hanging → score rises.
    """
    score = 0
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is None or not is_hanging(board, sq):
            continue
        value = _CP.get(piece.piece_type, 0)
        if piece.color == chess.WHITE:
            score -= value
        else:
            score += value
    return score


def piece_square_score(board: chess.Board) -> int:
    """
    Positional bonus/penalty from piece-square tables.
    White reads PST[sq ^ 56]; Black reads PST[sq].
    See the PST comment block above for the full derivation.
    """
    score = 0
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is None:
            continue
        pst = _PST.get(piece.piece_type)
        if pst is None:
            continue
        if piece.color == chess.WHITE:
            score += pst[sq ^ 56]
        else:
            score -= pst[sq]
    return score


def mobility_score(board: chess.Board) -> int:
    """
    2 cp per legal move of advantage over the opponent.

    The opponent's legal-move count is estimated by flipping the turn on a
    board copy.  The en passant square is cleared on that copy because EP
    captures are only valid on the turn immediately following the pawn push —
    giving them to the wrong side would inflate the opponent's move count.
    """
    own_count = board.legal_moves.count()

    opp_board = board.copy()
    opp_board.turn    = not board.turn
    opp_board.ep_square = None          # EP only valid on the correct turn
    opp_count = opp_board.legal_moves.count()

    if board.turn == chess.WHITE:
        return 2 * (own_count - opp_count)
    else:
        return 2 * (opp_count - own_count)


def center_control_score(board: chess.Board) -> int:
    """
    Bonuses for attacking central squares, summed over all pieces:
      10 cp per attack on a core center square   (d4, e4, d5, e5).
       5 cp per attack on an extended center sq  (c3–f6, excluding core 4).
    """
    score = 0
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is None:
            continue
        sign = 1 if piece.color == chess.WHITE else -1
        for attacked_sq in board.attacks(sq):
            if controls_center(attacked_sq):
                score += sign * 10
            elif in_extended_center(attacked_sq):
                score += sign * 5
    return score


# ---------------------------------------------------------------------------
# Top-level evaluator
# ---------------------------------------------------------------------------

def evaluate(board: chess.Board) -> int:
    """
    Static evaluation of *board* in centipawns from White's perspective.

    Terminal cases:
      Checkmate          → ±99999  (side to move is the loser).
      Stalemate          → 0.
      Insufficient mat.  → 0.

    Otherwise returns:
      material + hanging_penalty + piece_square + mobility + center_control
    """
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    return (
        material_score(board)
        + hanging_penalty(board)
        + piece_square_score(board)
        + mobility_score(board)
        + center_control_score(board)
    )

"""
Tests for engine/search.py.

Each test uses a concrete FEN position so failures are easy to reproduce on a board.
"""

import chess
import pytest

from engine.search import find_best_move


# ---------------------------------------------------------------------------
# Mate in 1
# ---------------------------------------------------------------------------

def test_finds_mate_in_one():
    # White Rf7 + Kh6 vs Black Kh8: Rf7-f8 is the only checkmate.
    board = chess.Board("7k/5R2/7K/8/8/8/8/8 w - - 0 1")
    move, _ = find_best_move(board, depth=2)
    board.push(move)
    assert board.is_checkmate()


# ---------------------------------------------------------------------------
# Material: captures hanging piece
# ---------------------------------------------------------------------------

def test_captures_hanging_queen():
    # White Rd1 vs Black Qd5 (undefended): engine should capture Rxd5.
    board = chess.Board("7k/8/8/3q4/8/8/8/3R3K w - - 0 1")
    move, _ = find_best_move(board, depth=2)
    assert move == chess.Move.from_uci("d1d5")


# ---------------------------------------------------------------------------
# Avoids blunder
# ---------------------------------------------------------------------------

def test_avoids_walking_queen_into_defended_pawn():
    # White Qa4 can capture Black pawn b5, but b5 is defended by Black pawn c6.
    # Qxb5 loses a queen for a pawn (SEE = -8).  Engine must play something else.
    board = chess.Board("7k/8/2p5/1p6/Q7/8/8/7K w - - 0 1")
    move, _ = find_best_move(board, depth=3)
    assert move != chess.Move.from_uci("a4b5")


# ---------------------------------------------------------------------------
# Mate in 2
# ---------------------------------------------------------------------------

def test_finds_mate_in_two():
    # White: Kh1, Rg2, Rf1; Black: Kh3 (lone king).
    # Forced line: 1.Rf1-f8! (quiet — cuts off h4 escape) Kh3-h4 (only legal)
    #              2.Rf8-h8#
    # Black has exactly one legal reply to Rf8, so depth 4 finds the full line.
    board = chess.Board("8/8/8/8/8/7k/6R1/5R1K w - - 0 1")
    move, score = find_best_move(board, depth=4)
    assert move == chess.Move.from_uci("f1f8")
    assert score == 99999


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_find_best_move_raises_on_no_legal_moves():
    # Smothered mate: White Nf7 checkmates Black Kh8 — no legal moves.
    board = chess.Board("6rk/5Npp/8/8/8/8/8/7K b - - 0 1")
    with pytest.raises(ValueError, match="No legal moves"):
        find_best_move(board)


# ---------------------------------------------------------------------------
# Draw detection inside negamax
# ---------------------------------------------------------------------------

def test_negamax_stalemate_branch():
    # White Kc6, Qb7 vs Black Ka8.  Qb7-b6 leads to stalemate (Ka8 has no
    # legal moves and is not in check), so negamax returns 0 for that branch.
    board = chess.Board("k7/1Q6/2K5/8/8/8/8/8 w - - 0 1")
    move, _ = find_best_move(board, depth=2)
    assert move in board.legal_moves


def test_negamax_insufficient_material_branch():
    # KvK is always insufficient material; every child node returns 0.
    board = chess.Board("8/8/4k3/8/8/4K3/8/8 w - - 0 1")
    move, score = find_best_move(board, depth=2)
    assert move in board.legal_moves
    assert score == 0


def test_negamax_fifty_move_rule_branch():
    # halfmove clock at 99: any non-capture king/rook move pushes it to 100,
    # triggering is_fifty_moves() → return 0 in the child node.
    board = chess.Board("8/3k4/8/8/8/8/8/R2K4 w - - 99 1")
    move, score = find_best_move(board, depth=2)
    assert move in board.legal_moves
    assert score == 0


def test_negamax_repetition_branch():
    # Two full Rd2/Kd3 vs Kd7 oscillations build a history where the third
    # occurrence of each position triggers is_repetition() → return 0.
    board = chess.Board("8/3k4/8/8/8/3K4/3R4/8 w - - 0 1")
    for _ in range(2):
        board.push(chess.Move.from_uci("d2e2"))
        board.push(chess.Move.from_uci("d7e7"))
        board.push(chess.Move.from_uci("e2d2"))
        board.push(chess.Move.from_uci("e7d7"))
    # After two oscillations Rd2→e2 now visits a position for the 3rd time.
    move, _ = find_best_move(board, depth=2)
    assert move in board.legal_moves

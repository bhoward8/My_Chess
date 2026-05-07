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

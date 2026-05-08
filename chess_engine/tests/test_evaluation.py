"""
Tests for engine/evaluation.py.

Each test uses a concrete FEN position so failures are easy to reproduce on a board.
"""

import chess
import pytest

from engine.evaluation import evaluate


# ---------------------------------------------------------------------------
# Terminal conditions
# ---------------------------------------------------------------------------

def test_checkmate_black_is_mated():
    # Smothered mate: White knight f7 checkmates Black king h8.
    # board.turn == BLACK → evaluate returns +99999 (White wins).
    board = chess.Board("6rk/5Npp/8/8/8/8/8/7K b - - 0 1")
    assert evaluate(board) == 99999


def test_checkmate_white_is_mated():
    # Fool's mate (1.f3 e5 2.g4 Qh4#): Black queen h4 checkmates White king e1.
    # board.turn == WHITE → evaluate returns -99999 (Black wins).
    board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    assert evaluate(board) == -99999


def test_stalemate_returns_zero():
    # Black king h8 is stalemated: White queen g5 and king h6 cover g8, g7, h7.
    board = chess.Board("7k/8/7K/6Q1/8/8/8/8 b - - 0 1")
    assert evaluate(board) == 0


# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------

def test_starting_position_is_zero():
    # The opening position is perfectly symmetric, so all score components cancel.
    board = chess.Board()
    assert evaluate(board) == 0


def test_white_up_a_queen_is_strongly_positive():
    # Opening position with Black's queen removed from d8.
    # Material advantage alone is +900 cp; total score should comfortably exceed +800.
    board = chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert evaluate(board) > 800


# ---------------------------------------------------------------------------
# Hanging penalty
# ---------------------------------------------------------------------------

def test_hanging_knight_scores_worse_than_defended():
    # White knight e4 is attacked by Black bishop d5 and has no defenders.
    board_hanging = chess.Board("8/7k/8/3b4/4N3/8/8/6K1 w - - 0 1")

    # Same position plus White pawn d3, which defends e4 diagonally (d3→e4).
    # The pawn itself is not attacked by the bishop (d5→d3 is same file, not diagonal).
    board_defended = chess.Board("8/7k/8/3b4/4N3/3P4/8/6K1 w - - 0 1")

    assert evaluate(board_hanging) < evaluate(board_defended)


# ---------------------------------------------------------------------------
# Insufficient material
# ---------------------------------------------------------------------------

def test_insufficient_material_returns_zero():
    # KvK: no side can force checkmate; evaluate must return 0.
    board = chess.Board("8/8/4k3/8/8/4K3/8/8 w - - 0 1")
    assert evaluate(board) == 0


# ---------------------------------------------------------------------------
# mobility_score — Black-to-move branch
# ---------------------------------------------------------------------------

def test_evaluate_with_black_to_move():
    # After 1.e4 it is Black's turn; this exercises the `else` branch in
    # mobility_score (board.turn == BLACK).
    board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
    score = evaluate(board)
    assert isinstance(score, int)

"""Tests for engine/engine.py (public API wrapper)."""

import chess

from engine.engine import choose_move


def test_choose_move_returns_legal_move():
    board = chess.Board()
    move, _ = choose_move(board, depth=1)
    assert move in board.legal_moves


def test_choose_move_score_is_int():
    board = chess.Board()
    _, score = choose_move(board, depth=1)
    assert isinstance(score, int)

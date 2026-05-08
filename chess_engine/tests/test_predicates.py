"""
Tests for engine/predicates.py.

Each test uses a concrete FEN position so failures are easy to reproduce on a board.
At least one positive and one negative case per predicate.
"""

import chess
import pytest

from engine.predicates import (
    attackers_of,
    controls_center,
    defenders_of,
    gives_check,
    in_extended_center,
    is_attacked,
    is_defended,
    is_essential_defender,
    is_hanging,
    is_pinned,
    piece_value,
    static_exchange_eval,
)


# ---------------------------------------------------------------------------
# piece_value
# ---------------------------------------------------------------------------

def test_piece_value_pawn():
    assert piece_value(chess.Piece(chess.PAWN, chess.WHITE)) == 1

def test_piece_value_knight():
    assert piece_value(chess.Piece(chess.KNIGHT, chess.BLACK)) == 3

def test_piece_value_bishop():
    assert piece_value(chess.Piece(chess.BISHOP, chess.WHITE)) == 3

def test_piece_value_rook():
    assert piece_value(chess.Piece(chess.ROOK, chess.BLACK)) == 5

def test_piece_value_queen():
    assert piece_value(chess.Piece(chess.QUEEN, chess.WHITE)) == 9

def test_piece_value_king_is_zero():
    # King loss ends the game; we never count it as capturable material.
    assert piece_value(chess.Piece(chess.KING, chess.WHITE)) == 0


# ---------------------------------------------------------------------------
# attackers_of
#
# Position: White rook a1, Black rook a8, White king h1, Black king h8.
#   r6k/8/8/8/8/8/8/R6K
# ---------------------------------------------------------------------------

_ATTACKER_FEN = "r6k/8/8/8/8/8/8/R6K w - - 0 1"

def test_attackers_of_white_attacks_a8():
    board = chess.Board(_ATTACKER_FEN)
    # White rook on a1 attacks a8 along the a-file.
    result = attackers_of(board, chess.A8, chess.WHITE)
    assert chess.A1 in result

def test_attackers_of_black_attacks_a1():
    board = chess.Board(_ATTACKER_FEN)
    # Black rook on a8 attacks a1 along the a-file.
    result = attackers_of(board, chess.A1, chess.BLACK)
    assert chess.A8 in result

def test_attackers_of_no_white_attackers_of_b8():
    board = chess.Board(_ATTACKER_FEN)
    # Neither white piece attacks b8.
    result = attackers_of(board, chess.B8, chess.WHITE)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# defenders_of
#
# Position: White rooks a1 and b1, White king h1, Black king h8.
#   7k/8/8/8/8/8/8/RR5K
# ---------------------------------------------------------------------------

_DEFENDER_FEN = "7k/8/8/8/8/8/8/RR5K w - - 0 1"

def test_defenders_of_rook_defended_by_rook():
    board = chess.Board(_DEFENDER_FEN)
    # White rook on b1 defends White rook on a1 along rank 1.
    result = defenders_of(board, chess.A1)
    assert chess.B1 in result

def test_defenders_of_king_has_no_defenders():
    board = chess.Board(_DEFENDER_FEN)
    # Black king on h8 — no other Black pieces exist to defend it.
    result = defenders_of(board, chess.H8)
    assert len(result) == 0

def test_defenders_of_empty_square_returns_empty():
    board = chess.Board(_DEFENDER_FEN)
    result = defenders_of(board, chess.E4)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# is_attacked
# (re-uses _ATTACKER_FEN)
# ---------------------------------------------------------------------------

def test_is_attacked_positive():
    board = chess.Board(_ATTACKER_FEN)
    # Black rook on a8 attacks a1.
    assert is_attacked(board, chess.A1, chess.BLACK) is True

def test_is_attacked_negative():
    board = chess.Board(_ATTACKER_FEN)
    # No Black piece attacks b1.
    assert is_attacked(board, chess.B1, chess.BLACK) is False


# ---------------------------------------------------------------------------
# is_defended
# (re-uses _DEFENDER_FEN)
# ---------------------------------------------------------------------------

def test_is_defended_positive():
    board = chess.Board(_DEFENDER_FEN)
    # White rook on a1 defended by White rook on b1.
    assert is_defended(board, chess.A1) is True

def test_is_defended_negative():
    board = chess.Board(_DEFENDER_FEN)
    # Black king on h8 has no defenders.
    assert is_defended(board, chess.H8) is False


# ---------------------------------------------------------------------------
# is_hanging
#
# Positive: White pawn e4, Black pawn d5 (attacks e4), no White defender.
#   8/8/8/3p4/4P3/8/8/K6k
#
# Negative: add White bishop on d3, which defends e4 diagonally.
#   8/8/8/3p4/4P3/3B4/8/K6k
# ---------------------------------------------------------------------------

def test_is_hanging_positive():
    # Black d5 pawn attacks White e4 pawn; nothing defends e4.
    board = chess.Board("8/8/8/3p4/4P3/8/8/K6k w - - 0 1")
    assert is_hanging(board, chess.E4) is True

def test_is_hanging_negative_defended():
    # White bishop on d3 defends e4, so the pawn is not hanging.
    board = chess.Board("8/8/8/3p4/4P3/3B4/8/K6k w - - 0 1")
    assert is_hanging(board, chess.E4) is False

def test_is_hanging_empty_square():
    board = chess.Board("8/8/8/3p4/4P3/8/8/K6k w - - 0 1")
    assert is_hanging(board, chess.H4) is False


# ---------------------------------------------------------------------------
# is_pinned
#
# Positive: White bishop e2 pinned to White king e1 by Black rook e8.
#   4rk2/8/8/8/8/8/4B3/4K3
#
# Negative: White bishop on d2 — off the e-file, not in the rook's pin ray.
#   4rk2/8/8/8/8/8/3B4/4K3
# ---------------------------------------------------------------------------

def test_is_pinned_positive():
    # Bishop on e2 sits between king e1 and rook e8 — absolutely pinned.
    board = chess.Board("4rk2/8/8/8/8/8/4B3/4K3 w - - 0 1")
    assert is_pinned(board, chess.E2) is True

def test_is_pinned_negative():
    # Bishop on d2 is not on the e-file, so the Black rook cannot pin it.
    board = chess.Board("4rk2/8/8/8/8/8/3B4/4K3 w - - 0 1")
    assert is_pinned(board, chess.D2) is False

def test_is_pinned_empty_square():
    board = chess.Board("4rk2/8/8/8/8/8/4B3/4K3 w - - 0 1")
    assert is_pinned(board, chess.A4) is False


# ---------------------------------------------------------------------------
# gives_check
#
# Position: White rook a1, White king h1, Black king e8.
#   4k3/8/8/8/8/8/8/R6K
#
# Positive: Ra1-a8 — rook lands on rank 8, attacks e8 along the rank.
# Negative: Ra1-h1 — rook moves within rank 1, cannot reach e8.
# ---------------------------------------------------------------------------

def test_gives_check_positive():
    board = chess.Board("4k3/8/8/8/8/8/8/R6K w - - 0 1")
    move = chess.Move.from_uci("a1a8")
    assert gives_check(board, move) is True

def test_gives_check_negative():
    board = chess.Board("4k3/8/8/8/8/8/8/R6K w - - 0 1")
    move = chess.Move.from_uci("a1b1")
    assert gives_check(board, move) is False


# ---------------------------------------------------------------------------
# is_essential_defender
#
# Positive (a) — pin path:
#   White bishop e2 is pinned to king e1 by Black rook e8.
#   4rk2/8/8/8/8/8/4B3/4K3
#
# Positive (b) — guardian path:
#   White rook e1 guards White knight e5 against Black rook e8.
#   Removing e1 rook leaves the knight hanging.
#   4rk2/8/8/4N3/8/8/8/4R1K1
#
# Negative:
#   White rook a1 guards nothing; no allied piece becomes hanging on removal.
#   7k/8/8/8/4N3/8/8/R3K3
# ---------------------------------------------------------------------------

def test_is_essential_defender_pinned_piece():
    board = chess.Board("4rk2/8/8/8/8/8/4B3/4K3 w - - 0 1")
    assert is_essential_defender(board, chess.E2) is True

def test_is_essential_defender_guardian():
    # White rook e1 is the only defender of the White knight on e5.
    board = chess.Board("4rk2/8/8/4N3/8/8/8/4R1K1 w - - 0 1")
    assert is_essential_defender(board, chess.E1) is True

def test_is_essential_defender_negative():
    # White rook a1 guards nothing; removing it changes nothing for allied pieces.
    board = chess.Board("7k/8/8/8/4N3/8/8/R3K3 w - - 0 1")
    assert is_essential_defender(board, chess.A1) is False

def test_is_essential_defender_empty_square():
    board = chess.Board("4rk2/8/8/4N3/8/8/8/4R1K1 w - - 0 1")
    assert is_essential_defender(board, chess.A4) is False


# ---------------------------------------------------------------------------
# controls_center
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("square", [chess.D4, chess.E4, chess.D5, chess.E5])
def test_controls_center_positive(square):
    assert controls_center(square) is True

@pytest.mark.parametrize("square", [chess.C3, chess.F6, chess.A1, chess.H8])
def test_controls_center_negative(square):
    assert controls_center(square) is False


# ---------------------------------------------------------------------------
# in_extended_center  (c3–f6, the 16-square zone)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("square", [
    chess.C3, chess.F3, chess.C6, chess.F6,  # corners of the zone
    chess.D4, chess.E5,                        # also in classical center
])
def test_in_extended_center_positive(square):
    assert in_extended_center(square) is True

@pytest.mark.parametrize("square", [
    chess.B4,  # file b — one step outside western edge
    chess.G4,  # file g — one step outside eastern edge
    chess.D2,  # rank 2 — one step below southern edge
    chess.E7,  # rank 7 — one step above northern edge
    chess.A1,
    chess.H8,
])
def test_in_extended_center_negative(square):
    assert in_extended_center(square) is False


# ---------------------------------------------------------------------------
# static_exchange_eval
#
# (a) Free capture — no defenders on the target square.
#
#   7k/8/8/3p4/8/4N3/8/7K
#   White knight e3 takes Black pawn d5; nothing defends d5.
#   SEE = +1 (wins the pawn outright).
#
# (b) Bad capture into a defended square.
#
#   7k/8/3p4/2p5/1Q6/8/8/7K
#   White queen b4 takes Black pawn c5, defended by Black pawn d6.
#   After Qxc5 the d6 pawn recaptures; White nets +1 (pawn) − +9 (queen) = −8.
#
# (c) Complex exchange — multiple attackers and defenders, X-ray reveal.
#
#   3r3k/8/2p5/3p4/8/4NB2/8/3R3K
#   White: Nе3, Bf3 (hidden behind Ne3 on the f3-d5 diagonal), Rd1 (d-file).
#   Black: pd5 (target), pc6, Rd8.
#
#   Sequence:
#     Nxd5 (+1).  Black pc6 recaptures (+3, cheapest).  White Bf3 revealed,
#     recaptures (+1, cheapest).  Black Rd8 recaptures (+3).  White Rd1
#     recaptures (+5).  No more Black pieces.
#
#   Backward pass (each side opts out when losing):
#     depth 4 raw = 5  → Black Rd8 recapture nets 3 − max(0,5) = −2 (Black stops).
#     depth 3 raw = 3  → White Bf3 nets  1 − max(0,−2) = +1 (White recaptures).
#     depth 2 raw = 1  → Black pc6 nets  3 − max(0, 1) = +2 (Black recaptures).
#     depth 1 raw = 3  → Nxd5 nets       1 − max(0, 2) = −1.
#   SEE = −1  (the initial knight capture is a slight loss).
#
# Additional cases: even exchange (SEE = 0) and non-capture (SEE = 0).
# ---------------------------------------------------------------------------

def test_see_free_capture():
    # Nxd5: pawn is undefended; knight wins it for free.
    board = chess.Board("7k/8/8/3p4/8/4N3/8/7K w - - 0 1")
    assert static_exchange_eval(board, chess.Move.from_uci("e3d5")) == 1

def test_see_bad_capture():
    # Qxc5: queen takes a pawn defended by another pawn.
    # White queen (9) captures pawn (1), Black d6-pawn recaptures queen.
    # Net: 1 − 9 = −8.
    board = chess.Board("7k/8/3p4/2p5/1Q6/8/8/7K w - - 0 1")
    assert static_exchange_eval(board, chess.Move.from_uci("b4c5")) == -8

def test_see_even_exchange():
    # Rxd8: rook trades for rook; Black's second rook on e8 recaptures.
    # Net: 5 (White wins rook) − 5 (Black recaptures rook) = 0.
    board = chess.Board("3rr2k/8/8/8/8/8/8/3R3K w - - 0 1")
    assert static_exchange_eval(board, chess.Move.from_uci("d1d8")) == 0

def test_see_complex_multiple_attackers():
    # Nxd5 with X-ray bishop behind knight and rook on the d-file.
    # Full exchange leads to SEE = −1 (Black's pawn recapture nets more than White gains).
    board = chess.Board("3r3k/8/2p5/3p4/8/4NB2/8/3R3K w - - 0 1")
    assert static_exchange_eval(board, chess.Move.from_uci("e3d5")) == -1

def test_see_non_capture_returns_zero():
    # Quiet moves have no victim; SEE must return 0 without error.
    board = chess.Board()
    assert static_exchange_eval(board, chess.Move.from_uci("e2e4")) == 0


def test_see_promotion_capture():
    # White pawn e7 captures undefended Black rook d8 with queen promotion.
    # The promotion branch sets current_piece_value to the promoted queen's value.
    # No Black defenders remain, so SEE = value of the captured rook = 5.
    board = chess.Board("3r4/4P3/8/8/8/8/8/K6k w - - 0 1")
    assert static_exchange_eval(board, chess.Move.from_uci("e7d8q")) == 5

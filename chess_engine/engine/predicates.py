"""
predicates.py — pure, composable boolean/numeric functions over chess positions.

Each function answers a single well-defined question about the board.
Nothing here has side-effects or depends on search state.
These are the building blocks for evaluation.py and search.py.
"""

import chess

# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------

_PIECE_VALUES: dict[chess.PieceType, int] = {
    chess.PAWN:   1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK:   5,
    chess.QUEEN:  9,
    chess.KING:   0,  # king loss is handled via checkmate, not material counting
}


def piece_value(piece: chess.Piece) -> int:
    """
    Returns the integer material value for a piece.
    King is 0 — its capture ends the game, so we never count it as capturable material.
    """
    return _PIECE_VALUES.get(piece.piece_type, 0)


# ---------------------------------------------------------------------------
# Attack / defense relations
# ---------------------------------------------------------------------------

def attackers_of(
    board: chess.Board, square: chess.Square, color: chess.Color
) -> chess.SquareSet:
    """
    The set of squares occupied by pieces of *color* that currently attack *square*.
    Handles all piece types (sliders, knights, pawns, king) via python-chess internals.
    """
    return board.attackers(color, square)


def defenders_of(board: chess.Board, square: chess.Square) -> chess.SquareSet:
    """
    The set of squares of same-color pieces that defend the piece on *square* —
    i.e., pieces that would recapture if an opponent captured there.
    Returns an empty SquareSet if *square* is unoccupied.

    Note: a piece cannot defend itself, so the piece on *square* is never included.
    """
    piece = board.piece_at(square)
    if piece is None:
        return chess.SquareSet()
    # board.attackers returns pieces of *color* attacking *square*;
    # the piece on *square* is never in that set (it occupies, not attacks, its own square).
    return board.attackers(piece.color, square)


def is_attacked(
    board: chess.Board, square: chess.Square, by_color: chess.Color
) -> bool:
    """True iff at least one piece of *by_color* attacks *square*."""
    return board.is_attacked_by(by_color, square)


def is_defended(board: chess.Board, square: chess.Square) -> bool:
    """
    True iff the piece on *square* has at least one same-color piece that defends it.
    False if the square is empty.
    """
    return bool(defenders_of(board, square))


def is_hanging(board: chess.Board, square: chess.Square) -> bool:
    """
    True iff a piece sits on *square*, is attacked by at least one opponent piece,
    and has zero same-color defenders.  A hanging piece can be captured for free.
    """
    piece = board.piece_at(square)
    if piece is None:
        return False
    opponent = not piece.color
    return is_attacked(board, square, opponent) and not is_defended(board, square)


# ---------------------------------------------------------------------------
# Pin and check
# ---------------------------------------------------------------------------

def is_pinned(board: chess.Board, square: chess.Square) -> bool:
    """
    True iff the piece on *square* is absolutely pinned to its own king —
    moving it would expose the king to check.
    Delegates to board.is_pinned(), which handles all slider directions.
    Returns False if the square is empty.
    """
    piece = board.piece_at(square)
    if piece is None:
        return False
    return board.is_pinned(piece.color, square)


def gives_check(board: chess.Board, move: chess.Move) -> bool:
    """
    True iff *move* (by the side to move) leaves the opponent's king in check.
    Covers direct checks, discovered checks, and double checks.
    Delegates to board.gives_check(), which handles all cases efficiently.
    """
    return board.gives_check(move)


# ---------------------------------------------------------------------------
# Compound tactical relations
# ---------------------------------------------------------------------------

def is_essential_defender(board: chess.Board, square: chess.Square) -> bool:
    """
    True iff removing the piece on *square* would harm the allied position in either
    of two ways:

      (a) The piece is absolutely pinned — moving it exposes the king to check.
      (b) At least one currently-safe allied piece would become hanging after removal
          (the piece was the only thing guarding it, or its removal opens a line).

    Useful for avoiding trades that quietly collapse the defence.
    """
    piece = board.piece_at(square)
    if piece is None:
        return False

    color = piece.color

    # (a) fast-path: a pinned piece is essential by definition
    if board.is_pinned(color, square):
        return True

    # (b) simulate removal and scan allied pieces for newly-hanging members
    test_board = board.copy()
    test_board.remove_piece_at(square)

    for sq in chess.SquareSet(test_board.occupied_co[color]):
        # A piece that was already hanging before removal doesn't count as "new" damage.
        if is_hanging(test_board, sq) and not is_hanging(board, sq):
            return True

    return False


def static_exchange_eval(board: chess.Board, move: chess.Move) -> int:
    """
    Returns the net material gained (positive) or lost (negative) from the
    sequence of captures on *move*'s destination square, assuming both sides
    always recapture with their least-valuable attacker and stop as soon as
    continuing would lose material.  Non-captures return 0.

    The algorithm (SEE):
      1. Record the value of the piece captured by the initial move.
      2. Simulate alternating recaptures, cheapest piece first, shrinking the
         occupied bitboard after each capture so X-ray pieces are revealed.
      3. Fold the gain array backwards so each side only recaptures when the
         net result is non-negative.
    """
    to_sq  = move.to_square
    victim = board.piece_at(to_sq)
    if victim is None:
        return 0  # not a capture

    attacker = board.piece_at(move.from_square)
    if attacker is None:
        return 0

    # gains[d] = raw value of the piece picked up at capture depth d.
    gains: list[int] = [piece_value(victim)]

    # What sits on to_sq after the initial move and can now be captured.
    # For promotions the pawn transforms, so use the promoted piece's value.
    if move.promotion is not None:
        current_piece_value = piece_value(chess.Piece(move.promotion, board.turn))
    else:
        current_piece_value = piece_value(attacker)

    # Remove the moving piece from the occupied mask so sliders can see past
    # its origin square (revealing any X-ray attacker behind it).
    occupied = board.occupied ^ chess.BB_SQUARES[move.from_square]

    side = not board.turn  # side that makes the first recapture
    while True:
        # board.attackers_mask accepts a custom occupied mask; the extra
        # `& occupied` drops any piece already removed during the simulation
        # (they are still in board.occupied_co but no longer "on the board").
        atk = board.attackers_mask(side, to_sq, occupied) & occupied
        if not atk:
            break

        # Least-valuable attacker: iterate piece types cheapest-first.
        for pt in (chess.PAWN, chess.KNIGHT, chess.BISHOP,
                   chess.ROOK, chess.QUEEN, chess.KING):
            lva_mask = board.pieces_mask(pt, side) & atk
            if lva_mask:
                lva_sq = chess.lsb(lva_mask)
                break

        gains.append(current_piece_value)
        current_piece_value = piece_value(chess.Piece(pt, side))  # type: ignore[possibly-undefined]

        # Remove the recaptor; its departure may reveal the next X-ray piece.
        occupied ^= chess.BB_SQUARES[lva_sq]  # type: ignore[possibly-undefined]
        side = not side

    # Backward pass: gains[i] = (what I capture) - max(0, what opponent nets next).
    # The max(0, …) is the opt-out: a side stops rather than recapture into a loss.
    for i in range(len(gains) - 2, -1, -1):
        gains[i] = gains[i] - max(0, gains[i + 1])

    return gains[0]


# ---------------------------------------------------------------------------
# Spatial relations
# ---------------------------------------------------------------------------

_CENTER_SQUARES = chess.SquareSet([chess.D4, chess.E4, chess.D5, chess.E5])

# c3–f6: files c(2)–f(5), ranks 3(2)–6(5) in 0-indexed (file, rank) coords
_EXTENDED_CENTER_SQUARES = chess.SquareSet(
    chess.square(f, r) for f in range(2, 6) for r in range(2, 6)
)


def controls_center(square: chess.Square) -> bool:
    """
    True iff *square* is one of the four classical center squares: d4, e4, d5, e5.
    Occupation of or influence over these squares is a core positional goal.
    """
    return square in _CENTER_SQUARES


def in_extended_center(square: chess.Square) -> bool:
    """
    True iff *square* lies within the 16-square extended center (c3–f6).
    Pieces placed here enjoy maximum mobility and influence over both wings.
    """
    return square in _EXTENDED_CENTER_SQUARES

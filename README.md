# LamarEngine

A chess engine written in Python, playable in the terminal or through any UCI-compatible chess GUI (Arena, ChessBase, Lichess via a bot account).

## Getting Started

**Requirements:** Python 3.10+, `python-chess`, `colorama`

```bash
cd chess_engine
pip install python-chess colorama

# Play against the engine in the terminal
python play.py

# Run as a UCI engine (connect to a chess GUI)
python uci.py
```

On Windows you can also launch the UCI mode via `lamar_engine.bat`, which activates the bundled virtual environment automatically.

In `play.py` you are White; the engine plays Black. Enter moves in UCI notation (`e2e4`, `g1f3`, `e1g1` for castling, `e7e8q` for promotion). Type `quit` to resign.

## How It Works

### Search — Negamax with Alpha-Beta Pruning

The engine searches to **4 plies** (2 full moves) by default using the [negamax](https://www.chessprogramming.org/Negamax) formulation of minimax with [alpha-beta pruning](https://www.chessprogramming.org/Alpha-Beta). Alpha-beta prunes branches that cannot influence the final result, making the search significantly faster without changing the outcome.

At each leaf node the engine drops into **quiescence search** instead of returning the static evaluation immediately. Quiescence search keeps looking at captures until the position is "quiet" (no more winning captures available), which avoids the [horizon effect](https://www.chessprogramming.org/Horizon_Effect) where the engine misses a recapture just beyond the search depth.

**Move ordering** — captures are searched first, sorted by MVV-LVA (Most Valuable Victim, Least Valuable Attacker), followed by checks, then quiet moves. Good move ordering maximises alpha-beta cutoffs.

### Evaluation — Static Position Score

Positions are scored in **centipawns** (100 cp = 1 pawn) from White's perspective. The score is the sum of five components:

| Component | What it measures |
|---|---|
| **Material** | Piece values: P=100, N=320, B=330, R=500, Q=900 |
| **Piece-square tables** | Positional bonuses per square per piece type (e.g. knights are penalised on the rim, kings are rewarded for castling) |
| **Hanging penalty** | Deducts the full value of any undefended piece that is under attack |
| **Mobility** | +2 cp per legal move of advantage over the opponent |
| **Center control** | +10 cp per attack on a core center square (d4/d5/e4/e5), +5 cp on the extended center |

### Tactical Helpers (`predicates.py`)

Pure functions used by the evaluator and search: `attackers_of`, `defenders_of`, `is_hanging`, `is_pinned`, `gives_check`, and a full [Static Exchange Evaluation (SEE)](https://www.chessprogramming.org/Static_Exchange_Evaluation) implementation that accurately values capture sequences accounting for X-ray reveals.

## Running Tests

```bash
cd chess_engine
python -m pytest tests/

# Single file
python -m pytest tests/test_search.py

# Single test
python -m pytest tests/test_search.py::test_mate_in_one
```

The test suite has 30+ tests covering evaluation, search (mate-in-1, mate-in-2 puzzles), and all predicate functions. Every test uses a concrete FEN position for full reproducibility.

## Project Structure

```
chess_engine/
├── engine/
│   ├── engine.py       # Public API: choose_move(board, depth)
│   ├── search.py       # Negamax, alpha-beta, quiescence search
│   ├── evaluation.py   # Static evaluator (material, PST, hanging, mobility, center)
│   └── predicates.py   # Pure tactical helpers (attackers, SEE, pins, checks)
├── tests/              # pytest suite
├── play.py             # Terminal game (human vs engine)
├── uci.py              # UCI protocol wrapper
└── lamar_engine.bat    # Windows launcher
```

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

This repo contains **LamarEngine**, a Python chess engine with UCI protocol support. All source lives in `chess_engine/`.

## Setup & Running

```bash
cd chess_engine

# Interactive human vs engine game
python play.py

# UCI protocol mode (for chess GUIs like Arena or ChessBase)
python uci.py
# Or use the Windows launcher:
lamar_engine.bat
```

Dependencies: `python-chess`, `colorama`. A `venv/` is already present in `chess_engine/`.

## Running Tests

```bash
cd chess_engine
python -m pytest tests/

# Single test file
python -m pytest tests/test_search.py

# Single test
python -m pytest tests/test_search.py::test_mate_in_one
```

## Architecture

The engine is split into four modules under `chess_engine/engine/`:

1. **`engine.py`** — Public API. Exports `choose_move(board, depth)` which returns `(move, score_in_centipawns)`. All callers go through this.

2. **`search.py`** — Negamax with alpha-beta pruning and quiescence search.
   - `find_best_move(board, depth=4)` is the entry point.
   - `quiescence()` extends the search at leaf nodes (captures only) to avoid the horizon effect.
   - `_order_moves()` sorts moves by MVV-LVA for better alpha-beta cutoffs.

3. **`evaluation.py`** — Static position evaluator returning centipawns (100 cp = 1 pawn). Components: material (piece values), piece-square tables, hanging piece penalty, mobility (+2 cp/extra move), center control.

4. **`predicates.py`** — Pure, side-effect-free tactical helpers used by evaluation and search: `attackers_of()`, `defenders_of()`, `is_hanging()`, `is_pinned()`, `gives_check()`, `static_exchange_eval()` (SEE), `controls_center()`.

`play.py` is the interactive terminal front-end (human = White, engine = Black, UCI notation input). `uci.py` wraps the engine in the UCI protocol for GUI integration.

## Key Extension Points

- **Evaluation weights:** material values and PST (piece-square table) arrays are defined as module-level constants in `evaluation.py`.
- **Search depth:** default depth is 4 in `find_best_move()`; `play.py` and `uci.py` pass this through.
- **Adding evaluation terms:** add a new scoring function in `evaluation.py` and sum it into `evaluate()`. If it needs attack/defense info, add predicates to `predicates.py`.
- **UCI options:** extend the `uci` / `setoption` handling block in `uci.py`.

## Test Conventions

All tests use concrete FEN strings to set up positions — never rely on engine self-play for reproducibility. `test_predicates.py` covers the lowest-level functions; `test_search.py` uses known tactical puzzles (mate-in-1, mate-in-2) to validate the search.

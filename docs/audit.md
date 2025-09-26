# Audit – Current State vs. Roadmap

## Phase 1: Foundations & Architecture
- Project layout (`src/app/...`) ✔
- Registry ✔
- Config/Prefs ✔ (QSettings for FPS/input/theme, VizConfig overrides)
- Logging/crash handler ✔

## Phase 2: Correctness & Tests
- Unit/property tests ✔
- Step replay determinism ✔
- Static quality ✔ (`ruff`, `black`, `mypy`, pre-commit)

## Phase 3: Algorithms
Implemented and fully covered:
- Bubble Sort
- Insertion Sort
- Selection Sort
- Heap Sort
- Shell Sort
- Cocktail Shaker Sort
- Comb Sort
- Quick Sort
- Merge Sort (bottom-up trace)
- Counting Sort
- Radix Sort LSD
- Bucket Sort
- Timsort Trace

Outstanding priorities:
1. Algorithm metadata surfaced in UI (Phase 4).
2. Compare mode and explanations panel.
3. Remaining non-visual optimisations (canvas batching, seeds, JSON/GIF export).

## Phase 4: UI/UX Polish
- Legend, manual step controls, value labels DONE
- Remaining high-impact items:
  * Toolbar/menu + shortcuts
  * Theme toggle (light/dark), high-contrast / accessibility
  * Data presets menu (random, reverse, nearly-sorted, seeded)
  * Compare mode & explanations panel (algorithm metadata display)

## Phase 5+: Deferred
- Canvas batching / OpenGL backend
- Dynamic FPS reduction when idle/offscreen
- Advanced playback controls
- Seeded runs, export formats (JSON, PNG, GIF), benchmark runner
- CI matrix, installers, docs, community files

## Immediate Next Steps (Suggested)
1. Expose algorithm metadata in the UI (compare mode + explanations panel).
2. Implement data presets + seeded RNG with deterministic HUD display.
3. Add JSON/PNG/GIF export and benchmark mode (Phase 6).

## Latest Regression Run (2024-XX-XX)
- `ruff check` → pass
- `mypy src tests contrast_checker.py` → pass (20+ files)
- `pytest -q` → pass (14 tests)
- `pytest tests/test_step_invariants.py -q` → pass (2 tests)

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
- Counting Sort
- Radix Sort LSD
- Bucket Sort
- Iterative Merge Sort (bottom-up)
- Iterative Quick Sort (median-of-three)

Outstanding priorities:
1. Comb Sort (optional comparison variant)
2. Radix Sort (LSD)
3. Bucket Sort
4. Timsort trace / advanced visual

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
1. Implement **Heap Sort** with full Step instrumentation and integrate into registry/tests.
2. Implement **Shell Sort** or **Comb/Cocktail Sort** to round out comparison algorithms.
3. Add metadata exposure in UI (tab labels or forthcoming explanations panel).
4. Begin work on data presets + seeded RNG once core algorithms are in place.

## Latest Regression Run (2024-XX-XX)
- `ruff check` → pass
- `mypy src tests contrast_checker.py` → pass (20+ files)
- `pytest -q` → pass (14 tests)
- `pytest tests/test_step_invariants.py -q` → pass (2 tests)

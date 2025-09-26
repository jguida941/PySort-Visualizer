# Project Phase Snapshot

This summary captures the current roadmap progress. For the full breakdown, see [ROADMAP.md](ROADMAP.md).

## Phase Status

- **Phase 1 – Foundations**: ✓ complete (project layout, registry, VizConfig, crash-safe logging).
- **Phase 2 – Correctness & Tests**: ✓ complete (property tests, replay determinism, strict mypy/ruff/black).
- **Phase 3 – Algorithms**: ✓ complete
  - Comparison sorts: Bubble, Insertion, Selection, Heap, Shell, Cocktail Shaker, Comb, Quick, Merge.
  - Non-comparison sorts: Counting, Radix LSD, Bucket.
  - Advanced: Timsort Trace.
- **Phase 4 – UI/UX Polish**: In progress
  - TODO: toolbar/menu, theme toggle, data presets, compare mode, explanations panel, accessibility improvements.
- **Phase 5 – Performance & Rendering**: Not started
  - Planned: canvas batching, optional OpenGL backend, dynamic FPS throttling, advanced playback controls.
- **Phase 6 – Data, Export & Replay**: Not started
  - Planned: deterministic seeds, JSON/PNG/GIF export, benchmark mode.
- **Phase 7 – CI/CD & Distribution**: Not started
  - Planned: GitHub Actions matrix, installer pipeline, changelog/versioning.

## Next Focus

1. Phase 4 polish (toolbar/menu, theme toggle, explanations panel, accessibility).
2. Phase 5 performance enhancements (canvas batching, OpenGL option, idle throttling).
3. Phase 6 data/export features (seeded runs, session export, GIF/PNG output, benchmarks).
4. Phase 7 automation/distribution (CI matrix, installers, release process).

Regression suite currently passes (`ruff`, `black --check`, `mypy src tests contrast_checker.py`, `pytest -q`).

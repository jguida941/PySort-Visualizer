# Production-Grade Feature Roadmap

This document outlines the plan to elevate the project to a production-grade application with more features, algorithms, and polish.

## Phase 1: Foundations & Architecture
**Goals:** Clean repo, consistent style, plug-in algorithms, rock-solid correctness.

- [x] **Project Layout:** Refactor the project into a more standard layout (baseline `src/app` structure in place; `ui/` and `presets/` modules stubbed for upcoming work):
    - `app/core/`: Step model, playback, checkpoints, metrics
    - `app/ui/`: widgets, styles, icons, resources.qrc
    - `app/algos/`: each algorithm in its own module
    - `app/presets/`: data generators (random, nearly-sorted, etc.)
    - `tests/`
    - `pyproject.toml`
- [x] **Algorithm Registry:** Implement a plugin architecture for algorithms using a registry.
- [ ] **Config & Prefs:**
    - [x] Use `QSettings` for FPS, theme, last array, window geometry.
    - [x] Use a single source of truth `VizConfig`, with overrides from settings/env.
- [x] **Error Handling & Logging:**
    - [x] Keep rotating file handler.
    - [x] Add global `sys.excepthook` for a user-friendly crash dialog.

## Phase 2: Correctness & Tests
**Goals:** Every algorithm proven correct; step replay is deterministic.

- [x] **Unit Tests (pytest):**
    - [x] For each algorithm: test with random arrays, duplicates, already sorted, reverse, few-unique.
    - [x] Cross-check: `final_array == sorted(original)`.
- [x] **Property-Based Tests (hypothesis):**
    - [x] Test with various sizes and integer ranges.
- [x] **Step-Replay Test:**
    - [x] Rebuild array by applying emitted `Step` objects and assert it matches the internal result.
- [ ] **Static Quality:**
- [x] **Static Quality:**
    - [x] `ruff`, `black`, `mypy --strict`.
    - [x] `pre-commit` to enforce locally.

## Phase 3: Algorithms
**Priority Order:**

- [ ] **Core Algorithms:**
    - [ ] Insertion Sort (stable, in-place)
    - [ ] Selection Sort (in-place)
    - [ ] Heap Sort (in-place, O(n log n))
    - [ ] Shell Sort (gap sequences)
    - [ ] Cocktail Shaker / Comb Sort
- [ ] **Non-Comparison Algorithms:**
    - [ ] Counting Sort
    - [ ] Radix Sort LSD
    - [ ] Bucket Sort
- [ ] **Advanced:**
    - [ ] Timsort "trace" (simplified)
- [ ] **Algorithm Metadata:**
    - [ ] Expose metadata for each algorithm (stable, in-place, complexity) in the UI.

## Phase 4: UI/UX Polish
**Goals:** Consistent, delightful, accessible.

- [ ] **Hollow-Glass Theme:** Ensure the theme is consistent across all controls.
- [ ] **Toolbar & Menu Bar:**
    - [ ] Create a main toolbar and menu bar with shortcuts.
- [ ] **Themes:**
    - [ ] Dark (default) + Light theme toggle.
    - [ ] Persist theme in `QSettings`.
- [ ] **Data Presets Menu:**
    - [ ] Add a menu for generating different kinds of data (random, nearly sorted, etc.).
- [ ] **Side-by-Side Compare Mode:**
    - [ ] Implement a split view to run two algorithms on the same data.
- [ ] **Explanations Panel:**
    - [ ] Add a panel with a description and complexity table for each algorithm.
- [ ] **Accessibility:**
    - [ ] Larger UI scale option.
    - [ ] High-contrast mode.
    - [ ] Keyboard-only navigation.
    - [ ] Tooltips on all controls.

## Phase 5: Performance & Rendering
- [ ] **Canvas Optimization:**
    - [ ] Batch draw operations using `QPainterPath`.
    - [ ] Optional `QOpenGLWidget` backend for large datasets.
- [ ] **Dynamic FPS:**
    - [ ] Cap repaint when offscreen/minimized.
    - [ ] Lower FPS when idle.
- [ ] **Playback Controls:**
    - [ ] "Scrub speed" control.
    - [ ] "Jump to next swap/compare" buttons.

## Phase 6: Data, Export & Replay
- [ ] **Deterministic Seeds:** Show the random seed in the HUD and allow re-running with the same seed.
- [ ] **Import/Export:**
    - [ ] JSON session export/import (config, seed, steps, etc.).
    - [ ] Export PNG of the current frame.
    - [ ] Export GIF of the full run.
- [ ] **Benchmark Mode:**
    - [ ] Run N trials per algorithm/preset and export results as CSV.

## Phase 7: CI/CD & Distribution
- [ ] **GitHub Actions:**
    - [ ] CI matrix for Ubuntu/macOS/Windows (lint, type-check, tests).
- [ ] **Build Artifacts (PyInstaller/Briefcase):**
    - [ ] macOS `.dmg`
    - [ ] Windows `.exe`
    - [ ] Linux `AppImage`
- [ ] **Versioning:** Use SemVer and maintain a changelog.
- [ ] **Crash Reporting:** Prompt user to open the log folder on crash.

## Phase 8: Docs & Community
- [ ] **Documentation:**
    - [ ] README with screenshots/GIFs.
    - [ ] User Guide.
    - [ ] Algorithm Notes.
- [ ] **Community Files:**
    - [ ] `CONTRIBUTING.md`
    - [ ] `CODE_OF_CONDUCT.md`
- [ ] **In-App Help:**
    - [ ] "What’s this color?" legend.
    - [ ] "Learn more" links.

## Backlog (Prioritized)
1.  [x] Registry + refactor existing Bubble/Quick/Merge to use it.
2.  [x] Tests: unit + hypothesis; step-replay harness.
3.  [ ] New algos: Insertion → Heap → Shell → Radix LSD.
4.  [ ] Presets + seeded RNG; HUD shows seed.
5.  [ ] Compare mode (two canvases; shared controls).
6.  [ ] JSON session export/replay.
7.  [ ] Benchmark runner (per-algo, per-preset).
8.  [ ] Theme toggle + accessibility polish.
9.  [ ] CI matrix + installers.
10. [ ] Docs pass + demo videos/GIFs.

# Sorting Algorithm Visualizer

A production-grade, research-friendly PyQt6 desktop application for studying sorting algorithms.  
Every animation frame is backed by an explicit stream of `Step` records, ensuring deterministic replay, reproducible metrics, and faithful narration for each algorithmic operation.

---

## Highlights

- **Instrumented algorithms** — Bubble, Insertion, Iterative Quick (median-of-three), and Bottom‑Up Merge Sort register themselves through a plugin registry. Each yields richly-typed `Step` objects so the UI, narration, and tests stay in lockstep.
- **Deterministic replay** — Checkpoints capture array snapshots/metrics every *n* steps (`VizConfig.checkpoint_stride`). Seeking restores the nearest checkpoint, replays intervening steps, and guarantees the HUD, highlights, and narration remain coherent.
- **Manual & automated playback** — `Step ▶`/`Step ◀` buttons advance or rewind one step at a time (even before a full run), while the timer provides smooth animation at user-selected FPS. Scrubbing, keyboard shortcuts, and narration updates respect both modes.
- **Color-coded semantics** — Dedicated highlight channels clarify intent:
  - Cyan = key being inserted (`Step("key", ...)`)
  - Orange = shift writes during insertion (`Step("shift", ...)`)
  - Yellow = comparisons
  - Red = swaps
  - Green = pivots / finish confirmations
  - Violet = merge ranges
  A legend beneath the log explains the palette in the running app.
- **Robust crash handling** — A hardened `sys.excepthook` writes to a rotating log under the user’s log directory (via `platformdirs`) and displays a critical dialog only when a `QApplication` exists.
- **Persistence** — User FPS, last input array, window geometry, and UI theme preferences round-trip automatically through `QSettings` (`org.pysort/sorting-visualizer`).
- **Production toolchain** — `ruff`, `black`, `mypy --strict`, and `pytest` all pass; algorithms are validated with property-based tests, determinism checks, and replay harnesses.

---

## Repository Layout

```
MergeSortAlgorithm-master/
├── README.md
├── main.py                      # CLI entry point → src/app/app.py
├── pyproject.toml               # build + lint/type settings
├── requirements.txt
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── algos/
│   │   │   ├── bubble.py
│   │   │   ├── insertion.py
│   │   │   ├── merge.py
│   │   │   ├── quick.py
│   │   │   └── registry.py
│   │   ├── app.py               # Main window composition
│   │   └── core/
│   │       ├── base.py          # AlgorithmVisualizerBase & canvas
│   │       ├── replay.py        # apply_step_sequence utilities
│   │       └── step.py          # Step dataclass / contract
│   └── sorting_viz.egg-info/ …
├── tests/
│   ├── conftest.py              # Spins up shared QApplication
│   ├── test_algorithms_property.py
│   ├── test_step_determinism.py
│   └── test_step_replay.py
├── docs/
│   └── Screenshot …             # Reference UI snapshot
└── logs/                        # Populated at runtime (ignored if absent)
```

---

## Installation & First Run

```bash
python -m venv .venv
source .venv/bin/activate             # Windows: .\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt       # or: pip install -e ".[dev]"
python main.py
```

> **Tip:** Always launch through `python main.py`. The script wires up `QApplication` with the correct organization/app identifiers so QSettings and logging land in predictable locations.

The application has been verified on macOS 14, Windows 11, and Ubuntu 24.10 with Python 3.10+. Property tests rely on `hypothesis`; headless execution uses Qt’s “offscreen” platform via the pytest fixture in `tests/conftest.py`.

---

## Feature Tour

### Algorithm Registry
- `src/app/algos/registry.py` exposes a frozen `AlgoInfo` dataclass (`name`, `stable`, `in_place`, `comparison`, `complexity`) and a decorator-based registration API.
- Clients import `app.algos.<algo>`; module import side-effects populate `REGISTRY` and `INFO` dictionaries keyed by human-readable names (“Bubble Sort”, “Insertion Sort”…).
- The app window iterates sorted `INFO` keys to build tabs dynamically. Tests do the same to guarantee coverage for every registered algorithm.

### Step Contract (`Step` dataclass)
Supported operations currently include:
- `compare(i, j)` — increments comparison counter, paints indices yellow.
- `swap(i, j)` — mutates the array, increments swap counter, paints red.
- `pivot(p)` — highlights quicksort pivots.
- `merge_mark(lo, hi)` — violet band for the merge subsequence.
- `merge_compare(i, j, payload=k)` — compare + mark destination index.
- `set(k, payload=value)` — writes a value (merge final placement, insertion drop-in).
- `shift(k, payload=value)` — visually distinct orange write (insertion shift).
- `key(i, payload=value)` / `key()` — cyan highlight for the held insertion key (empty tuple clears highlight).
- `confirm(i)` — finish sweep coloring.

All algorithms operate on the same contract; replay code treats `shift` exactly like `set` for state reconstruction.

### Visualization Canvas
- Stateless `VisualizationCanvas` queries `AlgorithmVisualizerBase._get_canvas_state()` each paint cycle. The state contains the live array, highlight tuples, confirmed indices, and HUD metrics.
- Bars render gap-aware and scale with window size. Highlight precedence ensures confirm > key > shift > swap > compare > pivot > merge > base.
- A HUD (top-left) displays algorithm name, `n`, FPS, comparison/swap totals, and elapsed seconds; the bottom-right legend clarifies colors.
- Optional value labels draw on each bar when the user toggles “Show values” or when a finished array has ≤40 elements.

### Manual Step Control & Narration
- `Step ▶` button (or → key) advances even if the timer never ran. The first press parses input, captures checkpoints, and primes the generator. Subsequent presses consume existing recorded steps before pulling more from the generator.
- `Step ◀` rewinds by replaying from the last checkpoint to the desired index; UI state, narration, and highlights reflect the exact historical step.
- Narration sentences derive from `_narrate_step`, using `safe_get` to guard against out-of-range indices after scrubbing.

### Persistence & Logging
- `VizConfig.from_settings()` merges environment overrides (`SORT_VIZ_*`) with QSettings values, coercing types with `typing.get_type_hints` to respect postponed annotations.
- FPS slider value, recent input, and theme are persisted automatically once changed.
- Logs (`sorting_viz.log`) rotate at 1 MB ×5, written to `platformdirs.user_log_dir("sorting-visualizer", "org.pysort")` or the workspace `logs/` fallback. Crash dialogs only display when a GUI app instance exists; otherwise a stderr message prompts the user to check the log.

### Tests
- `pytest -q` exercises deterministic behaviour, property checks (Hypothesis up to 60 integers, −1000..1000), and step replay invariants.
- `mypy src` runs under `--strict`; Qt stubs are ignored via `ignore_missing_imports = true` to work around incomplete PyQt6 type hints.
- `ruff` (style, pyupgrade, import sort) and `black` keep the codebase consistent; the repo ships with `.pre-commit-config.yaml` so hooks can be installed locally.

---

## Algorithms in Detail

| Algorithm        | Stable | In-Place | Complexity                         | Highlights                                                                          |
|------------------|:------:|:--------:|------------------------------------|--------------------------------------------------------------------------------------|
| Bubble Sort      | ✓      | ✓        | Best `O(n)`, Avg/Worst `O(n²)`     | Yellow comparisons, red swaps; early-exit when a pass has zero swaps.               |
| Insertion Sort   | ✓      | ✓        | Best `O(n)`, Avg/Worst `O(n²)`     | Cyan key highlight, orange shifts, green placement confirmation, yellow compares.  |
| Quick Sort       | ✗      | ✓        | Best/Avg `O(n log n)`, Worst `O(n²)` | Median-of-three pivot selection, pivots highlighted green, swaps recorded with payloads. |
| Merge Sort       | ✓      | ✗        | `O(n log n)` best/avg/worst        | Violet merge windows, yellow comparisons, orange merge writes, deterministic bottom-up passes. |

These stability and in-place columns reflect the classical algorithmic properties (not implementation bugs): Bubble and Insertion Sort are naturally stable and in-place, Quick Sort (with standard Lomuto partition) is not stable but remains in-place, and Bottom-Up Merge Sort is stable but requires auxiliary storage.

Each implementation mutates its working copy in sync with emitted steps so that `apply_step_sequence(original, steps)` equals both the generator’s final array and Python’s `sorted(original)`.

---

## Running & Developing

### Launching the App
- Enter integers separated by commas *or* leave blank and click **Randomize**.
- Use **Show values** to annotate bars; the app auto-enables labels after the last step when `n ≤ 40`.
- Scrub, step, or let the animation play; narration keeps up in all modes.
- Click **Export CSV** to capture the entire `Step` trace (index, op, indices, payload).

### Running the QA Suite
```bash
ruff check src tests
black src tests
mypy src
pytest -q
```

### Adding a New Algorithm
1. Create `src/app/algos/<name>.py` with a generator returning `Iterator[Step]`.
2. Decorate the function with `@register(AlgoInfo(...))` and provide accurate metadata.
3. Update `src/app/app.py` and the test modules’ import list (or rely on module discovery if you add automated import logic).
4. Emit existing ops (`compare`, `swap`, `set`, etc.) or introduce new ones — just update `Step`, `_apply_step`, the canvas color map, and tests accordingly.
5. Add property tests if the algorithm introduces new invariants (e.g., counting sort ranges, heap property).

---

## Roadmap Snapshot

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Foundations | ✓ Complete | src/app layout, registry, VizConfig, crash-safe logging |
| 2. Correctness | ✓ Complete | Property tests, replay determinism, mypy strictness |
| 3. Algorithms  | In Progress | Bubble, Insertion, Merge, Quick done. Upcoming: Selection, Heap, Shell, Radix LSD, Counting, Bucket, Timsort trace |
| 4. UI/UX      | In Progress | Hollow-glass theme + color legend shipped; toolbar/menu, theme toggle, compare mode, explanations panel pending |
| 5. Performance | Planned | Canvas batching, OpenGL toggle, dynamic FPS |
| 6. Data/Export | In Progress | CSV export live; seeded presets, JSON import/export, PNG/GIF, benchmark mode TBD |
| 7. CI/CD       | Planned | Need GitHub Actions matrix, installer pipelines |
| 8. Docs        | In Progress | README + roadmap exist; still need CONTRIBUTING, user guide, algorithm notes |

---

## Logging, Support, & License

- Logs: `~/Library/Logs/org.pysort/sorting-visualizer/` (macOS) or the platformdirs equivalent on Windows/Linux.
- Issues/PRs: please include failing steps / seed and attach the exported step CSV when bug-reporting visual discrepancies.
- License: Educator Non-Commercial (see `LICENSE.txt`). Commercial usage requires explicit permission.

Maintainer: **Justin Guida** — justn.guida@snhu.edu

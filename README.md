# 🧩 Sorting Algorithm Visualizer

A production-grade, research-friendly PyQt6 visualizer for sorting algorithms and data structures **built for educators, students, and curious engineers** to explore algorithms through visual, step-by-step interaction, because seeing is the best way to learn.

Every animation frame is backed by an explicit stream of Step records, ensuring deterministic replay, reproducible metrics, and faithful narration of each operation.

**From bubble to quick and merge: compare, replay, and measure, all in one PyQt6 desktop tool.**

---
## Bubble Sort
<img width="1196" height="863" alt="Screenshot 2025-09-24 at 10 04 57 PM" src="https://github.com/user-attachments/assets/d0890b71-0cf3-4524-852b-1460731cac60" />

## Insertion Sort
<img width="1196" height="862" alt="Screenshot 2025-09-24 at 10 05 13 PM" src="https://github.com/user-attachments/assets/3efada78-2c30-4170-8ea4-e0770952a4e0" />

## Merge Sort
<img width="1198" height="870" alt="Screenshot 2025-09-24 at 10 05 33 PM" src="https://github.com/user-attachments/assets/b39540ec-da03-49f7-83c7-a479b16e32f0" />

## Quick Sort
<img width="1192" height="869" alt="Screenshot 2025-09-24 at 10 05 53 PM" src="https://github.com/user-attachments/assets/d429b449-798e-4d88-b59a-f573cc720f6b" />

## CSV Export
<img width="1191" height="873" alt="Screenshot 2025-09-24 at 10 06 22 PM" src="https://github.com/user-attachments/assets/6da7494c-9210-465f-bb83-a0428e118929" />


## Highlights

- **Instrumented algorithms**: Bubble, Insertion, Iterative Quick (median-of-three), and Bottom‑Up Merge Sort register themselves through a plugin registry. Each yields richly-typed `Step` objects so the UI, narration, and tests stay in lockstep.
- **Deterministic replay**: Checkpoints capture array snapshots/metrics every *n* steps (`VizConfig.checkpoint_stride`). Seeking restores the nearest checkpoint, replays intervening steps, and guarantees the HUD, highlights, and narration remain coherent.
- **Manual & automated playback**: `Step ▶`/`Step ◀` buttons advance or rewind one step at a time (even before a full run), while the timer provides smooth animation at user-selected FPS. Scrubbing, keyboard shortcuts, and narration updates respect both modes.
- **Color-coded semantics**: Dedicated highlight channels clarify intent:
  - Cyan = key being inserted (`Step("key", ...)`)
  - Orange = shift writes during insertion (`Step("shift", ...)`)
  - Yellow = comparisons
  - Red = swaps
  - Green = pivots / finish confirmations
  - Violet = merge ranges
  A legend beneath the log explains the palette in the running app.
- **Robust crash handling**: A hardened `sys.excepthook` writes to a rotating log under the user’s log directory (via `platformdirs`) and displays a critical dialog only when a `QApplication` exists.
- **Persistence**: User FPS, last input array, window geometry, and UI theme preferences round-trip automatically through `QSettings` (`org.pysort/sorting-visualizer`).
- **Production toolchain**: `ruff`, `black`, `mypy --strict`, and `pytest` all pass; algorithms are validated with property-based tests, determinism checks, and replay harnesses.

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
├── native/
│   └── radix_simd.cpp           # Standalone Apple NEON sample (see README)
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
- `ruff` (style, pyupgrade, import sort) and `black` keep the codebase consistent; add them to your own pre-commit hooks if you want automatic formatting.
- A standalone Apple NEON radix-sieve sample lives in `native/radix_simd.cpp`. Build it with `clang++` on Apple silicon for SIMD experimentation separate from the PyQt application.

---

## Algorithms in Detail

| Algorithm             | Stable | In-Place | Type         | Complexity (best / avg / worst)       | Highlights                                                                             |
|-----------------------|:------:|:--------:|--------------|----------------------------------------|----------------------------------------------------------------------------------------|
| Bubble Sort           | ✓      | ✓        | Comparison   | `O(n)` / `O(n²)` / `O(n²)`            | Yellow comparisons, red swaps; early-exit when a pass has zero swaps.                 |
| Insertion Sort        | ✓      | ✓        | Comparison   | `O(n)` / `O(n²)` / `O(n²)`            | Cyan key highlight, orange shifts, green placement confirmation, yellow compares.    |
| Selection Sort        | ✗      | ✓        | Comparison   | `O(n²)` / `O(n²)` / `O(n²)`           | Tracks current minimum with a cyan key; confirms ends of the array first.            |
| Heap Sort             | ✗      | ✓        | Comparison   | `O(n log n)` / `O(n log n)` / `O(n log n)` | Max-heap build and sift-down steps recorded with compare/swap events.             |
| Shell Sort            | ✗      | ✓        | Comparison   | `O(n log n)` / `O(n²)` / `O(n²)`       | Gap-based insertion with `shift` events; final `key()` clears highlight.             |
| Cocktail Shaker Sort  | ✓      | ✓        | Comparison   | `O(n)` / `O(n²)` / `O(n²)`            | Bi-directional bubble passes; ends get confirmed after each sweep.                   |
| Comb Sort             | ✗      | ✓        | Comparison   | `O(n log n)` / `O(n²)` / `O(n²)`       | Shrinking gap (factor 1.3) removes turtles; finish sweep confirms every element.     |
| Quick Sort            | ✗      | ✓        | Comparison   | `O(n log n)` / `O(n log n)` / `O(n²)` | Median-of-three pivot selection, pivots highlighted green, swaps recorded with payloads. |
| Merge Sort            | ✓      | ✗        | Comparison   | `O(n log n)` / `O(n log n)` / `O(n log n)` | Violet merge windows, yellow comparisons, orange merge writes, deterministic bottom-up passes. |
| Timsort Trace         | ✓      | ✗        | Comparison   | `O(n)` / `O(n log n)` / `O(n log n)`   | Detects runs (via insertion sort) then merges them; approximates Python's Timsort trace. |
| Counting Sort         | ✓      | ✗        | Non-comparison | `O(n + k)` / `O(n + k)` / `O(n + k)` | Uses buckets indexed by value; writes back with `set` + cyan key highlights.         |
| Radix Sort (LSD)      | ✓      | ✗        | Non-comparison | `O(d(n + k))` across passes           | Offsets negatives once, then leverages stable per-digit counting to churn through integers efficiently; every placement is streamed via `set`. |
| Bucket Sort           | ✓      | ✗        | Non-comparison | `O(n)` / `O(n + k)` / `O(n²)`         | Normalizes values into buckets, sorts locally, replays as stable writes.             |

These stability and in-place columns reflect the classical algorithmic properties (not implementation bugs): Bubble and Insertion Sort are naturally stable and in-place, Quick Sort (with standard Lomuto partition) is not stable but remains in-place, and Bottom-Up Merge Sort is stable but requires auxiliary storage.

Each implementation mutates its working copy in sync with emitted steps so that `apply_step_sequence(original, steps)` equals both the generator’s final array and Python’s `sorted(original)`.

### Performance Notes

- **Linear-time specialists.** Counting Sort and Radix Sort (LSD) excel on integer datasets when the range (`k`) or number of digits (`d`) remain modest. Radix offsets negatives a single time and then streams stable per-digit counting passes, making it a go-to choice for large integer workloads.
- **Distribution-aware Bucket Sort.** Bucket Sort normalizes values into `n` buckets and sorts inside each bucket using Python’s highly optimised Timsort. It performs best when values are uniformly distributed; in adversarial cases where all elements land in one bucket, the complexity degrades toward quadratic.
- **Run-aware Timsort trace.** The Timsort trace algorithm models Python’s hybrid sorter by detecting short ascending runs (sorted via insertion sort) before merging them with a merge-sort style pass. It achieves linear time on already sorted data and stays `O(n log n)` in the worst case.
- **Gap-based accelerators.** Shell Sort and Comb Sort reduce “turtles” (small values trapped near the end of the array) far faster than pure quadratic sorts by comparing elements `gap` positions apart before finishing with insertion/bubble behaviour.
- **General-purpose workhorses.** Quick Sort remains the fastest comparison sort on average, Heap Sort guarantees `O(n log n)` regardless of input, and Merge Sort provides stability with predictable performance.
- **Nearly sorted data.** Insertion Sort and Cocktail Shaker Sort run in linear time when the input is almost sorted. Bubble and Selection Sort remain in the suite mainly as pedagogical baselines.

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
| 3. Algorithms  | ✓ Complete | Bubble, Insertion, Selection, Heap, Shell, Cocktail, Comb, Quick, Merge, Counting, Radix LSD, Bucket, Timsort trace |
| 4. UI/UX      | In Progress | Hollow-glass theme + legend shipped; toolbar/menu, theme toggle, compare mode, explanations panel pending |
| 5. Performance | Planned | Canvas batching, optional OpenGL backend, dynamic FPS throttling |
| 6. Data/Export | In Progress | CSV export live; seeded presets, JSON/PNG/GIF export, benchmark mode TBD |
| 7. CI/CD       | Planned | Need GitHub Actions matrix, installer pipelines |
| 8. Docs        | In Progress | README + roadmap exist; still need CONTRIBUTING, user guide, algorithm notes |

---

## Logging, Support, & License

- Logs: `~/Library/Logs/org.pysort/sorting-visualizer/` (macOS) or the platformdirs equivalent on Windows/Linux.
- Issues/PRs: please include failing steps / seed and attach the exported step CSV when bug-reporting visual discrepancies.
- License: Educator Non-Commercial (see `LICENSE.txt`). Commercial usage requires explicit permission.

Maintainer: **Justin Guida** — justn.guida@snhu.edu

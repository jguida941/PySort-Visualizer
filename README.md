# Sorting Algorithm Visualizer (PyQt6)

## Overview

This project is a desktop visualization suite for comparison-based sorting algorithms, written in Python and PyQt6. It combines rigorous algorithmic instrumentation with an extensible UI framework, allowing users to observe sorting behaviour step-by-step, scrub through execution history, export traces, and read natural-language narration describing each operation. The codebase is structured for research-grade reproducibility: every visual effect is driven by explicit `Step` records, ensuring deterministic playback even after scrubbing or re-running an algorithm.

Key goals:

- Provide faithful, instrumented implementations of Bubble Sort, iterative Quick Sort (median-of-three Lomuto partition), and bottom-up Merge Sort.
- Offer a reusable base class (`AlgorithmVisualizerBase`) that handles UI composition, animation timing, narration, metrics, scrubbing, and CSV export.
- Maintain scientific transparency by keeping swap narration stateless (values are embedded in the log) and by recording checkpoints for deterministic rewinds.

## Bubble Sort
<img width="1195" height="889" alt="Screenshot 2025-09-24 at 4 29 44 PM" src="https://github.com/user-attachments/assets/daf9c1b0-a47e-41ce-8943-ac38025a1c89" />

## Quick Sort
<img width="1189" height="871" alt="Screenshot 2025-09-24 at 4 29 54 PM" src="https://github.com/user-attachments/assets/57f80bd9-7a16-45a0-b132-accb7261aec3" />

## Merge Sort

<img width="1194" height="875" alt="Screenshot 2025-09-24 at 4 30 04 PM" src="https://github.com/user-attachments/assets/6b41e5e3-d5ee-4ff0-8698-d3aaa4b591c0" />


## Repository Layout

```
MergeSortAlgorithm-master/
├── base.py                  # Shared PyQt6 widget providing UI, timing, narration, scrub, export.
├── bubblesort_visualizer.py # Bubble sort subclass using the base framework.
├── quicksort_visualizer.py  # Iterative Quick Sort subclass (median-of-three + Lomuto partition).
├── mergesort_visualizer.py  # Bottom-up Merge Sort subclass.
├── main.py                  # PyQt6 entry point wiring the visualizers into tabs.
├── requirements.txt         # Python dependencies (PyQt6).
├── setup.sh / setup.bat     # Convenience scripts for creating a virtual environment.
├── logs/                    # Runtime log output (`sorting_viz.log`).
└── README.md                # This documentation.
```


## Installation & Execution

### Prerequisites

- Python 3.10 or newer (the project is tested with CPython 3.10).
- Pip package manager.
- (Optional) virtual environment tooling (`python -m venv` or `virtualenv`).

### Setup Steps

```bash
# Clone or unzip the repository, then inside the folder:
python -m venv .venv
source .venv/bin/activate            # On Windows: .\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# Launch the application
python main.py
```

### Platform Notes

- **macOS:** When exporting CSV, the application opts for the Qt non-native file dialog to avoid NSSavePanel warnings. No special configuration is required.
- **Windows/Linux:** No additional steps beyond installing PyQt6.


## Application Architecture

### Core Widget: `AlgorithmVisualizerBase`

All algorithm visualizers inherit from `AlgorithmVisualizerBase` defined in `base.py`. This QWidget orchestrates:

1. **UI Layout**
   - Input controls (`QLineEdit`, buttons for Randomize/Start/Pause/Reset/Export).
   - Animation controls (FPS slider + numeric spin box, scrub slider, step forward/back buttons).
   - Narration banner (`QLabel`) that shows short English descriptions of the most recent step.
   - Canvas (`VisualizationCanvas`) rendering bars, highlights, and HUD.
   - Step list (`QListWidget`) and log (`QTextEdit`) within a splitter biased towards the canvas.

2. **Animation Timing**
   - A single `QTimer` drives `_tick()`, fetching the next `Step` from the generator.
   - 60 FPS finish sweep reuses the timer to highlight sorted indices.
   - `hideEvent` automatically pauses running animations when the tab becomes invisible.

3. **State Management**
   - Maintains the current array (`_array`), initial snapshot (`_initial_array`), metrics (comparisons, swaps), and highlight sets.
   - Records every `Step` emitted by the generator as well as periodic checkpoints (`checkpoint_stride`) capturing array and metric snapshots.
   - Scrubbing restores the nearest checkpoint then replays steps using `_apply_step` to ensure identical metrics/highlights.

4. **Narration & Logs**
   - `_narrate_step` maps each `Step` to an English sentence. Swap narration uses the tuple payload baked into the step, keeping descriptions correct even when scrubbing.
   - `_set_narration` shows/hides the label depending on text content.
   - `txt_log` records lifecycle events (start/pause/resume/reset/export, finish sweep).

5. **User Interaction**
   - Keyboard shortcuts: `S` (start), `Space` (pause/resume), `R` (randomize), `←/→` (step backward/forward).
   - Scrub slider (`QSlider`) and step list (`QListWidget` double-click) both call `_seek_from_shortcut`, which pauses if necessary and replays the state.
   - FPS slider and spinbox remain synchronized via mirrored signal connections.

6. **Export**
   - `Export CSV` writes each recorded step with columns `(idx, op, i, j, payload)`, providing a reproducible log of algorithm operations.


### Visualization Canvas

`VisualizationCanvas` (in `base.py`) renders the array using PyQt6 painting primitives:

- Bars are positioned based on the current array and scaled to the widget height. Colors correspond to highlights: comparisons (`cmp_color`), swaps (`swap_color`), pivots (`pivot_color`), merge ranges (`merge_color`), final confirmations (`confirm_color`).
- A subtle outline improves contrast on dark themes.
- The HUD uses the system fixed-width font (`QFontDatabase.systemFont`) to avoid platform warnings.


### Step Model

`Step` is a dataclass capturing a single algorithmic action:

```python
@dataclass
class Step:
    op: str
    indices: Tuple[int, ...]
    payload: Optional[Any] = None
```

Supported operations:

- `"compare"` — compares elements at two indices; increments comparison counter.
- `"swap"` — swaps two indices; `payload` is `(value_at_i, value_at_j)` captured before the swap for narration accuracy.
- `"pivot"` — marks the pivot index in Quick Sort.
- `"merge_mark"` — highlights the current merge window in Merge Sort.
- `"merge_compare"` — compares two indices when merging, `payload` stores destination index.
- `"set"` — writes a value to an index (Merge Sort merging, or other algorithms that set values directly).
- `"confirm"` — used by the completion sweep to mark final sorted positions.

Every algorithm exclusively yields these operations, ensuring the base class remains the single source of truth for state mutations and metrics.


## Implemented Algorithms

### Bubble Sort

- **Theory:** Repeatedly scan the array, swapping adjacent inversions. Early exit if no swaps occur in a pass.
- **Complexity:** Worst/average `O(n²)`, best `O(n)` with early exit; swaps `≤ n(n−1)/2`.
- **Implementation (`bubblesort_visualizer.py`):**
  - Iterates `i` from 0 to `n-1`, reducing the comparison window (`n - i - 1`).
  - Yields `Step("compare", (j, j+1))` for each adjacent pair.
  - When an inversion is detected, yields `Step("swap", (j, j+1), payload=(value_j, value_j+1))`. The base class swaps the elements and increments the swap counter.
  - If a pass makes no swaps, the generator terminates early.

### Quick Sort (Iterative, Median-of-Three Lomuto)

- **Theory:** Uses a stack to emulate recursion. Each partition selects a pivot via median-of-three sampling to mitigate worst-case inputs. Lomuto partitioning ensures stability of the partition logic.
- **Complexity:** Average `O(n log n)`, worst `O(n²)` (mitigated by median-of-three). Stack depth `O(log n)` on average.
- **Implementation (`quicksort_visualizer.py`):**
  - Maintains a stack of `(low, high)` subarray bounds.
  - Median-of-three sampling compares `(low, mid)`, `(mid, high)`, `(low, high)` to choose a pivot candidate. If the median is not already at `high`, a swap step is emitted with payload `(value_at_pidx, value_at_high)`.
  - Pivot value is read from `self._array[high]`, recorded via `Step("pivot", (high,))`.
  - Partition loop compares each element to the pivot and swaps when necessary, with swap payloads capturing the pre-swap values.
  - After partitioning, pushes the right and left subranges onto the stack if they contain more than one element.

### Merge Sort (Bottom-Up Iterative)

- **Theory:** Bottom-up merge sort merges runs of size `width = 1, 2, 4, ...` until the entire array is sorted.
- **Complexity:** Deterministic `O(n log n)` comparisons, `O(n log n)` data moves; stable by construction.
- **Implementation (`mergesort_visualizer.py`):**
  - For each window `[lo, hi]`, copies the segment to `aux = self._array[lo:hi+1]` to avoid read/write conflicts.
  - Emits `Step("merge_mark", (lo, hi))` to highlight the merge span.
  - Uses two cursors `i` (left half) and `j` (right half). For each destination index `k`:
    - If one half is exhausted, emits `Step("set", (k,), aux[j])` (or `aux[i]`).
    - Otherwise emits `Step("merge_compare", (lo+i, lo+j), payload=k)` followed by `Step("set", (k,), value)` depending on comparison result.
  - Doubling `width` ensures logarithmic passes.


## User Interaction Guide

- **Randomize / Input:** Enter comma-separated integers or leave blank and press *Randomize* to generate a random array of length `default_n` within `min_val`–`max_val` (default 32 values, 1–200).
- **Start:** Parses any entered array, resets the visual state, and begins emitting steps from the algorithm’s generator.
- **Pause/Resume:** Toggles the QTimer; defensive FPS clamp ensures consistent timing when resuming.
- **Reset:** Restores the original unsorted array (`_initial_array`) and clears step history.
- **FPS Slider + Spinbox:** Adjust animation cadence; values are synchronized.
- **Scrub Slider:** Jump to any recorded step. The system loads the closest checkpoint and replays steps through `_apply_step` to guarantee metric consistency, updates highlights, and sets the narration to describe the currently-viewed operation.
- **Step Buttons / Arrow Keys:** Single-step forward/backward even while paused; keyboard shortcuts map to `_seek_from_shortcut`.
- **Step List:** Displays a contiguous window of steps around the current position. Double-clicking an item triggers `_seek` to the corresponding global step index.
- **Narration Panel:** Collapsed when empty; displays plain-text sentences for the latest step, drawing from `_narrate_step` and the payload data embedded in the `Step` object.
- **Export CSV:** Writes an ordered list of steps to a CSV. Swap steps include the `(val_i, val_j)` payload, enabling accurate offline narration or validation.
- **Finish Sweep:** After the generator exhausts, the application enters a confirmation phase that highlights each index in sequence (60 FPS) and logs completion.


## Extending the Visualizer

Adding a new algorithm involves subclassing `AlgorithmVisualizerBase` and implementing `_generate_steps(self, arr: List[int]) -> Iterator[Step]`:

1. Operate directly on `self._array` rather than copies to keep state consistent with the visualizer.
2. Emit only supported `Step` operations with accurate indices and payloads (e.g., include a tuple payload for swaps if you need correct narration).
3. Ensure any “set” operations are followed by the correct highlight behaviour if you introduce new semantics.
4. Add the subclass to `main.py` to expose it in the tabbed interface.

The base class automatically records steps, builds checkpoints, updates the canvas, and handles narration/logging, so new algorithms benefit from the existing instrumentation without additional UI code.


## Testing & Verification Checklist

- **Syntax Check:** `python -m compileall base.py bubblesort_visualizer.py quicksort_visualizer.py mergesort_visualizer.py main.py`
- **Runtime QA:**
  - Start each algorithm with randomized data; verify narration, highlights, and HUD counters.
  - Pause midway, scrub backward and forward, and resume; narration should remain correct thanks to swap payloads.
  - Double-clicking entries in the step list should jump to the corresponding state.
  - Reset should restore the original array and set the scrub label to `Step: 0/0`.
  - Finish sweep should complete without requiring manual reset and allow immediate restart.
  - CSV export should list every recorded step with payloads where applicable.


## References & Further Reading

- Cormen, T. H., et al. *Introduction to Algorithms* (3rd ed.). MIT Press, 2009. — Detailed analyses of Bubble Sort, Quick Sort, and Merge Sort.
- Sedgewick, R., & Wayne, K. *Algorithms* (4th ed.). Addison-Wesley, 2011. — Practical considerations for implementing iterative sorting algorithms.
- PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/ — Official reference for the widgets and painting APIs used in this project.


## Roadmap & Contributions

This is version 1 of the visualizer. Planned enhancements include:

- Additional algorithms: Selection Sort for didactic comparison and Radix Sort to showcase non-comparison paradigms.
- Parallel execution experiments: SIMD-friendly implementations (e.g., ARM NEON via C++ extensions) while preserving deterministic playback.
- Advanced visual overlays such as stability colouring and tweened animations.

Contributions are welcome. Please open an issue or pull request describing the proposed change, accompanied by reproducible steps and, where applicable, reference material. Commercial licensing or collaboration inquiries can be sent to Justin Guida at justn.guida@snhu.edu.


## License

This project is distributed under the Educator Non-Commercial License (see `LICENSE.txt`). You may use, modify, and share the software for personal learning, classroom instruction, or academic research. Any commercial usage, including integrating the code into paid products or services, requires explicit written permission from the authors.

Maintainer: Justin Guida (justn.guida@snhu.edu)

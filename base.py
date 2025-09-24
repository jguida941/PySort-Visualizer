from __future__ import annotations

import csv
import logging
import os
import time
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QFontDatabase, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSplitter, QListWidget, QListWidgetItem, QSlider, QTextEdit, QMessageBox,
    QSizePolicy, QFileDialog, QSpinBox
)

# ------------------------ Logging ------------------------

def _build_logger() -> logging.Logger:
    logger = logging.getLogger("sorting_viz")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    os.makedirs("logs", exist_ok=True)
    fh = RotatingFileHandler("logs/sorting_viz.log", maxBytes=1_000_000, backupCount=5)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger

LOGGER = _build_logger()

# ------------------------ Config ------------------------

@dataclass
class VizConfig:
    min_n: int = 5
    max_n: int = 200
    default_n: int = 32
    min_val: int = 1
    max_val: int = 200
    fps_min: int = 1
    fps_max: int = 60
    fps_default: int = 24
    bar_gap_px: int = 2
    padding_px: int = 10
    bg_color: str = "#0f1115"
    bar_color: str = "#6aa0ff"
    cmp_color: str = "#ffe08a"
    swap_color: str = "#fa8072"
    pivot_color: str = "#90ee90"
    merge_color: str = "#a390ee"
    confirm_color: str = "#62d26f"
    hud_color: str = "#e6e6e6"
    checkpoint_stride: int = 200  # snapshot frequency for scrub/reconstruct

# ------------------------ Step model ------------------------

@dataclass
class Step:
    """
    op:
      - "compare"       indices=(i, j)
      - "swap"          indices=(i, j), payload=(value_i, value_j)
      - "pivot"         indices=(p,)
      - "merge_mark"    indices=(lo, hi)
      - "merge_compare" indices=(i, j), payload=k (destination index)
      - "set"           indices=(k,), payload=value
      - "confirm"       indices=(i,) - final green sweep (used by finish sweep)
    """
    op: str
    indices: Tuple[int, ...]
    payload: Optional[Any] = None

# ------------------------ Canvas ------------------------

class VisualizationCanvas(QWidget):
    def __init__(self, get_state: Callable[[], Dict[str, Any]], cfg: VizConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._get_state = get_state
        self._cfg = cfg
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def minimumSizeHint(self) -> QSize:
        return QSize(360, 220)

    def paintEvent(self, _evt) -> None:
        state = self._get_state()
        arr: List[int] = state["array"]
        highlights: Dict[str, Tuple[int, ...]] = state["highlights"]
        confirms: Tuple[int, ...] = state.get("confirm", tuple())
        metrics: Dict[str, Any] = state["metrics"]

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self._cfg.bg_color))

        bar_outline = QColor("#0d0f14")

        if arr:
            w = self.width()
            h = self.height()
            n = len(arr)
            gap = self._cfg.bar_gap_px
            bar_w = max(1, (w - 2 * self._cfg.padding_px - (n - 1) * gap) // max(1, n))
            x = self._cfg.padding_px

            max_val = max(arr)
            scale = (h - 2 * self._cfg.padding_px) / max(1, max_val)

            base = QBrush(QColor(self._cfg.bar_color))
            cmpb = QBrush(QColor(self._cfg.cmp_color))
            swpb = QBrush(QColor(self._cfg.swap_color))
            pivb = QBrush(QColor(self._cfg.pivot_color))
            mrgb = QBrush(QColor(self._cfg.merge_color))
            confb = QBrush(QColor(self._cfg.confirm_color))

            cmp_idx = set(highlights.get("compare", ()))
            swap_idx = set(highlights.get("swap", ()))
            pivot_idx = set(highlights.get("pivot", ()))
            merge_idx = set(highlights.get("merge", ()))
            confirm_idx = set(confirms)

            for i, v in enumerate(arr):
                bar_h = max(1, int(v * scale))
                y = h - self._cfg.padding_px - bar_h

                if i in confirm_idx:
                    brush = confb
                elif i in swap_idx:
                    brush = swpb
                elif i in cmp_idx:
                    brush = cmpb
                elif i in pivot_idx:
                    brush = pivb
                elif i in merge_idx:
                    brush = mrgb
                else:
                    brush = base

                painter.fillRect(x, y, bar_w, bar_h, brush)
                painter.setPen(bar_outline)
                painter.drawRect(x, y, bar_w, bar_h)
                x += bar_w + gap

        # HUD
        painter.setPen(QColor(self._cfg.hud_color))
        hud_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        if hud_font.pointSize() > 0:
            hud_font.setPointSize(max(8, hud_font.pointSize()))
        painter.setFont(hud_font)
        hud_lines = [
            f"Algo: {metrics.get('algo','')}",
            f"n={len(arr) if arr else 0} | FPS={metrics.get('fps', 0)}",
            f"Compare={metrics.get('comparisons', 0)} | Swaps={metrics.get('swaps', 0)}",
            f"Steps={metrics.get('step_idx', 0)}/{metrics.get('total_steps','?')} | Time={metrics.get('elapsed_s', 0.0):.2f}s"
        ]
        x0 = self._cfg.padding_px
        y0 = self._cfg.padding_px + 14
        for line in hud_lines:
            painter.drawText(x0, y0, line)
            y0 += 16

        painter.end()

# ------------------------ Base Visualizer ------------------------

class AlgorithmVisualizerBase(QWidget):
    """
    - Non-blocking animation using QTimer
    - Highlight persistence between ticks
    - Scrub mode via stored steps and periodic checkpoints
    - CSV export of step trace
    - Robust UI state machine
    """
    title: str = "Algorithm"
    STEP_LIST_SAMPLE_RATE: int = 5
    STEP_LIST_MAX_ITEMS: int = 10_000

    def __init__(self, cfg: Optional[VizConfig] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.cfg = cfg or VizConfig()

        # model
        self._array: List[int] = []
        self._initial_array: List[int] = []
        self._step_source: Optional[Iterator[Step]] = None
        self._steps: List[Step] = []
        # checkpoint now stores: (step_idx, snapshot_array, comparisons, swaps)
        self._checkpoints: List[Tuple[int, List[int], int, int]] = []
        self._confirm_progress: int = -1

        # viz state
        self._highlights: Dict[str, Tuple[int, ...]] = {"compare": (), "swap": (), "pivot": (), "merge": ()}
        self._confirm_indices: Tuple[int, ...] = tuple()

        # metrics
        self._comparisons = 0
        self._swaps = 0
        self._step_idx = 0
        self._t0 = 0.0
        self._narration_default = ""
        self._shortcuts: List[QShortcut] = []

        # UI
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._build_ui()
        self._rebind()
        self._install_shortcuts()
        self._set_narration()
        self._update_ui_state("idle")

    # ---------- abstract

    def _generate_steps(self, arr: List[int]) -> Iterator[Step]:
        raise NotImplementedError

    # ---------- UI construction

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Input (comma ints) or leave blank to randomize:"))
        self.le_input = QLineEdit()
        self.le_input.setPlaceholderText("e.g. 5,2,9,1,5,6")
        self.btn_random = QPushButton("Randomize")
        self.btn_start = QPushButton("Start")
        self.btn_pause = QPushButton("Pause/Resume")
        self.btn_reset = QPushButton("Reset")
        self.btn_export = QPushButton("Export CSV")

        row.addWidget(self.le_input)
        row.addWidget(self.btn_random)
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_pause)
        row.addWidget(self.btn_reset)
        row.addWidget(self.btn_export)

        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("FPS:"))
        self.sld_fps = QSlider(Qt.Orientation.Horizontal)
        self.sld_fps.setRange(self.cfg.fps_min, self.cfg.fps_max)
        self.sld_fps.setValue(self.cfg.fps_default)
        speed_row.addWidget(self.sld_fps, 1)
        self.spn_fps = QSpinBox()
        self.spn_fps.setRange(self.cfg.fps_min, self.cfg.fps_max)
        self.spn_fps.setValue(self.cfg.fps_default)
        self.spn_fps.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spn_fps.setFixedWidth(64)
        speed_row.addWidget(self.spn_fps)

        scrub_row = QHBoxLayout()
        self.lbl_scrub = QLabel("Step: 0/0")
        self.sld_scrub = QSlider(Qt.Orientation.Horizontal)
        self.sld_scrub.setRange(0, 0)
        self.btn_step_fwd = QPushButton("Step ▶")
        self.btn_step_back = QPushButton("Step ◀")
        scrub_row.addWidget(self.lbl_scrub)
        scrub_row.addWidget(self.sld_scrub)
        scrub_row.addWidget(self.btn_step_back)
        scrub_row.addWidget(self.btn_step_fwd)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.canvas = VisualizationCanvas(self._get_canvas_state, self.cfg)
        splitter.addWidget(self.canvas)

        self.lbl_narration = QLabel()
        self.lbl_narration.setObjectName("narrationLabel")
        self.lbl_narration.setWordWrap(True)
        self.lbl_narration.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_narration.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lbl_narration.setVisible(False)
        self.lbl_narration.setMaximumHeight(self.fontMetrics().height() * 2 + 12)

        right = QVBoxLayout()
        right_w = QWidget()
        right_w.setLayout(right)
        right.addWidget(QLabel("Steps"))
        self.lst_steps = QListWidget()
        right.addWidget(self.lst_steps, 1)
        right.addWidget(QLabel("Log"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        right.addWidget(self.txt_log, 1)
        splitter.addWidget(right_w)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([1_000_000, 250_000])

        mono_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        if mono_font.pointSize() > 0:
            mono_font.setPointSize(max(9, mono_font.pointSize() - 1))
        self.lst_steps.setFont(mono_font)
        self.txt_log.setFont(mono_font)
        self.lst_steps.setStyleSheet("font-size: 11px;")
        self.lst_steps.itemActivated.connect(self._on_step_item_activated)

        root.addLayout(row)
        root.addLayout(speed_row)
        root.addLayout(scrub_row)
        root.addWidget(self.lbl_narration)
        root.addWidget(splitter)

        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)
        self.setStyleSheet(
            """
            QWidget { color: #e6e6e6; background-color: #0f1115; }
            QListWidget, QTextEdit { background: #12151b; border: 1px solid #2a2f3a; }
            QLineEdit { background: #12151b; border: 1px solid #2a2f3a; padding: 4px; }
            QPushButton { background: #1a1f27; border: 1px solid #2a2f3a; padding: 6px 10px; }
            QPushButton:hover { background: #202634; }
            QLabel#narrationLabel { background: #10131a; border: 1px solid #232838; border-radius: 6px; padding: 6px 8px; color: #cdd2e1; }
            """
        )

    def _rebind(self) -> None:
        self.btn_random.clicked.connect(self._on_randomize)
        self.btn_start.clicked.connect(self._on_start)
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_reset.clicked.connect(self._on_reset)
        self.sld_fps.valueChanged.connect(self._on_fps_changed)
        self.sld_fps.valueChanged.connect(self.spn_fps.setValue)
        self.spn_fps.valueChanged.connect(self.sld_fps.setValue)
        self.btn_export.clicked.connect(self._on_export)
        self.sld_scrub.valueChanged.connect(self._on_scrub_move)
        self.btn_step_fwd.clicked.connect(lambda: self._seek(self._step_idx + 1))
        self.btn_step_back.clicked.connect(lambda: self._seek(self._step_idx - 1))

    def _install_shortcuts(self) -> None:
        shortcuts = [
            ("S", self._on_start),
            ("Space", self._on_pause),
            ("R", self._on_randomize),
            ("Left", lambda: self._seek_from_shortcut(self._step_idx - 1)),
            ("Right", lambda: self._seek_from_shortcut(self._step_idx + 1)),
        ]
        for seq, handler in shortcuts:
            shortcut = QShortcut(QKeySequence(seq), self)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

    def _set_narration(self, text: Optional[str] = None) -> None:
        if getattr(self, "lbl_narration", None) is None:
            return
        message = text.strip() if isinstance(text, str) else ""
        if not message and self._narration_default:
            message = self._narration_default
        self.lbl_narration.setVisible(bool(message))
        self.lbl_narration.setText(message)

    # ---------- UI state machine

    def _update_ui_state(self, state: str) -> None:
        running = state == "running"
        paused = state == "paused"
        finished = state == "finished"
        idle = state == "idle"

        can_start_new = not running

        self.le_input.setEnabled(can_start_new)
        self.btn_random.setEnabled(can_start_new)
        self.btn_start.setEnabled(can_start_new)

        self.btn_pause.setEnabled(running or paused)

        self.btn_reset.setEnabled(can_start_new and bool(self._initial_array))

        has_steps = bool(self._steps)
        self.btn_export.setEnabled(can_start_new and has_steps)

        allow_scrub = can_start_new and has_steps
        self.sld_scrub.setEnabled(allow_scrub)
        self.btn_step_fwd.setEnabled(allow_scrub)
        self.btn_step_back.setEnabled(allow_scrub)

    # ---------- state and metrics

    def _get_canvas_state(self) -> Dict[str, Any]:
        elapsed = time.time() - self._t0 if self._t0 else 0.0
        return {
            "array": self._array,
            "highlights": self._highlights,
            "confirm": self._confirm_indices,
            "metrics": {
                "algo": self.title,
                "comparisons": self._comparisons,
                "swaps": self._swaps,
                "fps": self.sld_fps.value(),
                "step_idx": self._step_idx,
                "total_steps": len(self._steps) if self._steps else 0,
                "elapsed_s": elapsed
            }
        }

    def _set_array(self, arr: List[int]) -> None:
        if not arr:
            raise ValueError("Array cannot be empty")
        self._array = list(arr)
        self._initial_array = list(arr)
        self._highlights = {"compare": (), "swap": (), "pivot": (), "merge": ()}
        self._confirm_indices = tuple()
        self._comparisons = 0
        self._swaps = 0
        self._steps.clear()
        self._checkpoints.clear()
        self._step_idx = 0
        self.lst_steps.clear()
        self._append_checkpoint(0)  # checkpoint at step 0
        self.canvas.update()
        self._update_ui_state("idle")
        self._set_narration()
        self._update_scrub_ui()

    def _append_checkpoint(self, step_idx: int) -> None:
        # store array snapshot and metrics
        self._checkpoints.append((step_idx, list(self._array), self._comparisons, self._swaps))

    # ---------- controls

    def _on_randomize(self) -> None:
        try:
            import random
            n = self.cfg.default_n
            arr = [random.randint(self.cfg.min_val, self.cfg.max_val) for _ in range(n)]
            self._set_array(arr)
            self.txt_log.append(f"Randomized array n={n}")
            LOGGER.info("Randomized n=%d", n)
        except Exception as e:
            self._error(str(e))

    def _parse_input(self) -> List[int]:
        text = self.le_input.text().strip()
        if not text:
            return []
        parts = [p for p in text.replace(" ", "").split(",") if p]
        arr = [int(p) for p in parts]
        if len(arr) > self.cfg.max_n:
            raise ValueError(f"Max length {self.cfg.max_n}, got {len(arr)}")
        return arr

    def _on_start(self) -> None:
        try:
            # Always parse (new) input on start.
            parsed = self._parse_input()

            if parsed:
                # User provided a fresh array; set it and run.
                self._set_array(parsed)
            else:
                # No new input text.
                if self._initial_array:
                    # Re-run from the original unsorted snapshot captured at last _set_array().
                    self._set_array(self._initial_array)
                else:
                    # Nothing loaded yet → randomize a fresh one.
                    self._on_randomize()
                    if not self._array:
                        return

            # Construct generator and start animation
            self._step_source = self._generate_steps(self._array)
            self._t0 = time.time()
            fps = max(self.cfg.fps_min, min(self.cfg.fps_max, self.sld_fps.value()))
            self._timer.start(int(1000 / fps))
            self.txt_log.append(f"Started at {fps} FPS")
            LOGGER.info("Start algo=%s fps=%d n=%d", self.title, fps, len(self._array))
            self._update_ui_state("running")
        except Exception as e:
            self._error(str(e))

    def _on_pause(self) -> None:
        if self._timer.isActive():
            self._timer.stop()
            self.txt_log.append("Paused")
            self._update_ui_state("paused")
        else:
            fps = max(self.cfg.fps_min, min(self.cfg.fps_max, self.sld_fps.value()))
            self._timer.start(int(1000 / fps))
            self.txt_log.append("Resumed")
            self._update_ui_state("running")

    def _on_reset(self) -> None:
        self._timer.stop()
        self._step_source = None
        self._confirm_progress = -1
        if self._initial_array:
            self._set_array(self._initial_array)
        self.txt_log.append("Reset")
        self._update_ui_state("idle")

    def _on_fps_changed(self, v: int) -> None:
        if self._timer.isActive():
            self._timer.start(int(1000 / max(1, v)))

    def _on_export(self) -> None:
        if not self._steps:
            self._warn("No steps to export yet.")
            return
        options = QFileDialog.Option.DontUseNativeDialog
        path, _selected_filter = QFileDialog.getSaveFileName(
            self, "Export Steps CSV", "steps.csv", "CSV (*.csv)", options=options
        )
        if not path:
            return
        try:
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["idx", "op", "i", "j", "payload"])
                for idx, st in enumerate(self._steps):
                    i = st.indices[0] if st.indices else ""
                    j = st.indices[1] if len(st.indices) > 1 else ""
                    w.writerow([idx, st.op, i, j, st.payload if st.payload is not None else ""])
            self.txt_log.append(f"Exported {len(self._steps)} steps to {path}")
        except Exception as e:
            self._error(str(e))

    # ---------- animation tick

    def _tick(self) -> None:
        if self._step_source is None:
            self._timer.stop()
            return
        try:
            step = next(self._step_source)
            narration = self._narrate_step(step)
            self._apply_step(step)  # increments metrics
            self._steps.append(step)
            if len(self._steps) % self.cfg.checkpoint_stride == 0:
                self._append_checkpoint(len(self._steps))
            self._append_step_list(step)
            self._step_idx = len(self._steps)
            self._update_scrub_ui()
            self.canvas.update()
            self._set_narration(narration)
        except StopIteration:
            self._timer.stop()
            self._start_finish_animation()
        except Exception as e:
            self._timer.stop()
            self._error(str(e))

    def _start_finish_animation(self) -> None:
        self.txt_log.append(f"Finished. Comparisons={self._comparisons}, Swaps={self._swaps}")
        LOGGER.info("Finished algo=%s comps=%d swaps=%d", self.title, self._comparisons, self._swaps)
        self._confirm_progress = 0
        self._confirm_indices = tuple()
        self._set_narration("Sort complete. Finalizing display…")

        # Rebind timer to finish sweep at high FPS
        try:
            self._timer.timeout.disconnect(self._tick)
        except TypeError:
            pass
        try:
            self._timer.timeout.disconnect(self._finish_tick)
        except TypeError:
            pass
        self._timer.timeout.connect(self._finish_tick)
        self._timer.start(int(1000 / 60))
        self._update_ui_state("finished")

    def _finish_tick(self) -> None:
        if self._confirm_progress < len(self._array):
            idx = self._confirm_progress
            self._confirm_indices = tuple(list(self._confirm_indices) + [idx])
            self._confirm_progress += 1
            self.canvas.update()
        else:
            self._timer.stop()
            # Restore normal binding
            try:
                self._timer.timeout.disconnect(self._finish_tick)
            except TypeError:
                pass
            try:
                self._timer.timeout.disconnect(self._tick)
            except TypeError:
                pass
            self._timer.timeout.connect(self._tick)
            self._set_narration("Array sorted!")

    # ---------- step application and highlights

    def _narrate_step(self, step: Step) -> str:
        arr = self._array
        op = step.op
        idx = step.indices
        payload = step.payload

        def safe_get(i: int) -> Optional[int]:
            return arr[i] if 0 <= i < len(arr) else None

        try:
            if op == "compare":
                i, j = idx
                return (
                    f"Comparing {safe_get(i)} (index {i}) with "
                    f"{safe_get(j)} (index {j})."
                )
            if op == "merge_compare":
                i, j = idx
                dest = payload if isinstance(payload, int) else "?"
                return (
                    f"Comparing {safe_get(i)} (index {i}) with {safe_get(j)} (index {j}) "
                    f"for position {dest}."
                )
            if op == "swap":
                i, j = idx
                if payload and isinstance(payload, tuple) and len(payload) == 2:
                    val1, val2 = payload
                    return f"Swapping {val1} (index {i}) with {val2} (index {j})."
                return f"Swapping elements at indices {i} and {j}."
            if op == "set":
                k = idx[0]
                old_val = safe_get(k)
                return f"Setting index {k} from {old_val} to {payload}."
            if op == "pivot":
                p = idx[0]
                return f"Selecting {safe_get(p)} at index {p} as the pivot."
            if op == "merge_mark":
                lo, hi = idx
                return f"Marking merge range {lo} – {hi}."
            if op == "confirm" and idx:
                i = idx[0]
                return f"Confirming index {i} as sorted."
        except (IndexError, ValueError, TypeError):
            return ""

        return ""

    def _append_step_list(self, step: Step) -> None:
        current_idx = len(self._steps)
        important_ops = {"swap", "set", "pivot", "merge_mark"}
        if current_idx > 1 and (current_idx % self.STEP_LIST_SAMPLE_RATE != 0) and (step.op not in important_ops):
            return

        text = f"{step.op}: {step.indices}" + (f" -> {step.payload}" if step.payload is not None else "")
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, current_idx)
        self.lst_steps.addItem(item)
        if self.lst_steps.count() > self.STEP_LIST_MAX_ITEMS:
            self.lst_steps.takeItem(0)
        self.lst_steps.scrollToBottom()

    def _apply_step(self, step: Step) -> None:
        op = step.op
        idx = step.indices
        # leave last highlight visible until we set a new one here
        if op == "compare":
            self._comparisons += 1
            self._highlights["compare"] = idx
        elif op == "swap":
            self._swaps += 1
            i, j = idx
            self._array[i], self._array[j] = self._array[j], self._array[i]
            self._highlights["swap"] = idx
        elif op == "pivot":
            self._highlights["pivot"] = idx
        elif op == "merge_mark":
            lo, hi = idx
            self._highlights["merge"] = tuple(range(lo, hi + 1))
        elif op == "merge_compare":
            self._comparisons += 1
            self._highlights["compare"] = idx
            self._highlights["merge"] = (step.payload,) if isinstance(step.payload, int) else ()
        elif op == "set":
            k = idx[0]
            self._array[k] = int(step.payload)
            self._highlights["merge"] = (k,)
        elif op == "confirm":
            pass
        else:
            raise ValueError(f"Unknown step op: {op}")

    # ---------- scrub mode

    def _update_scrub_ui(self) -> None:
        total = len(self._steps)
        self.sld_scrub.blockSignals(True)
        self.sld_scrub.setRange(0, total)
        self.sld_scrub.setValue(self._step_idx)
        self.sld_scrub.blockSignals(False)
        self.lbl_scrub.setText(f"Step: {self._step_idx}/{total}")

    def _on_scrub_move(self, val: int) -> None:
        if self._timer.isActive():
            self._timer.stop()
            self._update_ui_state("paused")
        self._seek(val)

    def _seek_from_shortcut(self, target_idx: int) -> None:
        if self._timer.isActive():
            self._timer.stop()
            self._update_ui_state("paused")
        self._seek(target_idx)

    def _seek(self, target_idx: int) -> None:
        target_idx = max(0, min(len(self._steps), target_idx))

        # find nearest checkpoint <= target_idx and restore array + metrics
        ck_idx, ck_arr, ck_comps, ck_swaps = 0, list(self._initial_array), 0, 0
        for s_idx, snap, comps, swaps in self._checkpoints:
            if s_idx <= target_idx:
                ck_idx, ck_arr, ck_comps, ck_swaps = s_idx, list(snap), comps, swaps
            else:
                break

        self._array = ck_arr
        self._comparisons = ck_comps
        self._swaps = ck_swaps
        self._confirm_indices = tuple()
        self._confirm_progress = -1
        self._highlights = {"compare": (), "swap": (), "pivot": (), "merge": ()}

        narration = ""
        for i in range(ck_idx, target_idx):
            step = self._steps[i]
            narration = self._narrate_step(step)
            self._apply_step(step)

        self._step_idx = target_idx
        self._rebuild_step_list_after_seek(target_idx)
        self._update_scrub_ui()
        self.canvas.update()

        if target_idx == 0:
            self._set_narration()
        else:
            if not narration and target_idx <= len(self._steps):
                last_step = self._steps[target_idx - 1]
                narration = f"Viewing {last_step.op} at {last_step.indices}."
            self._set_narration(narration)

    def _on_step_item_activated(self, item: QListWidgetItem) -> None:
        if item is None:
            return
        step_idx = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(step_idx, int):
            self._seek_from_shortcut(step_idx)

    def _rebuild_step_list_after_seek(self, target_idx: int) -> None:
        """Show a contiguous window of steps around the scrub target for context."""
        if not self._steps:
            self.lst_steps.clear()
            return

        total_steps = len(self._steps)
        window = min(self.STEP_LIST_MAX_ITEMS, total_steps)
        if window <= 0:
            self.lst_steps.clear()
            return

        half_window = window // 2
        start = max(0, target_idx - half_window)
        end = min(total_steps, start + window)
        if end - start < window:
            start = max(0, end - window)

        self.lst_steps.clear()
        selected_row: Optional[int] = None

        for i in range(start, end):
            step = self._steps[i]
            text = f"{step.op}: {step.indices}"
            if step.payload is not None:
                text += f" -> {step.payload}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, i + 1)
            self.lst_steps.addItem(item)

            if i == target_idx - 1:
                selected_row = self.lst_steps.count() - 1

        if selected_row is not None and 0 <= selected_row < self.lst_steps.count():
            item = self.lst_steps.item(selected_row)
            self.lst_steps.setCurrentItem(item)
            self.lst_steps.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)
        elif self.lst_steps.count():
            if target_idx <= 0:
                self.lst_steps.scrollToTop()
            else:
                self.lst_steps.scrollToBottom()

    # ---------- utils

    def pause_if_running(self) -> None:
        if self._timer.isActive():
            self._timer.stop()
            self.txt_log.append("Paused (auto)")
            self._update_ui_state("paused")

    def hideEvent(self, event) -> None:  # type: ignore[override]
        self.pause_if_running()
        super().hideEvent(event)

    def _warn(self, msg: str) -> None:
        self.txt_log.append(f"[WARN] {msg}")

    def _error(self, msg: str) -> None:
        self.txt_log.append(f"[ERROR] {msg}")
        LOGGER.exception(msg)
        QMessageBox.critical(self, self.title, msg)

from __future__ import annotations

import csv
import logging
import os
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import suppress
from dataclasses import dataclass, fields
from logging.handlers import RotatingFileHandler
from typing import Any, get_type_hints

from PyQt6.QtCore import QRect, QSettings, QSize, Qt, QTimer
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFontDatabase,
    QHideEvent,
    QKeySequence,
    QPainter,
    QPaintEvent,
    QPen,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.algos.registry import AlgoInfo
from app.core.step import Step

AlgorithmFunc = Callable[[list[int]], Iterator[Step]]


def _install_crash_hook() -> None:
    def _hook(exc_type: type[BaseException], exc: BaseException, tb: Any) -> None:
        logging.getLogger("sorting_viz").exception(
            "Uncaught exception", exc_info=(exc_type, exc, tb)
        )
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox

            if QApplication.instance() is not None:
                QMessageBox.critical(
                    None,
                    "Unexpected error",
                    "The app hit an unexpected error.\n\nCheck the log file for details.",
                )
        except Exception:
            print("Unexpected error; check logs for details.", file=sys.stderr)

    sys.excepthook = _hook


# ------------------------ Logging ------------------------


def _build_logger() -> logging.Logger:
    from pathlib import Path

    user_log_dir_func: Callable[..., str] | None
    try:
        from platformdirs import user_log_dir as _user_log_dir

        user_log_dir_func = _user_log_dir
    except ImportError:  # pragma: no cover - platformdirs is optional for runtime
        user_log_dir_func = None

    logger = logging.getLogger("sorting_viz")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    if user_log_dir_func is not None:
        log_dir = Path(user_log_dir_func("sorting-visualizer", "org.pysort"))
    else:
        log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(log_dir / "sorting_viz.log", maxBytes=1_000_000, backupCount=5)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


LOGGER = _build_logger()


_install_crash_hook()

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
    key_color: str = "#3cd7d7"
    shift_color: str = "#ff9f43"
    confirm_color: str = "#62d26f"
    hud_color: str = "#e6e6e6"
    checkpoint_stride: int = 200  # snapshot frequency for scrub/reconstruct

    @staticmethod
    def _coerce(expected_type: type[Any] | str, raw: Any) -> Any:
        name = (
            expected_type
            if isinstance(expected_type, str)
            else getattr(expected_type, "__name__", "")
        )
        if expected_type is int or name == "int":
            return int(raw)
        if expected_type is float or name == "float":
            return float(raw)
        if expected_type is bool or name == "bool":
            if isinstance(raw, str):
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            return bool(raw)
        if expected_type is str or name == "str":
            return str(raw)
        return raw

    @classmethod
    def from_settings(cls, settings: QSettings | None = None) -> VizConfig:
        settings = settings or QSettings()
        overrides: dict[str, Any] = {}
        hints = get_type_hints(cls)
        for field in fields(cls):
            settings_key = f"config/{field.name}"
            if settings.contains(settings_key):
                raw = settings.value(settings_key)
            else:
                env_key = f"SORT_VIZ_{field.name.upper()}"
                raw = os.environ.get(env_key)
            if raw not in (None, ""):
                expected = hints.get(field.name, field.type)
                overrides[field.name] = cls._coerce(expected, raw)
        return cls(**overrides)


# ------------------------ Canvas ------------------------


class VisualizationCanvas(QWidget):
    def __init__(
        self, get_state: Callable[[], dict[str, Any]], cfg: VizConfig, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._get_state = get_state
        self._cfg = cfg
        self._show_labels = False
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def minimumSizeHint(self) -> QSize:
        return QSize(360, 220)

    def set_show_labels(self, show: bool) -> None:
        self._show_labels = show
        self.update()

    def paintEvent(self, _event: QPaintEvent | None) -> None:
        state = self._get_state()
        arr: list[int] = state["array"]
        highlights: dict[str, tuple[int, ...]] = state["highlights"]
        confirms: tuple[int, ...] = state.get("confirm", tuple())
        metrics: dict[str, Any] = state["metrics"]

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self._cfg.bg_color))

        pen = QPen(QColor("#0d0f14"))
        pen.setCosmetic(True)
        painter.setPen(pen)

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
            keyb = QBrush(QColor(self._cfg.key_color))
            shiftb = QBrush(QColor(self._cfg.shift_color))
            confb = QBrush(QColor(self._cfg.confirm_color))

            cmp_idx = set(highlights.get("compare", ()))
            swap_idx = set(highlights.get("swap", ()))
            pivot_idx = set(highlights.get("pivot", ()))
            merge_idx = set(highlights.get("merge", ()))
            key_idx = set(highlights.get("key", ()))
            shift_idx = set(highlights.get("shift", ()))
            confirm_idx = set(confirms)

            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            for i, v in enumerate(arr):
                bar_h = max(1, int(v * scale))
                y = h - self._cfg.padding_px - bar_h

                if i in confirm_idx:
                    brush = confb
                elif i in key_idx:
                    brush = keyb
                elif i in shift_idx:
                    brush = shiftb
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

                painter.drawRect(x, y, bar_w, bar_h)
                x += bar_w + gap

            labels_auto = (
                metrics.get("total_steps", 0) > 0
                and metrics.get("step_idx", 0) >= metrics.get("total_steps", 0)
                and n <= 40
            )
            if self._show_labels or labels_auto:
                painter.setPen(QColor(self._cfg.hud_color))
                font = painter.font()
                x = self._cfg.padding_px
                for v in arr:
                    bar_h = max(1, int(v * scale))
                    y = h - self._cfg.padding_px - bar_h
                    text = str(v)

                    if bar_w < 8:
                        x += bar_w + gap
                        continue

                    if bar_w < 14:
                        font.setPointSize(8)
                    elif bar_w < 20:
                        font.setPointSize(9)
                    else:
                        font.setPointSize(10)
                    painter.setFont(font)
                    fm = painter.fontMetrics()
                    tw = fm.horizontalAdvance(text)
                    th = fm.ascent()

                    tx = x + max(0, (bar_w - tw) // 2)
                    ty_above = y - 2
                    ty_inside = y + th + 2
                    if ty_above - th >= 0:
                        painter.drawText(tx, ty_above, text)
                    elif bar_h > th + 4:
                        painter.drawText(tx, ty_inside, text)

                    x += bar_w + gap

        # --- Upgraded HUD (rounded, translucent panel) ---
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QColor(self._cfg.hud_color))
        painter.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))

        hud_lines = [
            f"Algo: {metrics.get('algo','')}",
            f"n={len(arr) if arr else 0} | FPS={metrics.get('fps', 0)}",
            f"Compare={metrics.get('comparisons', 0)} | Swaps={metrics.get('swaps', 0)}",
            f"Steps={metrics.get('step_idx', 0)}/{metrics.get('total_steps','?')} | Time={metrics.get('elapsed_s', 0.0):.2f}s",
        ]

        fm = painter.fontMetrics()
        line_h = fm.lineSpacing()
        pad = 6
        x_text = self._cfg.padding_px
        y_text = self._cfg.padding_px

        w_text = max(fm.horizontalAdvance(s) for s in hud_lines) if hud_lines else 0
        h_text = line_h * len(hud_lines)

        bg_rect = QRect(x_text - pad, y_text - pad, w_text + pad * 2, h_text + pad * 2)

        # Panel
        painter.setBrush(QColor(0, 0, 0, 120))  # translucent black
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bg_rect, 6, 6)

        # Text
        painter.setPen(QColor(self._cfg.hud_color))
        for i, line in enumerate(hud_lines):
            # drawText baseline is at y + ascent
            painter.drawText(x_text, y_text + fm.ascent() + i * line_h, line)

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

    def __init__(
        self,
        algo_info: AlgoInfo,
        algo_func: AlgorithmFunc,
        cfg: VizConfig | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = QSettings()
        self.cfg = cfg or VizConfig.from_settings(self._settings)
        self.algo_info = algo_info
        self.algo_func: AlgorithmFunc = algo_func
        self.title = algo_info.name

        # Ensure this widget really paints a dark background (not the parent’s light gray)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(self.cfg.bg_color))
        self.setPalette(pal)

        # model
        self._array: list[int] = []
        self._initial_array: list[int] = []
        self._step_source: Iterator[Step] | None = None
        self._steps: list[Step] = []
        # checkpoint now stores: (step_idx, snapshot_array, comparisons, swaps)
        self._checkpoints: list[tuple[int, list[int], int, int]] = []
        self._confirm_progress: int = -1

        # viz state
        self._highlights: dict[str, tuple[int, ...]] = {
            "compare": (),
            "swap": (),
            "pivot": (),
            "merge": (),
            "key": (),
            "shift": (),
        }
        self._confirm_indices: tuple[int, ...] = tuple()

        # metrics
        self._comparisons = 0
        self._swaps = 0
        self._step_idx = 0
        self._t0 = 0.0
        self._narration_default = ""
        self._shortcuts: list[QShortcut] = []

        # UI
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._build_ui()
        self._rebind()
        self._install_shortcuts()
        self._restore_preferences()
        self._set_narration()
        self._update_ui_state("idle")

    # ---------- abstract

    def _generate_steps(self, arr: list[int]) -> Iterator[Step]:
        return self.algo_func(arr)

    # ---------- UI construction

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        row = QHBoxLayout()
        lbl_input = QLabel("Input (comma ints) or leave blank to randomize:")
        lbl_input.setObjectName("caption")
        row.addWidget(lbl_input)
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
        row.setSpacing(8)
        row.setContentsMargins(8, 6, 8, 0)

        speed_row = QHBoxLayout()
        fps_label = QLabel("FPS:")
        fps_label.setObjectName("caption")
        speed_row.addWidget(fps_label)
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
        speed_row.setSpacing(8)
        speed_row.setContentsMargins(8, 0, 8, 0)

        scrub_row = QHBoxLayout()
        self.lbl_scrub = QLabel("Step: 0/0")
        self.lbl_scrub.setObjectName("caption")
        self.sld_scrub = QSlider(Qt.Orientation.Horizontal)
        self.sld_scrub.setRange(0, 0)
        self.btn_step_fwd = QPushButton("Step ▶")
        self.btn_step_back = QPushButton("Step ◀")
        self.chk_labels = QCheckBox("Show values")

        icon_size = QSize(16, 16)
        for btn in (
            self.btn_random,
            self.btn_start,
            self.btn_pause,
            self.btn_reset,
            self.btn_export,
            self.btn_step_back,
            self.btn_step_fwd,
        ):
            btn.setIconSize(icon_size)

        style = self.style()
        if style is not None:
            self.btn_random.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
            self.btn_start.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.btn_pause.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.btn_reset.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
            self.btn_export.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
            self.btn_step_back.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
            self.btn_step_fwd.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        scrub_row.addWidget(self.lbl_scrub)
        scrub_row.addWidget(self.sld_scrub)
        scrub_row.addWidget(self.btn_step_back)
        scrub_row.addWidget(self.btn_step_fwd)
        scrub_row.addWidget(self.chk_labels)
        scrub_row.setSpacing(8)
        scrub_row.setContentsMargins(8, 0, 8, 6)

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
        right_w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        right_w.setAutoFillBackground(True)
        rp = right_w.palette()
        rp.setColor(right_w.backgroundRole(), QColor(self.cfg.bg_color))
        right_w.setPalette(rp)
        right_w.setLayout(right)
        right.addWidget(QLabel("Steps"))
        self.lst_steps = QListWidget()
        right.addWidget(self.lst_steps, 1)
        right.addWidget(QLabel("Log"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        right.addWidget(self.txt_log, 1)
        legend = QLabel(
            "<b>Legend</b><br/>"
            f"<span style='color:{self.cfg.key_color};'>■</span> Key  "
            f"<span style='color:{self.cfg.shift_color};'>■</span> Shift  "
            f"<span style='color:{self.cfg.cmp_color};'>■</span> Compare  "
            f"<span style='color:{self.cfg.swap_color};'>■</span> Swap  "
            f"<span style='color:{self.cfg.pivot_color};'>■</span> Pivot"
        )
        legend.setObjectName("legend")
        legend.setWordWrap(True)
        right.addWidget(legend)
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

        focusables = [
            self.le_input,
            self.spn_fps,
            self.sld_fps,
            self.sld_scrub,
            self.btn_random,
            self.btn_start,
            self.btn_pause,
            self.btn_reset,
            self.btn_export,
            self.btn_step_back,
            self.btn_step_fwd,
            self.chk_labels,
            self.lst_steps,
            self.txt_log,
        ]
        is_macos = sys.platform == "darwin"
        for w in focusables:
            w.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            if is_macos:
                w.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)

        root.addLayout(row)
        root.addLayout(speed_row)
        root.addLayout(scrub_row)
        root.addWidget(self.lbl_narration)
        root.addWidget(splitter)

        # (optional) nice keyboard order; defer until widgets belong to this window
        QWidget.setTabOrder(self.le_input, self.btn_random)
        QWidget.setTabOrder(self.btn_random, self.btn_start)
        QWidget.setTabOrder(self.btn_start, self.btn_pause)
        QWidget.setTabOrder(self.btn_pause, self.btn_reset)
        QWidget.setTabOrder(self.btn_reset, self.btn_export)
        QWidget.setTabOrder(self.btn_export, self.sld_fps)
        QWidget.setTabOrder(self.sld_fps, self.spn_fps)
        QWidget.setTabOrder(self.spn_fps, self.sld_scrub)
        QWidget.setTabOrder(self.sld_scrub, self.btn_step_back)
        QWidget.setTabOrder(self.btn_step_back, self.btn_step_fwd)

        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)
        self.setStyleSheet(
            f"""
/* Global */
QWidget {{ color:#e6e6e6; background:#0f1115; }}

/* Accent helpers */
 @accent: #6aa0ff; /* (Qt ignores variables, left as a reminder) */

/* Caption pills – same accent as buttons */
QLabel#caption {{
  color:#e6e6e6;
  background:rgba(106,160,255,0.06);
  border:1px solid {self.cfg.bar_color};
  border-radius:8px;
  padding:4px 10px;
  font-weight:600;
}}

QLabel#legend {{
  color:#98a6c7;
  padding:6px 8px;
  background:rgba(35,45,64,0.45);
  border:1px solid rgba(152,166,199,0.25);
  border-radius:6px;
  font-size:11px;
}}

/* Inputs (LineEdit + SpinBox) – same hollow glass */
QLineEdit, QAbstractSpinBox {{
  color:#e6e6e6;
  background:rgba(106,160,255,0.06);
  border:1px solid {self.cfg.bar_color};
  border-radius:6px;
  padding:6px 8px;
}}
QLineEdit::placeholder {{ color:#b6bfca; }}
QLineEdit:focus, QAbstractSpinBox:focus {{ border-color:#9bc0ff; }}

/* Buttons – hollow glass */
QPushButton {{
  color:#e6e6e6;
  background:transparent;
  border:1px solid {self.cfg.bar_color};
  border-radius:6px;
  padding:6px 10px;
}}
QPushButton:hover   {{ background:rgba(106,160,255,0.20); }}
QPushButton:pressed {{ background:rgba(106,160,255,0.40); }}
QPushButton:disabled{{
  color:#7b8496; border-color:#3e4a60; background:transparent;
}}

/* Lists / Log – same accent frame */
QListWidget, QTextEdit {{
  color:#e6e6e6;
  background:rgba(106,160,255,0.04);
  border:1px solid {self.cfg.bar_color};
  border-radius:6px;
}}
QListWidget::item:selected {{ background:#243042; }}

/* Sliders – groove outlined in accent so FPS/Step “match” */
QSlider::groove:horizontal {{
  height:8px;
  background:rgba(106,160,255,0.06);
  border:1px solid {self.cfg.bar_color};
  border-radius:4px;
}}
QSlider::handle:horizontal {{
  width:18px;
  background:#e6e6e6;
  border:1px solid {self.cfg.bar_color};
  border-radius:9px;
  margin:-6px 0;
}}

/* Cobalt accent */
QLineEdit:focus,
QAbstractSpinBox:focus,
QPushButton:focus,
QListWidget:focus,
QTextEdit:focus {{
  border: 1px solid #2f6bff;              /* bright cobalt */
  background: rgba(47,107,255,0.14);       /* subtle glow */
}}

/* Sliders: groove + handle focus */
QSlider::groove:horizontal:focus {{
  border: 1px solid #2f6bff;
  background: rgba(47,107,255,0.12);
}}
QSlider::handle:horizontal:focus {{
  border: 2px solid #2f6bff;               /* a bit bolder on the knob */
  margin: -7px 0;                          /* compensates so the handle doesn't shift */
}}

/* Make sure no native subpage color fights the look */
QSlider::sub-page:horizontal,
QSlider::add-page:horizontal {{ background: transparent; border: none; }}

QSpinBox::up-button, QSpinBox::down-button {{ width: 0; height: 0; border: none; }}
"""
        )

    def _rebind(self) -> None:
        self.btn_random.clicked.connect(self._on_randomize)
        self.btn_start.clicked.connect(self._on_start)
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_reset.clicked.connect(self._on_reset)
        self.sld_fps.valueChanged.connect(self._on_fps_changed)
        self.spn_fps.valueChanged.connect(self._on_fps_changed)
        self.btn_export.clicked.connect(self._on_export)
        self.le_input.editingFinished.connect(
            lambda: self._settings.setValue("viz/last_input", self.le_input.text())
        )
        self.sld_scrub.valueChanged.connect(self._on_scrub_move)
        self.btn_step_fwd.clicked.connect(self._on_step_forward)
        self.btn_step_back.clicked.connect(self._on_step_back)
        self.chk_labels.toggled.connect(self.canvas.set_show_labels)

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

    def _restore_preferences(self) -> None:
        fps = int(self._settings.value("viz/fps", self.cfg.fps_default))
        for widget in (self.sld_fps, self.spn_fps):
            widget.blockSignals(True)
        self.sld_fps.setValue(fps)
        self.spn_fps.setValue(fps)
        for widget in (self.sld_fps, self.spn_fps):
            widget.blockSignals(False)

        last_input = self._settings.value("viz/last_input", "")
        if isinstance(last_input, bytes):
            last_input = last_input.decode()
        self.le_input.setText(str(last_input))

    def _persist_last_array(self, arr: list[int]) -> None:
        rendered = ",".join(str(v) for v in arr)
        self._settings.setValue("viz/last_input", rendered)

    def _set_narration(self, text: str | None = None) -> None:
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

        can_start_new = not running

        self.le_input.setEnabled(can_start_new)
        self.btn_random.setEnabled(can_start_new)
        self.btn_start.setEnabled(can_start_new)

        self.btn_pause.setEnabled(running or paused)

        self.btn_reset.setEnabled(can_start_new and bool(self._initial_array))

        has_steps = bool(self._steps)
        self.btn_export.setEnabled(can_start_new and has_steps)

        allow_scrub = can_start_new and has_steps
        manual_forward_available = can_start_new and (has_steps or self._step_source is not None)
        self.sld_scrub.setEnabled(allow_scrub)
        self.btn_step_fwd.setEnabled(manual_forward_available)
        self.btn_step_back.setEnabled(can_start_new and self._step_idx > 0)

    # ---------- state and metrics

    def _get_canvas_state(self) -> dict[str, Any]:
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
                "elapsed_s": elapsed,
            },
        }

    def _set_array(self, arr: list[int], *, persist: bool = True) -> None:
        if not arr:
            raise ValueError("Array cannot be empty")
        self._array = list(arr)
        self._initial_array = list(arr)
        if persist:
            self._persist_last_array(arr)
        self._highlights = {
            "compare": (),
            "swap": (),
            "pivot": (),
            "merge": (),
            "key": (),
            "shift": (),
        }
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
            self._set_array(arr, persist=False)
            self._settings.setValue("viz/last_input", "")
            self.txt_log.append(f"Randomized array n={n}")
            LOGGER.info("Randomized n=%d", n)
        except Exception as e:
            self._error(str(e))

    def _prepare_run(self) -> bool:
        # If we already have a generator in progress, nothing to do.
        if self._step_source is not None:
            return True

        parsed = self._parse_input()

        if parsed:
            self._set_array(parsed)
            self.le_input.setText(",".join(str(x) for x in parsed))
        else:
            if self._initial_array:
                self._set_array(self._initial_array, persist=False)
            else:
                self._on_randomize()
                if not self._array:
                    return False

        self._step_source = self._generate_steps(list(self._array))
        self._t0 = time.time()
        self._update_ui_state("paused")
        return True

    def _parse_input(self) -> list[int]:
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
            if not self._prepare_run():
                return
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
            if self._step_source is None and (
                self._confirm_progress >= 0 or not self._steps or self._step_idx >= len(self._steps)
            ):
                self._warn("Nothing to resume.")
                return
            fps = max(self.cfg.fps_min, min(self.cfg.fps_max, self.sld_fps.value()))
            self._timer.start(int(1000 / fps))
            self.txt_log.append("Resumed")
            self._update_ui_state("running")

    def _on_reset(self) -> None:
        self._timer.stop()
        self._step_source = None
        self._confirm_progress = -1
        if self._initial_array:
            self._set_array(self._initial_array, persist=False)
        self.txt_log.append("Reset")
        self._update_ui_state("idle")

    def _on_fps_changed(self, v: int) -> None:
        # keep slider/spin synchronized without causing recursive events
        for widget in (self.sld_fps, self.spn_fps):
            if widget.value() != v:
                widget.blockSignals(True)
                widget.setValue(v)
                widget.blockSignals(False)

        clamped = max(self.cfg.fps_min, min(self.cfg.fps_max, int(v)))
        self._settings.setValue("viz/fps", clamped)
        if self._timer.isActive():
            self._timer.start(int(1000 / max(1, clamped)))

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
        advanced = self._advance_step()
        if not advanced and self._step_source is None and self._confirm_progress < 0:
            self._timer.stop()

    def _advance_step(self) -> bool:
        if self._step_source is None:
            return False
        try:
            step = next(self._step_source)
        except StopIteration:
            self._step_source = None
            self._start_finish_animation()
            return False
        except Exception as exc:  # capture unexpected generator errors
            self._step_source = None
            self._error(str(exc))
            return False

        self._process_step(step)
        return True

    def _process_step(self, step: Step) -> None:
        narration = self._narrate_step(step)
        self._apply_step(step)
        self._steps.append(step)
        if len(self._steps) % self.cfg.checkpoint_stride == 0:
            self._append_checkpoint(len(self._steps))
        self._append_step_list(step)
        self._step_idx = len(self._steps)
        self._update_scrub_ui()
        self.canvas.update()
        self._set_narration(narration)

    def _start_finish_animation(self) -> None:
        self.txt_log.append(f"Finished. Comparisons={self._comparisons}, Swaps={self._swaps}")
        LOGGER.info(
            "Finished algo=%s comps=%d swaps=%d", self.title, self._comparisons, self._swaps
        )
        self._confirm_progress = 0
        self._confirm_indices = tuple()
        self._set_narration("Sort complete. Finalizing display…")

        # Rebind timer to finish sweep at high FPS
        with suppress(TypeError):
            self._timer.timeout.disconnect(self._tick)
        with suppress(TypeError):
            self._timer.timeout.disconnect(self._finish_tick)
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
            with suppress(TypeError):
                self._timer.timeout.disconnect(self._finish_tick)
            with suppress(TypeError):
                self._timer.timeout.disconnect(self._tick)
            self._timer.timeout.connect(self._tick)
            self._set_narration("Array sorted!")
            self._confirm_progress = -1

    # ---------- step application and highlights

    def _narrate_step(self, step: Step) -> str:
        arr = self._array
        op = step.op
        idx = step.indices
        payload = step.payload

        def safe_get(i: int) -> int | None:
            return arr[i] if 0 <= i < len(arr) else None

        try:
            if op == "compare":
                i, j = idx
                return f"Comparing {safe_get(i)} (index {i}) with " f"{safe_get(j)} (index {j})."
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
            if op == "shift":
                k = idx[0]
                return f"Shifting {payload} into index {k}."
            if op == "pivot":
                p = idx[0]
                return f"Selecting {safe_get(p)} at index {p} as the pivot."
            if op == "merge_mark":
                lo, hi = idx
                return f"Marking merge range {lo} – {hi}."
            if op == "key":
                if not idx:
                    return "Key placement complete."
                target = idx[0]
                return f"Tracking key {payload} (target index {target})."
            if op == "confirm" and idx:
                i = idx[0]
                return f"Confirming index {i} as sorted."
        except (IndexError, ValueError, TypeError):
            return ""

        return ""

    def _append_step_list(self, step: Step) -> None:
        current_idx = len(self._steps)
        important_ops = {"swap", "set", "shift", "pivot", "merge_mark", "key"}
        if (
            current_idx > 1
            and (current_idx % self.STEP_LIST_SAMPLE_RATE != 0)
            and (step.op not in important_ops)
        ):
            return

        display_idx = current_idx
        text = f"{display_idx:04d} | {step.op}: {step.indices}" + (
            f" -> {step.payload}" if step.payload is not None else ""
        )
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
            self._highlights["shift"] = ()
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
            payload = step.payload
            if not isinstance(payload, int):
                raise ValueError("set step requires int payload")
            self._array[k] = payload
            self._highlights["merge"] = (k,)
            self._highlights["shift"] = ()
        elif op == "shift":
            k = idx[0]
            payload = step.payload
            if not isinstance(payload, int):
                raise ValueError("shift step requires int payload")
            self._array[k] = payload
            self._highlights["shift"] = (k,)
            self._highlights["merge"] = ()
        elif op == "key":
            self._highlights["key"] = idx
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

    def _on_step_forward(self) -> None:
        if self._timer.isActive():
            self._timer.stop()
        try:
            if self._step_source is None and not self._steps and not self._prepare_run():
                return
            if self._step_idx < len(self._steps):
                self._seek(self._step_idx + 1)
                self._update_ui_state("paused")
                return
            if self._advance_step():
                self._update_ui_state("paused")
            else:
                self._update_ui_state("finished" if self._confirm_progress >= 0 else "paused")
        except Exception as exc:
            self._error(str(exc))

    def _on_step_back(self) -> None:
        if self._timer.isActive():
            self._timer.stop()
        if self._step_idx > 0:
            self._seek(self._step_idx - 1)
            self._update_ui_state("paused")

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
        self._highlights = {
            "compare": (),
            "swap": (),
            "pivot": (),
            "merge": (),
            "key": (),
            "shift": (),
        }

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
        selected_row: int | None = None

        for i in range(start, end):
            step = self._steps[i]
            text = f"{step.op}: {step.indices}"
            if step.payload is not None:
                text += f" -> {step.payload}"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.ItemDataRole.UserRole, i + 1)
            self.lst_steps.addItem(list_item)

            if i == target_idx - 1:
                selected_row = self.lst_steps.count() - 1

        if selected_row is not None and 0 <= selected_row < self.lst_steps.count():
            selected_item = self.lst_steps.item(selected_row)
            if selected_item is not None:
                self.lst_steps.setCurrentItem(selected_item)
                self.lst_steps.scrollToItem(selected_item, QListWidget.ScrollHint.PositionAtCenter)
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

    def hideEvent(self, event: QHideEvent | None) -> None:
        self.pause_if_running()
        super().hideEvent(event)

    def _warn(self, msg: str) -> None:
        self.txt_log.append(f"[WARN] {msg}")

    def _error(self, msg: str) -> None:
        self.txt_log.append(f"[ERROR] {msg}")
        LOGGER.exception(msg)
        QMessageBox.critical(self, self.title, msg)

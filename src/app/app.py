from __future__ import annotations

import sys
from importlib import import_module

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from app.algos.registry import INFO, REGISTRY
from app.core.base import AlgorithmVisualizerBase

_ORG_NAME = "org.pysort"
_APP_NAME = "sorting-visualizer"
_APP_DOMAIN = "sortingviz.dev"

for module in (
    "app.algos.bubble",
    "app.algos.insertion",
    "app.algos.merge",
    "app.algos.quick",
):
    import_module(module)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings(_ORG_NAME, _APP_NAME)
        self.setWindowTitle("Sorting Algorithm Visualizers")
        self.resize(1200, 850)

        tabs = QTabWidget()
        for name in sorted(INFO.keys()):
            info = INFO[name]
            algo_func = REGISTRY[name]
            visualizer = AlgorithmVisualizerBase(algo_info=info, algo_func=algo_func)
            tabs.addTab(visualizer, name)
        self.setCentralWidget(tabs)

        geometry = self._settings.value("main/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        theme = self._settings.value("ui/theme", "dark")
        self._settings.setValue("ui/theme", theme)

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self._settings.setValue("main/geometry", self.saveGeometry())
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setOrganizationDomain(_APP_DOMAIN)
    app.setOrganizationName(_ORG_NAME)
    app.setApplicationName(_APP_NAME)
    app.setApplicationVersion("0.1.0")
    app.setStyleSheet(
        """
QMainWindow, QTabWidget::pane, QTabWidget {
  background: #0f1115;
}
QTabBar::tab {
  background: #1a1f27;
  color: #cfd6e6;
  padding: 6px 10px;
  border-radius: 6px;
}
QTabBar::tab:selected { background: #2a2f3a; color: #ffffff; }
QTabBar::tab:hover    { background: #202634; }
"""
    )
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

from __future__ import annotations
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

# Import algorithms to register them
from app.algos import bubble, quick, merge
from app.algos.registry import REGISTRY, INFO
from app.core.base import AlgorithmVisualizerBase


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sorting Algorithm Visualizers")
        self.resize(1200, 850)

        tabs = QTabWidget()
        for name, algo_func in REGISTRY.items():
            info = INFO[name]
            visualizer = AlgorithmVisualizerBase(algo_info=info, algo_func=algo_func)
            tabs.addTab(visualizer, name)
        self.setCentralWidget(tabs)


def main() -> None:
    app = QApplication(sys.argv)
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

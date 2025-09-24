from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from .bubble import BubbleSortVisualizer
from .merge import MergeSortVisualizer
from .quick import QuickSortVisualizer


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sorting Algorithm Visualizers")
        self.resize(1200, 850)

        tabs = QTabWidget()
        tabs.addTab(BubbleSortVisualizer(), "Bubble Sort")
        tabs.addTab(QuickSortVisualizer(), "Quick Sort")
        tabs.addTab(MergeSortVisualizer(), "Merge Sort")
        self.setCentralWidget(tabs)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

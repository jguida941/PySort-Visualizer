from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from bubblesort_visualizer import BubbleSortVisualizer
from mergesort_visualizer import MergeSortVisualizer
from quicksort_visualizer import QuickSortVisualizer


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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

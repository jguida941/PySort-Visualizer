import os

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setOrganizationDomain("sortingviz.dev")
    app.setOrganizationName("SortingViz")
    app.setApplicationName("Sorting Visualizer")
    yield app

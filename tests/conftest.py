import os
from collections.abc import Generator
from typing import cast

import pytest
from PyQt6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    instance = QApplication.instance()
    app = cast(QApplication, instance) if instance is not None else QApplication([])
    app.setOrganizationDomain("sortingviz.dev")
    app.setOrganizationName("SortingViz")
    app.setApplicationName("Sorting Visualizer")
    yield app

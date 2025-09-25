from __future__ import annotations

from collections.abc import Callable, Iterable

import pytest
from hypothesis import given
from hypothesis import strategies as st
from PyQt6.QtWidgets import QApplication

from app.algos.registry import REGISTRY, load_all_algorithms
from app.core.replay import apply_step_sequence
from app.core.step import Step

load_all_algorithms()


def _steps_and_results(
    algo: Callable[[list[int]], Iterable[Step]], arr: list[int]
) -> tuple[list[Step], list[int], list[int]]:
    working = list(arr)
    steps = list(algo(working))
    replayed = apply_step_sequence(arr, steps)
    return steps, working, replayed


@given(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=64))
def test_algorithms_sort_like_python_sorted(qapp: QApplication, xs: list[int]) -> None:
    for name, algo in REGISTRY.items():
        steps, working, replayed = _steps_and_results(algo, xs)
        assert working == sorted(xs), f"generator result mismatch for {name}"
        assert replayed == sorted(xs), f"replay result mismatch for {name}"
        assert replayed == working, f"replay diverged from generator for {name}"


@pytest.mark.parametrize(
    "arr",
    [
        [],
        [1],
        [2, 1],
        [1, 1, 1],
        [3, 2, 2, 1],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [2, 3, 1, 5, 4],
        [10, -1, 0, 10, -1],
    ],
)
def test_known_cases(qapp: QApplication, arr: list[int]) -> None:
    for name, algo in REGISTRY.items():
        _steps, working, replayed = _steps_and_results(algo, arr)
        assert working == sorted(arr), f"generator result mismatch for {name}"
        assert replayed == sorted(arr), f"replay result mismatch for {name}"
        assert replayed == working, f"replay diverged from generator for {name}"

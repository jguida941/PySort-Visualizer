from __future__ import annotations

from typing import Iterator, List

from base import AlgorithmVisualizerBase, Step


class BubbleSortVisualizer(AlgorithmVisualizerBase):
    title = "Bubble Sort"

    def _generate_steps(self, arr: List[int]) -> Iterator[Step]:
        n = len(arr)
        if n <= 1:
            return

        for i in range(n):
            swapped = False
            limit = n - i - 1
            for j in range(limit):
                yield Step("compare", (j, j + 1))
                if self._array[j] > self._array[j + 1]:
                    left, right = self._array[j], self._array[j + 1]
                    yield Step("swap", (j, j + 1), payload=(left, right))
                    swapped = True
            if not swapped:
                break

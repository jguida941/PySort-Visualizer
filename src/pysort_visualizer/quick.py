from __future__ import annotations

from typing import Iterator, List, Tuple

from .base import AlgorithmVisualizerBase, Step


class QuickSortVisualizer(AlgorithmVisualizerBase):
    title = "Quick Sort (Iterative)"

    def _generate_steps(self, arr: List[int]) -> Iterator[Step]:
        n = len(arr)
        if n <= 1:
            return

        stack: List[Tuple[int, int]] = [(0, n - 1)]
        while stack:
            low, high = stack.pop()
            if low >= high:
                continue

            mid = (low + high) // 2
            yield Step("compare", (low, mid))
            yield Step("compare", (mid, high))
            yield Step("compare", (low, high))
            trio = sorted(
                [
                    (self._array[low], low),
                    (self._array[mid], mid),
                    (self._array[high], high),
                ]
            )
            _, pidx = trio[1]
            if pidx != high:
                left, right = self._array[pidx], self._array[high]
                yield Step("swap", (pidx, high), payload=(left, right))

            pivot_index = high
            pivot_val = self._array[pivot_index]
            yield Step("pivot", (pivot_index,))
            i = low
            for j in range(low, high):
                yield Step("compare", (j, pivot_index))
                if self._array[j] <= pivot_val:
                    if i != j:
                        left, right = self._array[i], self._array[j]
                        yield Step("swap", (i, j), payload=(left, right))
                    i += 1
            if i != high:
                left, right = self._array[i], self._array[high]
                yield Step("swap", (i, high), payload=(left, right))
            p = i

            if p + 1 < high:
                stack.append((p + 1, high))
            if low < p - 1:
                stack.append((low, p - 1))

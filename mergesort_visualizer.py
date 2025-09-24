from __future__ import annotations

from typing import Iterator, List

from base import AlgorithmVisualizerBase, Step


class MergeSortVisualizer(AlgorithmVisualizerBase):
    title = "Merge Sort (Iterative)"

    def _generate_steps(self, arr: List[int]) -> Iterator[Step]:
        n = len(arr)
        if n <= 1:
            return

        width = 1
        while width < n:
            stride = 2 * width
            for lo in range(0, n, stride):
                mid = min(lo + width - 1, n - 1)
                hi = min(lo + stride - 1, n - 1)
                if mid >= hi:
                    continue

                aux = self._array[lo : hi + 1]
                yield Step("merge_mark", (lo, hi))

                left_len = mid - lo + 1
                i = 0
                j = left_len
                for k in range(lo, hi + 1):
                    if i >= left_len:
                        yield Step("set", (k,), aux[j])
                        j += 1
                    elif j >= len(aux):
                        yield Step("set", (k,), aux[i])
                        i += 1
                    else:
                        yield Step("merge_compare", (lo + i, lo + j), payload=k)
                        if aux[i] <= aux[j]:
                            yield Step("set", (k,), aux[i])
                            i += 1
                        else:
                            yield Step("set", (k,), aux[j])
                            j += 1
            width *= 2

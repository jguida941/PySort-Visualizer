from app.algos.registry import register, AlgoInfo
from app.core.step import Step
from typing import Iterator, List


@register(
    AlgoInfo(
        name="Merge Sort",
        stable=True,
        in_place=False,
        comparison=True,
        complexity={"best": "O(n log n)", "avg": "O(n log n)", "worst": "O(n log n)"},
    )
)
def merge_sort(a: list[int]):
    n = len(a)
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

            aux = a[lo : hi + 1]
            yield Step("merge_mark", (lo, hi))

            left_len = mid - lo + 1
            i = 0
            j = left_len
            for k in range(lo, hi + 1):
                if i >= left_len:
                    yield Step("set", (k,), aux[j])
                    a[k] = aux[j]
                    j += 1
                elif j >= len(aux):
                    yield Step("set", (k,), aux[i])
                    a[k] = aux[i]
                    i += 1
                else:
                    yield Step("merge_compare", (lo + i, lo + j), payload=k)
                    if aux[i] <= aux[j]:
                        yield Step("set", (k,), aux[i])
                        a[k] = aux[i]
                        i += 1
                    else:
                        yield Step("set", (k,), aux[j])
                        a[k] = aux[j]
                        j += 1
        width *= 2

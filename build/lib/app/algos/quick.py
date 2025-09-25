from app.algos.registry import register, AlgoInfo
from app.core.step import Step
from typing import Iterator, List, Tuple


@register(
    AlgoInfo(
        name="Quick Sort",
        stable=False,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n log n)", "avg": "O(n log n)", "worst": "O(n^2)"},
    )
)
def quick_sort(a: list[int]):
    n = len(a)
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
                (a[low], low),
                (a[mid], mid),
                (a[high], high),
            ]
        )
        _, pidx = trio[1]
        if pidx != high:
            left, right = a[pidx], a[high]
            yield Step("swap", (pidx, high), payload=(left, right))
            a[pidx], a[high] = a[high], a[pidx]

        pivot_index = high
        pivot_val = a[pivot_index]
        yield Step("pivot", (pivot_index,))
        i = low
        for j in range(low, high):
            yield Step("compare", (j, pivot_index))
            if a[j] <= pivot_val:
                if i != j:
                    left, right = a[i], a[j]
                    yield Step("swap", (i, j), payload=(left, right))
                    a[i], a[j] = a[j], a[i]
                i += 1
        if i != high:
            left, right = a[i], a[high]
            yield Step("swap", (i, high), payload=(left, right))
            a[i], a[hign] = a[high], a[i]
        p = i

        if p + 1 < high:
            stack.append((p + 1, high))
        if low < p - 1:
            stack.append((low, p - 1))

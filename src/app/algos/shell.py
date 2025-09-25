from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Shell Sort",
        stable=False,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n log n)", "avg": "O(n^2)", "worst": "O(n^2)"},
    )
)
def shell_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        return

    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            key = a[i]
            yield Step("key", (i,), key)
            j = i
            while j >= gap:
                yield Step("compare", (j - gap, j))
                if a[j - gap] <= key:
                    break
                a[j] = a[j - gap]
                yield Step("shift", (j,), a[j])
                j -= gap
            if j != i:
                a[j] = key
                yield Step("set", (j,), key)
            yield Step("key", (j,), key)
        gap //= 2
    yield Step("key", ())

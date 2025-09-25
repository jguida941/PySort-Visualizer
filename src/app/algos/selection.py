from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Selection Sort",
        stable=False,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n^2)", "avg": "O(n^2)", "worst": "O(n^2)"},
    )
)
def selection_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        return

    for i in range(n - 1):
        min_idx = i
        yield Step("key", (i,), a[i])

        for j in range(i + 1, n):
            yield Step("compare", (min_idx, j))
            if a[j] < a[min_idx]:
                min_idx = j
                yield Step("key", (min_idx,), a[min_idx])

        if min_idx != i:
            payload = (a[i], a[min_idx])
            yield Step("swap", (i, min_idx), payload=payload)
            a[i], a[min_idx] = a[min_idx], a[i]
            yield Step("key", (i,), a[i])

    yield Step("key", ())

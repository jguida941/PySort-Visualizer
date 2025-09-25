from collections.abc import Iterator

from app.algos.registry import AlgoInfo, register
from app.core.step import Step


@register(
    AlgoInfo(
        name="Comb Sort",
        stable=False,
        in_place=True,
        comparison=True,
        complexity={"best": "O(n log n)", "avg": "O(n^2)", "worst": "O(n^2)"},
    )
)
def comb_sort(a: list[int]) -> Iterator[Step]:
    n = len(a)
    if n <= 1:
        return

    gap = n
    shrink = 1.3
    swapped = True

    while gap > 1 or swapped:
        gap = max(1, int(gap / shrink))
        swapped = False

        for i in range(0, n - gap):
            j = i + gap
            yield Step("compare", (i, j))
            if a[i] > a[j]:
                payload = (a[i], a[j])
                yield Step("swap", (i, j), payload=payload)
                a[i], a[j] = a[j], a[i]
                swapped = True

    for idx in range(n):
        yield Step("confirm", (idx,))
